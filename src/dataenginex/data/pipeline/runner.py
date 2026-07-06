"""PipelineRunner — config-driven data pipeline execution.

Flow: Config -> Extract (connector or lakehouse) -> Register views ->
      Transform chain -> Quality gate -> Load (correct lakehouse layer)

Layer resolution (explicit beats implicit):
  - If cfg.target["layer"] is set, use that.
  - Otherwise infer from pipeline name prefix:
      bronze_* → bronze   gold_* → gold   everything else → silver
"""

from __future__ import annotations

import contextlib
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import structlog

from dataenginex.config.schema import (
    DexConfig,
    PipelineConfig,
    TransformStepConfig,
)
from dataenginex.core.exceptions import PipelineError, PipelineStepError
from dataenginex.data.connectors import connector_registry

# Import to trigger registration
from dataenginex.data.connectors.csv import CsvConnector as _CsvConnector  # noqa: F401
from dataenginex.data.connectors.dbt import DbtConnector as _DbtConnector  # noqa: F401
from dataenginex.data.connectors.duckdb import DuckDBConnector as _DuckDBConnector  # noqa: F401
from dataenginex.data.connectors.parquet import ParquetConnector as _ParquetConnector  # noqa: F401
from dataenginex.data.connectors.spark import SparkConnector as _SparkConnector  # noqa: F401
from dataenginex.data.pipeline.dag import resolve_execution_order
from dataenginex.data.quality.gates import check_quality
from dataenginex.data.transforms import transform_registry

# Import to trigger registration
from dataenginex.data.transforms.sql import (  # noqa: F401
    CastTransform as _CastTransform,
)
from dataenginex.lakehouse.storage import DeltaStorage
from dataenginex.middleware.domain_metrics import quality_gate_evaluations_total
from dataenginex.warehouse.lineage import LineageBackend

logger = structlog.get_logger()

# Prefixes that imply a specific lakehouse layer when no explicit target is set.
_LAYER_PREFIXES: list[tuple[str, str]] = [
    ("bronze_", "bronze"),
    ("gold_", "gold"),
]


def _infer_layer(pipeline_name: str) -> str:
    """Return the lakehouse layer implied by a pipeline name prefix."""
    for prefix, layer in _LAYER_PREFIXES:
        if pipeline_name.startswith(prefix):
            return layer
    return "silver"


def _is_delta_table(path: Path) -> bool:
    """Return True if *path* is a directory laid out as a Delta table."""
    return (path / "_delta_log").exists()


@dataclass(frozen=True)
class PipelineResult:
    """Result of a single pipeline execution."""

    pipeline: str
    success: bool
    rows_input: int = 0
    rows_output: int = 0
    steps_completed: int = 0
    dry_run: bool = False
    error: str | None = None


def _build_transform_kwargs(step: TransformStepConfig) -> dict[str, Any]:
    """Extract non-None fields from a transform step config."""
    kwargs: dict[str, Any] = {}
    for field in (
        "condition",
        "expression",
        "name",
        "columns",
        "key",
        "sql",
        "mapping",
        "defaults",
        "group_by",
        "agg_exprs",
        "partition_by",
        "order_by",
    ):
        value = getattr(step, field, None)
        if value is not None:
            kwargs[field] = value
    kwargs.update(step.options)
    return kwargs


def _summarize_step(step: TransformStepConfig) -> str:
    """One-line human summary of a transform step for the flow canvas."""
    if step.condition:
        return step.condition
    if step.sql:
        return step.sql.strip().splitlines()[0]
    if step.key:
        return f"key: {step.key if isinstance(step.key, str) else ', '.join(step.key)}"
    if step.name:
        return f"{step.name} = {step.expression or ''}"
    return step.type


class PipelineRunner:
    """Execute data pipelines defined in dex.yaml.

    Args:
        config: Loaded DexConfig.
        data_dir: Root directory for lakehouse layer storage.
        project_dir: Project root — used to resolve relative source paths.
        lineage: Optional lineage backend.
        feature_store: Optional feature store — gold tables are saved as feature groups.
        vector_store: Optional vector store — gold/silver rows are embedded on completion.
        embed_fn: Embedding callable for vector store ingest.
    """

    def __init__(
        self,
        config: DexConfig,
        data_dir: Path | None = None,
        project_dir: Path | None = None,
        lineage: LineageBackend | None = None,
        feature_store: Any = None,
        vector_store: Any = None,
        embed_fn: Any = None,
    ) -> None:
        self._config = config
        self._data_dir = data_dir or Path(".dex/lakehouse")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._project_dir = project_dir
        self._lineage = lineage
        self._feature_store = feature_store
        self._vector_store = vector_store
        self._embed_fn = embed_fn
        # Temp directory for DuckDB spill-to-disk — prevents OOM on large datasets
        self._tmp_dir = (self._data_dir.parent / "tmp" / "duckdb").resolve()
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def run(self, pipeline_name: str, *, dry_run: bool = False) -> PipelineResult:
        """Run a single pipeline by name."""
        pipelines = self._config.data.pipelines
        if pipeline_name not in pipelines:
            available = list(pipelines.keys())
            msg = f"Pipeline '{pipeline_name}' not found. Available: {available}"
            raise KeyError(msg)

        pipeline_config = pipelines[pipeline_name]
        log = logger.bind(pipeline=pipeline_name)
        log.info("pipeline starting", dry_run=dry_run)

        if dry_run:
            log.info("pipeline dry run — validating only")
            return PipelineResult(pipeline=pipeline_name, success=True, dry_run=True)

        conn = duckdb.connect(":memory:", config={"temp_directory": str(self._tmp_dir)})

        try:
            return self._execute(conn, pipeline_name, pipeline_config, log)
        except (PipelineError, PipelineStepError, KeyError):
            raise
        except Exception as e:
            log.error("pipeline failed", error=str(e))
            return PipelineResult(pipeline=pipeline_name, success=False, error=str(e))
        finally:
            conn.close()

    def run_all(self) -> dict[str, PipelineResult]:
        """Run all pipelines in dependency order."""
        if not self._config.data.pipelines:
            return {}

        dep_graph: dict[str, list[str]] = {
            name: list(p.depends_on) for name, p in self._config.data.pipelines.items()
        }
        order = resolve_execution_order(dep_graph)
        results: dict[str, PipelineResult] = {}

        for name in order:
            result = self.run(name)
            results[name] = result
            if not result.success:
                logger.error("pipeline failed — stopping", pipeline=name)
                break

        return results

    def preview(self, pipeline_name: str, sample: int = 200_000) -> dict[str, Any]:
        """Per-stage row counts for the flow canvas.

        Runs extract + each transform on a *sample* of the source and scales the
        counts back to full size, so the UI shows how data shrinks/changes as it
        travels through the pipeline — without a full (heavy) production run.
        """
        pipelines = self._config.data.pipelines
        if pipeline_name not in pipelines:
            msg = f"Pipeline '{pipeline_name}' not found"
            raise KeyError(msg)
        cfg = pipelines[pipeline_name]
        log = logger.bind(pipeline=pipeline_name, mode="preview")
        conn = duckdb.connect(":memory:", config={"temp_directory": str(self._tmp_dir)})
        try:
            self._register_lakehouse_views(conn, log)
            rows_input = self._extract(conn, pipeline_name, cfg, log)
            n = min(rows_input, sample) if rows_input else 0
            sampled = rows_input > sample
            if sampled:
                conn.execute(
                    f"CREATE OR REPLACE TABLE bronze AS SELECT * FROM bronze LIMIT {sample}"
                )
            scale = (rows_input / n) if n else 1.0
            stages: list[dict[str, Any]] = [
                {
                    "kind": "source",
                    "type": "source",
                    "label": cfg.source or "source",
                    "rows": rows_input,
                    "estimated": False,
                }
            ]
            current = "bronze"
            for step in cfg.transforms:
                transform = transform_registry.get(step.type)(**_build_transform_kwargs(step))
                current = transform.apply(conn, current)
                row = conn.execute(f"SELECT count(*) FROM {current}").fetchone()
                cnt = int((row[0] if row else 0) * scale)
                stages.append(
                    {
                        "kind": "transform",
                        "type": step.type,
                        "label": _summarize_step(step),
                        "rows": cnt,
                        "estimated": sampled,
                    }
                )
            dest_rows = stages[-1]["rows"] if cfg.transforms else rows_input
            stages.append(
                {
                    "kind": "destination",
                    "type": "destination",
                    "label": cfg.destination or pipeline_name,
                    "rows": dest_rows,
                    "estimated": sampled and bool(cfg.transforms),
                }
            )
            return {
                "pipeline": pipeline_name,
                "sampled": sampled,
                "sample_size": n,
                "source_rows": rows_input,
                "stages": stages,
            }
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Internal pipeline steps
    # -------------------------------------------------------------------------

    def _execute(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        log: Any,
    ) -> PipelineResult:
        """Core pipeline execution: extract -> register views -> transform -> quality -> load."""
        # Register all existing lakehouse parquet files as DuckDB views so that
        # cross-pipeline SQL references (e.g. silver_movies JOIN bronze_ratings)
        # resolve correctly inside the same connection.
        self._register_lakehouse_views(conn, log)

        rows_input = self._extract(conn, name, cfg, log)

        # Empty source (e.g. SSE window with no events) — nothing to transform or load.
        if rows_input == 0:
            log.info("pipeline complete — empty source, nothing to write", pipeline=name)
            return PipelineResult(
                pipeline=name, success=True, rows_input=0, rows_output=0, steps_completed=0
            )

        current_table, steps = self._transform(conn, name, cfg, log)
        self._check_quality(conn, name, cfg, current_table, log)
        rows_output = self._load(conn, name, cfg, current_table, log)
        self._post_load_hooks(conn, name, cfg, current_table, log)

        return PipelineResult(
            pipeline=name,
            success=True,
            rows_input=rows_input,
            rows_output=rows_output,
            steps_completed=steps,
        )

    def _register_lakehouse_views(
        self,
        conn: duckdb.DuckDBPyConnection,
        log: Any,
    ) -> None:
        """Register every parquet file in the lakehouse as a DuckDB view.

        This makes previously-run pipeline outputs visible to SQL transforms
        without requiring the runner to manage a shared DuckDB file.  Views
        are overwritten on each pipeline run so stale data is never referenced.
        """
        for layer in ("bronze", "silver", "gold"):
            layer_dir = self._data_dir / layer
            if not layer_dir.exists():
                continue
            for pf in sorted(layer_dir.glob("*.parquet")):
                safe = str(pf).replace("'", "''")
                with contextlib.suppress(Exception):
                    conn.execute(
                        f"CREATE OR REPLACE VIEW {pf.stem} AS SELECT * FROM read_parquet('{safe}')"
                    )
            for dd in sorted(p for p in layer_dir.iterdir() if p.is_dir()):
                if not _is_delta_table(dd):
                    continue
                with contextlib.suppress(Exception):
                    records = DeltaStorage(base_path=str(layer_dir)).read(dd.name)
                    conn.register(dd.name, pa.Table.from_pylist(records or []))
        log.debug("lakehouse views registered")

    def _extract(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        log: Any,
    ) -> int:
        """Extract source data into a ``bronze`` table in *conn*.

        Source resolution order:
        1. Named entry in ``data.sources`` (standard path).
        2. Pipeline name in ``data.pipelines`` → load from its lakehouse output.
        3. Fail with a descriptive PipelineStepError.
        """
        sources = self._config.data.sources
        pipelines = self._config.data.pipelines

        if cfg.source in sources:
            return self._extract_from_source(conn, name, cfg, log)

        if cfg.source in pipelines:
            return self._extract_from_lakehouse(conn, name, cfg, log)

        msg = (
            f"Source '{cfg.source}' not found in data.sources or data.pipelines. "
            f"Available sources: {list(sources.keys())}"
        )
        raise PipelineStepError(step="extract", cause=msg, pipeline=name)

    def _extract_from_source(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        log: Any,
    ) -> int:
        """Standard connector-based extraction."""
        sources = self._config.data.sources
        source_config = sources[cfg.source]
        connector_cls = connector_registry.get(source_config.type)

        # connection holds credentials; options holds connector-specific settings.
        # options wins on conflicts so connectors can tune behaviour per-source.
        connector_kwargs: dict[str, Any] = {
            **dict(source_config.connection),
            **dict(source_config.options),
        }
        if source_config.path and "path" not in connector_kwargs:
            src_path = source_config.path
            if self._project_dir and not Path(src_path).is_absolute():
                src_path = str(self._project_dir / src_path)
            connector_kwargs["path"] = src_path
        if source_config.url and "url" not in connector_kwargs:
            connector_kwargs["url"] = source_config.url

        connector = connector_cls(**connector_kwargs)
        connector.connect()
        read_table = connector_kwargs.get("default_file", cfg.source)
        raw_data = connector.read(table=read_table)
        connector.disconnect()

        # Connectors may return a pa.Table (e.g. HttpConnector) to avoid the
        # cost of converting 10M+ rows through Python dicts.
        arrow_table = raw_data if isinstance(raw_data, pa.Table) else pa.Table.from_pylist(raw_data)

        # Empty result (e.g. SSE window with no matching events) — nothing to load.
        if len(arrow_table) == 0 or len(arrow_table.schema) == 0:
            log.info("extract complete (source) — empty result", source=cfg.source)
            conn.execute("CREATE OR REPLACE TABLE bronze (placeholder VARCHAR)")
            rows = 0
        else:
            conn.register("_raw_src", arrow_table)
            conn.execute("CREATE OR REPLACE TABLE bronze AS SELECT * FROM _raw_src")
            rows = len(arrow_table)
        log.info("extract complete (source)", source=cfg.source, rows=rows)

        if self._lineage is not None:
            self._lineage.record(
                operation="ingest",
                layer="bronze",
                source=cfg.source,
                destination=f"bronze/{name}",
                input_count=rows,
                output_count=rows,
                pipeline_name=name,
                step_name="extract",
            )
        return rows

    def _find_lakehouse_output(self, source_name: str) -> tuple[Path | None, Path | None]:
        """Locate a pipeline's lakehouse output, Parquet file or Delta directory.

        Searches bronze → silver → gold layers (most-likely layer first,
        inferred from the source name prefix). Returns
        ``(parquet_path, delta_dir)`` — exactly one is set, or both are
        ``None`` if the output doesn't exist yet.
        """
        candidate_layers = [_infer_layer(source_name), "bronze", "silver", "gold"]
        layers = list(dict.fromkeys(candidate_layers))  # de-dup, preserve order

        for layer in layers:
            layer_dir = self._data_dir / layer
            p_candidate = layer_dir / f"{source_name}.parquet"
            if p_candidate.exists():
                return p_candidate, None
            d_candidate = layer_dir / source_name
            if _is_delta_table(d_candidate):
                return None, d_candidate
        return None, None

    def _extract_from_lakehouse(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        log: Any,
    ) -> int:
        """Load a previously-run pipeline's output as the bronze table."""
        source_name = cfg.source
        parquet_path, delta_dir = self._find_lakehouse_output(source_name)

        if parquet_path is None and delta_dir is None:
            msg = (
                f"Lakehouse output for pipeline '{source_name}' not found. "
                "Run upstream pipelines first."
            )
            raise PipelineStepError(step="extract", cause=msg, pipeline=name)

        if parquet_path is not None:
            found_path = parquet_path
            safe = str(parquet_path).replace("'", "''")
            conn.execute(f"CREATE OR REPLACE TABLE bronze AS SELECT * FROM read_parquet('{safe}')")
        else:
            assert delta_dir is not None  # narrowed by the guard above
            found_path = delta_dir
            records = DeltaStorage(base_path=str(delta_dir.parent)).read(delta_dir.name)
            conn.register("_delta_src", pa.Table.from_pylist(records or []))
            conn.execute("CREATE OR REPLACE TABLE bronze AS SELECT * FROM _delta_src")

        row = conn.execute("SELECT COUNT(*) FROM bronze").fetchone()
        rows = int(row[0]) if row else 0
        log.info(
            "extract complete (lakehouse)",
            source=source_name,
            path=str(found_path),
            rows=rows,
        )

        if self._lineage is not None:
            self._lineage.record(
                operation="ingest",
                layer=_infer_layer(name),
                source=str(found_path),
                destination=f"{_infer_layer(name)}/{name}",
                input_count=rows,
                output_count=rows,
                pipeline_name=name,
                step_name="extract",
            )
        return rows

    def _transform(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        log: Any,
    ) -> tuple[str, int]:
        """Run transform chain. Returns (final_table, steps_completed)."""
        current_table = "bronze"
        steps_completed = 0

        for i, step_config in enumerate(cfg.transforms):
            kwargs = _build_transform_kwargs(step_config)
            transform_cls = transform_registry.get(step_config.type)
            transform = transform_cls(**kwargs)

            errors = transform.validate()
            if errors:
                msg = f"Transform validation failed: {errors}"
                raise PipelineStepError(step=f"transform-{i}", cause=msg, pipeline=name)

            prev_table = current_table
            prev_row = conn.execute(f"SELECT count(*) FROM {prev_table}").fetchone()
            prev_rows = int(prev_row[0]) if prev_row else 0

            current_table = transform.apply(conn, current_table)
            steps_completed += 1
            log.info("transform complete", step=i, type=step_config.type)

            if self._lineage is not None:
                out_row = conn.execute(f"SELECT count(*) FROM {current_table}").fetchone()
                out_rows = int(out_row[0]) if out_row else 0
                self._lineage.record(
                    operation="transform",
                    layer=_infer_layer(name),
                    source=prev_table,
                    destination=current_table,
                    input_count=prev_rows,
                    output_count=out_rows,
                    pipeline_name=name,
                    step_name=f"transform-{i}:{step_config.type}",
                    metadata={"transform_type": step_config.type, "step_index": i},
                )

            # Each transform materializes a new physical table (CREATE OR REPLACE
            # TABLE) rather than overwriting in place, so the previous step's table
            # must be dropped or it stays resident for the rest of the pipeline run —
            # on wide multi-million-row sources this accumulates one full dataset
            # copy per transform step and was OOM-killing pods on cold-start ETL.
            conn.execute(f"DROP TABLE IF EXISTS {prev_table}")

        return current_table, steps_completed

    def _check_quality(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        table: str,
        log: Any,
    ) -> None:
        """Run quality gate if configured. Records result as a lineage event."""
        if not cfg.quality:
            return
        q = cfg.quality
        resolved_sql = q.custom_sql.replace("_data", table) if q.custom_sql else None
        result = check_quality(
            conn,
            table,
            completeness=q.completeness,
            uniqueness=q.uniqueness,
            row_count_min=q.row_count_min,
            custom_sql=resolved_sql,
        )
        outcome = "pass" if result.passed else "fail"
        for gate, configured in (
            ("completeness", q.completeness is not None),
            ("uniqueness", q.uniqueness is not None),
            ("row_count_min", q.row_count_min is not None),
            ("custom_sql", q.custom_sql is not None),
        ):
            if configured:
                quality_gate_evaluations_total.labels(
                    pipeline=name, gate=gate, result=outcome
                ).inc()

        # Record quality result as a lineage event for full observability.
        if self._lineage is not None:
            quality_score = (
                result.completeness_score * result.uniqueness_score
                if result.completeness_score < 1.0 or result.uniqueness_score < 1.0
                else 1.0
            )
            count_row = conn.execute(f"SELECT count(*) FROM {table}").fetchone()
            row_count = int(count_row[0]) if count_row else 0
            self._lineage.record(
                operation="quality",
                layer=_infer_layer(name),
                source=table,
                destination=f"{_infer_layer(name)}/{name}",
                input_count=row_count,
                output_count=row_count if result.passed else 0,
                pipeline_name=name,
                step_name="quality_gate",
                quality_score=round(quality_score, 4),
                metadata={
                    "passed": result.passed,
                    "completeness": round(result.completeness_score, 4),
                    "uniqueness": round(result.uniqueness_score, 4),
                    "custom_passed": result.custom_passed,
                    "schema_violations": result.schema_violations,
                    **result.details,
                },
            )

        if not result.passed:
            msg = (
                f"Quality gate failed: completeness={result.completeness_score:.2f}, "
                f"uniqueness={result.uniqueness_score:.2f}"
            )
            raise PipelineStepError(step="quality", cause=msg, pipeline=name)
        log.info("quality gate passed")

    def _load(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        table: str,
        log: Any,
    ) -> int:
        """Write the final table to the correct lakehouse layer.

        Layer resolution (explicit > inferred):
        - cfg.target["layer"] if present.
        - Otherwise _infer_layer(pipeline_name) from name prefix.

        Format resolution: cfg.target["format"], default "parquet".
        """
        count_row = conn.execute(f"SELECT count(*) FROM {table}").fetchone()
        rows = int(count_row[0]) if count_row else 0

        if cfg.target:
            target_layer = cfg.target.get("layer", _infer_layer(name))
            target_format = cfg.target.get("format", "parquet")
        else:
            target_layer = _infer_layer(name)
            target_format = "parquet"

        layer_dir = self._data_dir / target_layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        output_name = cfg.destination or name
        output_path = layer_dir / (
            f"{output_name}.parquet" if target_format == "parquet" else output_name
        )

        # Inject audit metadata columns before writing. These are constant per run
        # so they don't affect row count — they are useful for lineage in downstream
        # SQL queries and external BI tools.
        ingested_at = datetime.datetime.now(datetime.UTC).isoformat()
        source_name = (cfg.source or name).replace("'", "''")
        safe_name = name.replace("'", "''")
        meta_table = f"{table}_with_meta"
        conn.execute(f"""
            CREATE OR REPLACE TABLE {meta_table} AS
            SELECT
                *,
                '{ingested_at}'::TIMESTAMPTZ AS _dex_ingested_at,
                '{safe_name}'               AS _dex_pipeline,
                '{target_layer}'            AS _dex_layer,
                '{source_name}'             AS _dex_source
            FROM {table}
        """)
        if target_format == "delta":
            arrow_table = conn.execute(f"SELECT * FROM {meta_table}").to_arrow_table()
            # mode="overwrite" mirrors Parquet COPY's full-file-replace semantics
            # so re-running a pipeline replaces the prior output either way.
            DeltaStorage(base_path=str(layer_dir), mode="overwrite").write(
                arrow_table.to_pylist(), output_name
            )
        else:
            conn.execute(f"COPY {meta_table} TO '{output_path}' (FORMAT PARQUET)")
        log.info(
            "load complete",
            layer=target_layer,
            format=target_format,
            path=str(output_path),
            rows=rows,
        )

        if self._lineage is not None:
            self._lineage.record(
                operation="load",
                layer=target_layer,
                source=f"bronze/{name}",
                destination=str(output_path),
                input_count=rows,
                output_count=rows,
                pipeline_name=name,
                step_name="load",
            )
        return rows

    def _post_load_hooks(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        table: str,
        log: Any,
    ) -> None:
        """Run optional post-load integrations: feature store save + vector ingest."""
        target_layer = (
            (cfg.target or {}).get("layer", _infer_layer(name))
            if cfg.target
            else _infer_layer(name)
        )

        # ── Feature store ──────────────────────────────────────────────────────
        if self._feature_store is not None and target_layer == "gold":
            with contextlib.suppress(Exception):
                rows_data = conn.execute(f"SELECT * FROM {table} LIMIT 50000").fetchall()  # noqa: S608
                desc = conn.execute(f"DESCRIBE {table}").fetchall()
                cols = [d[0] for d in desc]
                records = [dict(zip(cols, r, strict=True)) for r in rows_data]
                _entity_keys = {"movie_id", "tconst", "nconst", "director_id", "person_id"}
                entity_key = next(
                    (c for c in cols if c in _entity_keys),
                    cols[0],
                )
                self._feature_store.save_features(
                    feature_group=name,
                    data=records,
                    entity_key=entity_key,
                )
                log.info("feature store updated", feature_group=name, rows=len(records))

        # ── Vector store ingest ────────────────────────────────────────────────
        if self._vector_store is not None and target_layer in ("silver", "gold"):
            with contextlib.suppress(Exception):
                from dataenginex.ai.vectorstore import Document, RAGPipeline

                rows_data = conn.execute(f"SELECT * FROM {table} LIMIT 5000").fetchall()  # noqa: S608
                desc = conn.execute(f"DESCRIBE {table}").fetchall()
                cols = [d[0] for d in desc]
                skip = {"movie_id", "tconst", "nconst", "director_id", "person_id", "series_id"}
                text_cols = {"title", "director_name", "genre", "person_name", "original_title"}
                docs: list[Document] = []
                for row in rows_data:
                    record = dict(zip(cols, row, strict=True))
                    text = " | ".join(
                        f"{k}: {v}" for k, v in record.items() if v is not None and k not in skip
                    )[:512]
                    meta = {
                        "table": name,
                        "layer": target_layer,
                        **{
                            k: str(v) for k, v in record.items() if k in text_cols and v is not None
                        },
                    }
                    docs.append(Document(text=text, metadata=meta))

                rag = RAGPipeline(
                    store=self._vector_store,
                    embed_fn=self._embed_fn,
                    dimension=384,
                )
                rag.store.upsert(docs)
                log.info("vector store updated", table=name, documents=len(docs))

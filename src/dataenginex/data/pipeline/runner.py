"""PipelineRunner — config-driven data pipeline execution.

Flow: Config -> Extract (connector) -> Transform chain -> Quality gate -> Load (lakehouse layer)
"""

from __future__ import annotations

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
from dataenginex.data.connectors.duckdb import DuckDBConnector as _DuckDBConnector  # noqa: F401
from dataenginex.data.pipeline.dag import resolve_execution_order
from dataenginex.data.quality.gates import check_quality
from dataenginex.data.transforms import transform_registry

# Import to trigger registration
from dataenginex.data.transforms.sql import (  # noqa: F401
    CastTransform as _CastTransform,
)
from dataenginex.middleware.domain_metrics import quality_gate_evaluations_total
from dataenginex.warehouse.lineage import LineageBackend

logger = structlog.get_logger()


@dataclass
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
    for field in ("condition", "expression", "name", "columns", "key", "sql"):
        value = getattr(step, field, None)
        if value is not None:
            kwargs[field] = value
    kwargs.update(step.options)
    return kwargs


class PipelineRunner:
    """Execute data pipelines defined in dex.yaml.

    Args:
        config: Loaded DexConfig.
        data_dir: Root directory for lakehouse layer storage.
    """

    def __init__(
        self,
        config: DexConfig,
        data_dir: Path | None = None,
        project_dir: Path | None = None,
        lineage: LineageBackend | None = None,
    ) -> None:
        self._config = config
        self._data_dir = data_dir or Path(".dex/lakehouse")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._project_dir = project_dir
        self._lineage = lineage

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

        db_path = self._data_dir / f"{pipeline_name}.duckdb"
        conn = duckdb.connect(str(db_path))

        try:
            return self._execute(conn, pipeline_name, pipeline_config, log)
        except (PipelineError, PipelineStepError, KeyError):
            raise
        except Exception as e:
            log.error("pipeline failed", error=str(e))
            return PipelineResult(pipeline=pipeline_name, success=False, error=str(e))
        finally:
            conn.close()

    def _execute(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        log: Any,
    ) -> PipelineResult:
        """Core pipeline execution: extract -> transform -> quality -> load."""
        rows_input = self._extract(conn, name, cfg, log)
        current_table, steps = self._transform(conn, name, cfg, log)
        self._check_quality(conn, name, cfg, current_table, log)
        rows_output = self._load(conn, name, cfg, current_table, log)

        return PipelineResult(
            pipeline=name,
            success=True,
            rows_input=rows_input,
            rows_output=rows_output,
            steps_completed=steps,
        )

    def _extract(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        log: Any,
    ) -> int:
        """Extract source data into DuckDB bronze table. Returns row count."""
        sources = self._config.data.sources
        if cfg.source not in sources:
            msg = f"Source '{cfg.source}' not found"
            raise PipelineStepError(step="extract", cause=msg, pipeline=name)

        source_config = sources[cfg.source]
        connector_cls = connector_registry.get(source_config.type)

        connector_kwargs: dict[str, Any] = dict(source_config.connection)
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

        bronze_arrow = pa.Table.from_pylist(raw_data)  # noqa: F841 — referenced by DuckDB SQL
        conn.execute("CREATE OR REPLACE TABLE bronze AS SELECT * FROM bronze_arrow")
        log.info("extract complete", source=cfg.source, rows=len(raw_data))
        if self._lineage is not None:
            self._lineage.record(
                operation="ingest",
                layer="bronze",
                source=cfg.source,
                destination=f"bronze/{name}",
                input_count=len(raw_data),
                output_count=len(raw_data),
                pipeline_name=name,
                step_name="extract",
            )
        return len(raw_data)

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

            current_table = transform.apply(conn, current_table)
            steps_completed += 1
            log.info("transform complete", step=i, type=step_config.type)

        return current_table, steps_completed

    def _check_quality(
        self,
        conn: duckdb.DuckDBPyConnection,
        name: str,
        cfg: PipelineConfig,
        table: str,
        log: Any,
    ) -> None:
        """Run quality gate if configured."""
        if not cfg.quality:
            return
        q = cfg.quality
        result = check_quality(
            conn,
            table,
            completeness=q.completeness,
            uniqueness=q.uniqueness,
            custom_sql=q.custom_sql,
        )
        outcome = "pass" if result.passed else "fail"
        for gate, configured in (
            ("completeness", q.completeness is not None),
            ("uniqueness", q.uniqueness is not None),
            ("custom_sql", q.custom_sql is not None),
        ):
            if configured:
                quality_gate_evaluations_total.labels(
                    pipeline=name, gate=gate, result=outcome
                ).inc()
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
        """Write final table to lakehouse layer as parquet. Returns row count."""
        count_row = conn.execute(f"SELECT count(*) FROM {table}").fetchone()
        rows = int(count_row[0]) if count_row else 0
        target_layer = "silver"
        if cfg.target:
            target_layer = cfg.target.get("layer", "silver")

        layer_dir = self._data_dir / target_layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        output_path = layer_dir / f"{name}.parquet"
        conn.execute(f"COPY {table} TO '{output_path}' (FORMAT PARQUET)")
        log.info("load complete", layer=target_layer, path=str(output_path), rows=rows)
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

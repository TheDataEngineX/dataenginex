"""DexEngine — primary entry point for the dataenginex library.

Usage::

    from dataenginex import DexEngine

    engine = DexEngine("path/to/dex.yaml")
    result = engine.run_pipeline("ingest")
    engine.close()

The engine initialises all subsystems (data, ML, AI) from the config file
and persists all state to ``.dex/store.duckdb`` alongside ``dex.yaml``.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import duckdb
import structlog
import yaml

from dataenginex.config import load_config, validate_config
from dataenginex.config.schema import DexConfig
from dataenginex.lakehouse.catalog import CatalogEntry as LakehouseCatalogEntry
from dataenginex.lakehouse.catalog import DataCatalog
from dataenginex.plugins.registry import PluginRegistry, discover
from dataenginex.store import DexStore

logger = structlog.get_logger()

__all__ = ["DexBackend", "DexEngine"]


# ---------------------------------------------------------------------------
# Protocol — structural interface consumed by state classes / tests
# ---------------------------------------------------------------------------


@runtime_checkable
class DexBackend(Protocol):
    """Structural interface satisfied by DexEngine.

    Depend on this Protocol rather than DexEngine to keep state classes
    and tests decoupled from the concrete implementation.
    """

    config: Any
    store: Any
    agents: dict[str, Any]
    tracker: Any
    feature_store: Any
    serving_engine: Any
    llm: Any
    ai_memory: Any
    plugins: Any
    catalog: Any

    def run_pipeline(self, name: str) -> Any: ...
    def pipeline_stats(self) -> dict[str, int]: ...
    def pipeline_last_run(self, name: str) -> Any | None: ...
    def update_pipeline_schedule(self, name: str, schedule: str | None) -> None: ...

    def warehouse_layers(self) -> list[dict[str, Any]]: ...
    def warehouse_tables(self, layer: str) -> list[dict[str, Any]]: ...
    def warehouse_table_schema(self, table_name: str, layer: str) -> list[dict[str, Any]]: ...
    def warehouse_table_stats(self, table_name: str, layer: str) -> dict[str, Any]: ...
    def warehouse_table_lineage(self, table_name: str, layer: str) -> dict[str, Any]: ...

    def source_row_count(self, source_name: str) -> int | None: ...
    def source_schema(self, source_name: str) -> list[dict[str, Any]] | None: ...
    def source_sample(
        self, source_name: str, limit: int, offset: int
    ) -> list[dict[str, Any]] | None: ...
    def source_stats(self, source_name: str) -> dict[str, Any] | None: ...

    def quality_check_table(self, table_name: str) -> dict[str, Any] | None: ...
    def quality_check_all_tables(self) -> dict[str, Any]: ...
    def quality_history(self) -> dict[str, Any]: ...

    def add_pipeline(self, name: str, source: str, schedule: str, destination: str) -> None: ...
    def delete_pipeline(self, name: str) -> None: ...
    def add_source(self, name: str, type_: str, path: str, url: str) -> None: ...
    def delete_source(self, name: str) -> None: ...
    def add_agent(self, name: str, runtime: str, system_prompt: str) -> None: ...
    def delete_agent(self, name: str) -> None: ...
    def delete_model(self, name: str) -> None: ...

    def health(self) -> dict[str, Any]: ...
    def close(self) -> None: ...


# ---------------------------------------------------------------------------
# DexEngine
# ---------------------------------------------------------------------------


class DexEngine:
    """Local dataenginex engine — direct library access, no HTTP.

    Initialises all subsystems from a ``dex.yaml`` config file.
    All persistent state is stored in ``.dex/store.duckdb`` next to the
    config file.

    Args:
        config_path: Path to a ``dex.yaml`` file.
    """

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path).resolve()
        if not self.config_path.exists():
            msg = f"Config file not found: {self.config_path}"
            raise FileNotFoundError(msg)

        self.config: DexConfig = load_config(self.config_path)
        validate_config(self.config)

        self.project_dir = self.config_path.parent
        self._dex_dir = self.project_dir / ".dex"
        self._dex_dir.mkdir(parents=True, exist_ok=True)

        # Single persistent store — replaces all JSON files
        self.store = DexStore(self._dex_dir / "store.duckdb")

        # Lakehouse catalog — tracks every dataset written to .dex/lakehouse/
        self.catalog = DataCatalog(persist_path=self._dex_dir / "catalog.json")

        # Data pipeline runner — passes store as lineage backend
        from dataenginex.data.pipeline.runner import PipelineRunner

        self.pipeline_runner = PipelineRunner(
            self.config,
            data_dir=self._dex_dir / "lakehouse",
            project_dir=self.project_dir,
            lineage=self.store,  # DexStore.record() satisfies PersistentLineage interface
        )

        # ML backends
        self.tracker: Any = self._init_ml_tracker()
        self.feature_store: Any = self._init_ml_feature_store()
        self.serving_engine: Any = self._init_ml_serving()

        # AI backends
        self.llm: Any = None
        self.agents: dict[str, Any] = {}
        self._init_ai()

        # AI layer — memory, routing, sandbox
        self.ai_memory: Any = None
        self.ai_episodic: Any = None
        self.ai_audit: Any = None
        self.ai_cost: Any = None
        self.ai_metrics: Any = None
        self.checkpoint_mgr: Any = None
        self.sandbox: Any = None
        self.model_router: Any = None
        self._init_ai_layer()

        # Plugin discovery
        self.plugins = PluginRegistry()
        self._load_plugins()

        logger.info(
            "DexEngine ready",
            project=self.config.project.name,
            config=str(self.config_path),
        )

    # -------------------------------------------------------------------------
    # Pipeline
    # -------------------------------------------------------------------------

    def run_pipeline(self, name: str) -> Any:
        import time

        from dataenginex.data.pipeline.runner import PipelineResult

        start = time.monotonic()
        result: PipelineResult = self.pipeline_runner.run(name)
        duration_ms = (time.monotonic() - start) * 1000

        self.store.record_pipeline_run(
            pipeline_name=name,
            success=result.success,
            rows_input=result.rows_input,
            rows_output=result.rows_output,
            steps_completed=result.steps_completed,
            duration_ms=duration_ms,
            error=result.error,
        )
        self.store.log_audit(
            action="pipeline_run",
            resource=name,
            resource_type="pipeline",
            status="success" if result.success else "failure",
            details={
                "rows_input": result.rows_input,
                "rows_output": result.rows_output,
                "duration_ms": round(duration_ms, 2),
                "error": result.error,
            },
        )

        # Register output table in catalog if pipeline has a destination
        pipeline_cfg = self.config.data.pipelines.get(name)
        if pipeline_cfg and pipeline_cfg.destination and result.success:
            target_layer = (pipeline_cfg.target or {}).get("layer", "silver")
            table_path = (
                self._dex_dir / "lakehouse" / target_layer / f"{pipeline_cfg.destination}.parquet"
            )
            if table_path.exists():
                self.catalog.register(
                    LakehouseCatalogEntry(
                        name=pipeline_cfg.destination,
                        layer=target_layer,
                        format="parquet",
                        location=str(table_path),
                        record_count=result.rows_output,
                    )
                )

        return result

    def pipeline_stats(self) -> dict[str, int]:
        pipelines = self.config.data.pipelines or {}
        total = len(pipelines)
        scheduled = sum(1 for p in pipelines.values() if p.schedule)
        failed = sum(
            1 for name in pipelines
            if (run := self.store.get_last_pipeline_run(name)) and not run.success
        )
        return {"total": total, "scheduled": scheduled, "failed": failed, "running": 0}

    def pipeline_last_run(self, name: str) -> Any | None:
        return self.store.get_last_pipeline_run(name)

    def update_pipeline_schedule(self, name: str, schedule: str | None) -> None:
        if name not in self.config.data.pipelines:
            msg = f"Pipeline '{name}' not found"
            raise KeyError(msg)
        self.config.data.pipelines[name].schedule = schedule
        self._save_config()

    # -------------------------------------------------------------------------
    # CRUD — pipelines / sources / agents / models
    # -------------------------------------------------------------------------

    def add_pipeline(
        self, name: str, source: str, schedule: str = "", destination: str = ""
    ) -> None:
        from dataenginex.config.schema import PipelineConfig

        self.config.data.pipelines[name] = PipelineConfig(
            source=source, schedule=schedule or None, destination=destination or None
        )
        self._save_config()

    def delete_pipeline(self, name: str) -> None:
        self.config.data.pipelines.pop(name, None)
        self._save_config()

    def add_source(self, name: str, type_: str, path: str = "", url: str = "") -> None:
        from dataenginex.config.schema import SourceConfig

        self.config.data.sources[name] = SourceConfig(
            type=type_, path=path or None, url=url or None
        )
        self._save_config()

    def delete_source(self, name: str) -> None:
        self.config.data.sources.pop(name, None)
        self._save_config()

    def add_agent(
        self, name: str, runtime: str = "builtin", system_prompt: str = ""
    ) -> None:
        from dataenginex.config.schema import AgentConfig

        self.config.ai.agents[name] = AgentConfig(runtime=runtime, system_prompt=system_prompt)
        self._save_config()

    def delete_agent(self, name: str) -> None:
        if self.config.ai:
            self.config.ai.agents.pop(name, None)
        self._save_config()

    def delete_model(self, name: str) -> None:
        self.store.delete_model(name)

    # -------------------------------------------------------------------------
    # Warehouse — reads from .dex/lakehouse/, registers in catalog
    # -------------------------------------------------------------------------

    def warehouse_layers(self) -> list[dict[str, Any]]:
        lakehouse = self._dex_dir / "lakehouse"
        layers: list[dict[str, Any]] = []
        for layer_name in ("bronze", "silver", "gold"):
            layer_path = lakehouse / layer_name
            table_count = len(list(layer_path.glob("*.parquet"))) if layer_path.exists() else 0
            layers.append({"name": layer_name, "table_count": table_count})
        return layers

    def warehouse_tables(self, layer: str) -> list[dict[str, Any]]:
        import datetime

        layer_path = self._dex_dir / "lakehouse" / layer
        if not layer_path.exists():
            return []
        tables: list[dict[str, Any]] = []
        for f in sorted(layer_path.glob("*.parquet")):
            try:
                stat = f.stat()
                size_bytes = stat.st_size
                size = (
                    f"{size_bytes / 1024:.1f} KB"
                    if size_bytes < 1_048_576
                    else f"{size_bytes / 1_048_576:.1f} MB"
                )
                updated_at = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%b %d %H:%M")
                row_count: int | None = None
                with contextlib.suppress(Exception), self._duckdb() as conn:
                    row = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{f}')").fetchone()
                    row_count = int(row[0]) if row else None

                # Register/refresh in catalog
                self.catalog.register(
                    LakehouseCatalogEntry(
                        name=f.stem, layer=layer, format="parquet",
                        location=str(f), record_count=row_count or 0,
                    )
                )
                tables.append({
                    "name": f.stem, "path": str(f), "size_bytes": size_bytes,
                    "size": size, "row_count": row_count, "updated_at": updated_at,
                })
            except OSError:
                continue
        return tables

    def warehouse_table_schema(self, table_name: str, layer: str) -> list[dict[str, Any]]:
        table_path = self._dex_dir / "lakehouse" / layer / f"{table_name}.parquet"
        if not table_path.exists():
            return []
        try:
            with self._duckdb() as conn:
                conn.execute(f"CREATE VIEW IF NOT EXISTS _wts AS SELECT * FROM '{table_path}'")
                cols = conn.execute("DESCRIBE _wts").fetchall()
                conn.execute("DROP VIEW IF EXISTS _wts")
                return [{"name": r[0], "dtype": r[1], "nullable": r[2] == "YES"} for r in cols]
        except Exception as exc:
            logger.warning("schema fetch failed", table=table_name, layer=layer, error=str(exc))
            return []

    def warehouse_table_stats(self, table_name: str, layer: str) -> dict[str, Any]:
        table_path = self._dex_dir / "lakehouse" / layer / f"{table_name}.parquet"
        if not table_path.exists():
            return {}
        size = table_path.stat().st_size
        schema = self.warehouse_table_schema(table_name, layer)
        row_count = None
        with contextlib.suppress(Exception), self._duckdb() as conn:
            row_count = conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{table_path}')"
            ).fetchone()[0]
        return {"size_bytes": size, "column_count": len(schema), "row_count": row_count}

    def warehouse_table_lineage(self, table_name: str, layer: str) -> dict[str, Any]:
        upstream: list[dict[str, Any]] = []
        downstream: list[dict[str, Any]] = []
        for ev in self.store.all_events:
            if ev.destination == table_name and ev.layer == layer and ev.parent_id:
                parent = self.store.get_lineage_event(ev.parent_id)
                if parent:
                    upstream.append({
                        "name": parent.destination, "layer": parent.layer,
                        "event_id": parent.event_id,
                    })
            if ev.source == table_name and ev.layer == layer:
                for child in self.store.get_lineage_children(ev.event_id):
                    downstream.append({
                        "name": child.destination, "layer": child.layer,
                        "event_id": child.event_id,
                    })
        return {"upstream": upstream, "downstream": downstream}

    # -------------------------------------------------------------------------
    # Sources
    # -------------------------------------------------------------------------

    def _source_read_fn(self, source_name: str) -> str | None:
        src = self.config.data.sources.get(source_name)
        if src is None:
            return None
        type_str = src.type.value if hasattr(src.type, "value") else str(src.type)
        _map = {
            "csv": "read_csv_auto", "parquet": "read_parquet",
            "json": "read_json_auto", "jsonl": "read_ndjson_auto",
        }
        return _map.get(type_str)

    def _source_path(self, source_name: str) -> tuple[Any, Path] | None:
        src = self.config.data.sources.get(source_name)
        if src is None:
            return None
        raw = getattr(src, "path", None) or getattr(src, "uri", None)
        if not raw:
            return None
        p = Path(raw)
        if not p.is_absolute():
            p = self.project_dir / p
        return src, p.resolve()

    def source_row_count(self, source_name: str) -> int | None:
        result = self._source_path(source_name)
        if result is None:
            return None
        _, resolved = result
        read_fn = self._source_read_fn(source_name)
        if read_fn is None:
            return None
        with contextlib.suppress(Exception), duckdb.connect(":memory:") as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM {read_fn}('{resolved}')").fetchone()
            return row[0] if row else 0
        return None

    def source_schema(self, source_name: str) -> list[dict[str, Any]] | None:
        result = self._source_path(source_name)
        if result is None:
            return None
        _, resolved = result
        read_fn = self._source_read_fn(source_name)
        if read_fn is None:
            return None
        with contextlib.suppress(Exception), duckdb.connect(":memory:") as conn:
            rows = conn.execute(
                f"DESCRIBE SELECT * FROM {read_fn}('{resolved}') LIMIT 1"
            ).fetchall()
            return [
                {"column_name": r[0], "column_type": r[1], "nullable": r[3] == "YES"}
                for r in rows
            ]
        return None

    def source_sample(
        self, source_name: str, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]] | None:
        result = self._source_path(source_name)
        if result is None:
            return None
        _, resolved = result
        read_fn = self._source_read_fn(source_name)
        if read_fn is None:
            return None
        with contextlib.suppress(Exception), duckdb.connect(":memory:") as conn:
            cursor = conn.execute(
                f"SELECT * FROM {read_fn}('{resolved}') LIMIT {limit} OFFSET {offset}"
            )
            col_names = [d[0] for d in cursor.description] if cursor.description else []
            return [dict(zip(col_names, row, strict=True)) for row in cursor.fetchall()]
        return None

    def source_stats(self, source_name: str) -> dict[str, Any] | None:
        result = self._source_path(source_name)
        if result is None:
            return None
        src, resolved = result
        size_bytes = resolved.stat().st_size if resolved.exists() else 0
        schema = self.source_schema(source_name)
        return {
            "row_count": self.source_row_count(source_name),
            "column_count": len(schema) if schema else None,
            "size_bytes": size_bytes,
            "path": str(resolved),
            "connector_type": getattr(src, "type", "unknown"),
        }

    # -------------------------------------------------------------------------
    # Quality
    # -------------------------------------------------------------------------

    def quality_check_table(self, table_name: str) -> dict[str, Any] | None:
        from dataenginex.data.quality.gates import ColumnSpec, check_quality

        layer, _, tbl = table_name.partition(".")
        if not layer or not tbl:
            return None
        table_path = self._dex_dir / "lakehouse" / layer / f"{tbl}.parquet"
        if not table_path.exists():
            return None
        try:
            with self._duckdb() as conn:
                conn.execute(f"CREATE VIEW IF NOT EXISTS _qc AS SELECT * FROM '{table_path}'")
                col_result = conn.execute("DESCRIBE _qc").fetchall()
                column_names = [r[0] for r in col_result]
                column_specs = [
                    ColumnSpec(name=r[0], dtype=r[1], nullable=True) for r in col_result
                ]
                result = check_quality(
                    conn, "_qc",
                    completeness=0.0, uniqueness=column_names, schema=column_specs,
                )
                conn.execute("DROP VIEW IF EXISTS _qc")
                custom_weight = 1.0 if result.custom_passed else 0.0
                score = (
                    result.completeness_score * 0.4
                    + result.uniqueness_score * 0.3
                    + custom_weight * 0.3
                )
                return {
                    "score": score, "completeness": result.completeness_score,
                    "uniqueness": result.uniqueness_score, "custom_passed": result.custom_passed,
                    "schema_violations": result.schema_violations,
                    "passed": result.passed, "details": result.details,
                }
        except Exception as exc:
            logger.warning("quality check failed", table=table_name, error=str(exc))
            return None

    def quality_check_all_tables(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for layer in ("bronze", "silver", "gold"):
            for table in self.warehouse_tables(layer):
                full_name = f"{layer}.{table['name']}"
                results[full_name] = self.quality_check_table(full_name)
        self.store.record_quality_run(results)
        return results

    def quality_history(self) -> dict[str, Any]:
        return self.store.get_quality_history()

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "project": self.config.project.name,
            "components": {
                "pipeline_runner": self.pipeline_runner is not None,
                "store": self.store is not None,
                "catalog": self.catalog is not None,
                "tracker": self.tracker is not None,
                "feature_store": self.feature_store is not None,
                "serving_engine": self.serving_engine is not None,
                "llm": self.llm is not None,
                "agents": len(self.agents),
                "ai_memory": self.ai_memory is not None,
                "plugins": self.plugins.count,
            },
        }

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def close(self) -> None:
        with contextlib.suppress(Exception):
            if self.feature_store and hasattr(self.feature_store, "close"):
                self.feature_store.close()
        self.store.close()
        logger.info("DexEngine shutdown", project=self.config.project.name)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @contextlib.contextmanager
    def _duckdb(self) -> Iterator[Any]:
        """Yield the DexStore's DuckDB connection for ad-hoc queries."""
        yield self.store.connection

    def _save_config(self) -> None:
        dump = self.config.model_dump()
        with open(self.config_path, "w") as f:
            yaml.dump(dump, f, default_flow_style=False, sort_keys=False)

    def _init_ml_tracker(self) -> Any:
        try:
            from typing import cast as _cast

            import dataenginex.ml.tracking.builtin  # noqa: F401
            from dataenginex.ml.tracking import tracker_registry

            cls: Any = _cast(Any, tracker_registry.get(self.config.ml.tracking.backend))
            return cls(storage_dir=str(self._dex_dir / "tracking"))
        except Exception:
            logger.warning("tracker init failed")
            return None

    def _init_ml_feature_store(self) -> Any:
        try:
            import dataenginex.ml.features.builtin  # noqa: F401
            from dataenginex.ml.features import feature_store_registry

            cls = feature_store_registry.get(self.config.ml.features.backend)
            return cls(**self.config.ml.features.options)
        except Exception:
            logger.warning("feature store init failed")
            return None

    def _init_ml_serving(self) -> Any:
        try:
            from typing import cast

            import dataenginex.ml.serving_engine.builtin  # noqa: F401

            # Use store-backed model registry
            from dataenginex.ml.registry import ModelRegistry
            from dataenginex.ml.serving_engine import serving_registry

            registry_path = str(self._dex_dir / "models" / "registry.json")
            model_registry = ModelRegistry(persist_path=registry_path)
            cls: Any = cast(Any, serving_registry.get(self.config.ml.serving.engine))
            return cls(model_registry=model_registry, model_dir=str(self._dex_dir / "models"))
        except Exception:
            logger.warning("serving engine init failed")
            return None

    def _init_ai(self) -> None:
        try:
            from dataenginex.ai.llm import get_llm_provider

            self.llm = get_llm_provider(self.config.ai.llm.provider, model=self.config.ai.llm.model)
        except Exception:
            self.llm = None
            logger.warning("LLM provider unavailable")

        if self.llm is None:
            return

        try:
            from typing import cast

            import dataenginex.ai.agents.builtin  # noqa: F401
            from dataenginex.ai.agents import agent_registry
            from dataenginex.ai.tools import tool_registry
            from dataenginex.ai.tools.builtin import register_builtin_tools

            register_builtin_tools()
            for name, agent_cfg in self.config.ai.agents.items():
                agent_llm = self.llm
                if agent_cfg.model:
                    with contextlib.suppress(Exception):
                        from dataenginex.ai.llm import get_llm_provider as _get
                        agent_llm = _get(self.config.ai.llm.provider, model=agent_cfg.model)
                cls: Any = cast(Any, agent_registry.get(agent_cfg.runtime))
                self.agents[name] = cls(
                    llm=agent_llm, system_prompt=agent_cfg.system_prompt,
                    tools=tool_registry, max_iterations=agent_cfg.max_iterations,
                )
                logger.info("agent initialized", agent=name)
        except Exception:
            logger.warning("agent initialization failed")

    def _init_ai_layer(self) -> None:
        try:
            from dataenginex.ai.memory.base import ShortTermMemory
            from dataenginex.ai.observability.audit import AuditLog
            from dataenginex.ai.observability.cost import CostTracker
            from dataenginex.ai.observability.metrics import AgentMetrics
            from dataenginex.ai.runtime.checkpoint import CheckpointManager
            from dataenginex.ai.runtime.sandbox import Sandbox

            self.ai_memory = ShortTermMemory(max_entries=200)
            self.ai_audit = AuditLog()
            self.ai_cost = CostTracker()
            self.ai_metrics = AgentMetrics()
            self.checkpoint_mgr = CheckpointManager()
            self.sandbox = Sandbox()
            self._init_model_router()
            logger.info("AI layer initialized")
        except Exception:
            logger.warning("AI layer init failed")

    def _init_model_router(self) -> None:
        import os

        from dataenginex.ai.routing.router import ModelRouter

        providers: dict[str, Any] = {}
        if os.environ.get("ANTHROPIC_API_KEY"):
            from dataenginex.ai.routing.anthropic import AnthropicProvider
            providers["anthropic"] = AnthropicProvider()
        if os.environ.get("OPENAI_API_KEY"):
            from dataenginex.ai.routing.openai import OpenAIProvider
            providers["openai"] = OpenAIProvider()

        from dataenginex.ai.routing.ollama import OllamaProvider
        providers.setdefault("ollama", OllamaProvider())

        if providers:
            self.model_router = ModelRouter(providers)

    def _load_plugins(self) -> None:
        try:
            for plugin in discover():
                with contextlib.suppress(ValueError):
                    self.plugins.register(plugin)
            logger.info("plugins loaded", count=self.plugins.count)
        except Exception:
            logger.warning("plugin discovery failed")

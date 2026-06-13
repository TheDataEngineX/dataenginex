"""Built-in tools for agent runtimes.

Provides tools that agents can invoke: SQL queries, ML inference,
semantic search, pipeline status, etc.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from dataenginex import _json
from dataenginex.ai.tools import ToolSpec, tool_registry

if TYPE_CHECKING:
    pass

# Names available after register_builtin_tools() — used by the config validator.
BUILTIN_TOOL_NAMES: frozenset[str] = frozenset(
    {"query", "list_tools", "echo", "predict", "search_similar"}
)

logger = structlog.get_logger()


# ── SQL / lakehouse ────────────────────────────────────────────────────────────


def _query_sql(sql: str, database: str = ":memory:") -> list[dict[str, Any]]:
    """Execute a SQL query via DuckDB and return results."""
    import duckdb

    conn = duckdb.connect(database)
    try:
        result = conn.execute(sql)
        description = result.description or []
        if not description:
            return []
        columns = [desc[0] for desc in description]
        return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
    finally:
        conn.close()


def _make_lakehouse_query(lakehouse_dir: Path) -> Callable[[str], list[dict[str, Any]]]:
    """Return a query function that pre-registers all lakehouse parquet files as views."""

    def _query_with_lakehouse(sql: str) -> list[dict[str, Any]]:
        import duckdb

        conn = duckdb.connect(":memory:")
        try:
            for layer in ("bronze", "silver", "gold"):
                layer_path = lakehouse_dir / layer
                if not layer_path.exists():
                    continue
                for pf in sorted(layer_path.glob("*.parquet")):
                    safe = str(pf).replace("'", "''")
                    with contextlib.suppress(Exception):
                        conn.execute(
                            f"CREATE OR REPLACE VIEW {pf.stem}"
                            f" AS SELECT * FROM read_parquet('{safe}')"
                        )
            result = conn.execute(sql)
            description = result.description or []
            if not description:
                return []
            columns = [desc[0] for desc in description]
            return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
        finally:
            conn.close()

    return _query_with_lakehouse


# ── ML inference ───────────────────────────────────────────────────────────────


def _make_predict(
    models_dir: Path,
    registry_path: Path | None = None,
) -> Callable[..., Any]:
    """Return a predict function that loads and calls sklearn models by name.

    Looks up the model artifact path from registry.json (if present) or falls
    back to ``<models_dir>/<model_name>_v*.pkl`` glob.
    """

    def _predict(model_name: str, features: dict[str, Any]) -> Any:
        import pickle

        artifact: Path | None = None

        # Try registry first
        reg = registry_path or models_dir / "registry.json"
        if reg.exists():
            with contextlib.suppress(Exception):
                data = _json.loads(reg.read_text())
                versions = data.get(model_name, [])
                if versions:
                    # Prefer production stage, else latest
                    prod = [v for v in versions if v.get("stage") == "production"]
                    entry = (prod or versions)[-1]
                    artifact = Path(entry["artifact_path"])

        # Fallback: glob for <model_name>_v*.pkl
        if artifact is None or not artifact.exists():
            candidates = sorted(models_dir.glob(f"{model_name}_v*.pkl"))
            if candidates:
                artifact = candidates[-1]

        if artifact is None or not artifact.exists():
            available = [p.stem.rsplit("_v", 1)[0] for p in models_dir.glob("*_v*.pkl")]
            return {"error": f"Model '{model_name}' not found. Available: {list(set(available))}"}

        try:
            with artifact.open("rb") as f:
                model = pickle.load(f)  # noqa: S301

            import pandas as pd  # type: ignore[import-untyped]

            df = pd.DataFrame([features])
            prediction = model.predict(df)
            result: Any = prediction.tolist() if hasattr(prediction, "tolist") else list(prediction)
            return {"model": model_name, "prediction": result, "artifact": artifact.name}
        except Exception as exc:
            return {"error": f"Prediction failed: {exc}"}

    return _predict


# ── Semantic search ────────────────────────────────────────────────────────────


def _make_search_similar(
    vector_store: Any,
    embed_fn: Any | None = None,
) -> Callable[..., list[dict[str, Any]]]:
    """Return a semantic search function backed by the shared vector store."""

    def _search_similar(query: str, top_k: int = 5) -> list[dict[str, Any]]:
        try:
            from dataenginex.ai.vectorstore import RAGPipeline

            rag = RAGPipeline(store=vector_store, embed_fn=embed_fn, dimension=384)
            results = rag.query(query, top_k=top_k)
            if not results:
                return [{"info": "Vector store is empty — run a gold pipeline to populate it."}]
            return [
                {
                    "id": r.document.id,
                    "text": r.document.text,
                    "score": round(r.score, 4),
                    **r.document.metadata,
                }
                for r in results
            ]
        except Exception as exc:
            return [{"error": str(exc)}]

    return _search_similar


# ── Builtins ───────────────────────────────────────────────────────────────────


def _list_tools() -> list[str]:
    return tool_registry.list()


def _echo(message: str) -> str:
    return message


# ── Registration ───────────────────────────────────────────────────────────────


def register_builtin_tools(
    lakehouse_dir: Path | None = None,
    models_dir: Path | None = None,
    vector_store: Any = None,
    embed_fn: Any | None = None,
) -> None:
    """Register all built-in tools.

    Args:
        lakehouse_dir: When provided, the ``query`` tool pre-registers every
            parquet file in bronze/silver/gold as a DuckDB view.
        models_dir: When provided, registers a ``predict`` tool that loads
            sklearn models from the model registry.
        vector_store: When provided, registers a ``search_similar`` tool for
            semantic search over embedded lakehouse documents.
        embed_fn: Embedding callable for ``search_similar``. Falls back to
            hash-based embedding when ``None``.
    """
    query_fn: Callable[..., Any]
    if lakehouse_dir:
        query_fn = _make_lakehouse_query(lakehouse_dir)
        query_desc = (
            "Execute a SQL query against the lakehouse. "
            "All bronze/silver/gold tables are pre-registered as views."
        )
        query_params: dict[str, str] = {"sql": "str"}
    else:
        query_fn = _query_sql
        query_desc = "Execute a SQL query via DuckDB"
        query_params = {"sql": "str", "database": "str (optional)"}

    builtins: list[ToolSpec] = [
        ToolSpec(name="query", description=query_desc, fn=query_fn, parameters=query_params),
        ToolSpec(
            name="list_tools",
            description="List all available tools",
            fn=_list_tools,
            parameters={},
        ),
        ToolSpec(
            name="echo",
            description="Echo a message back",
            fn=_echo,
            parameters={"message": "str"},
        ),
    ]

    if models_dir and models_dir.exists():
        registry_path = models_dir / "registry.json"
        predict_fn = _make_predict(models_dir, registry_path if registry_path.exists() else None)
        builtins.append(
            ToolSpec(
                name="predict",
                description=(
                    "Run ML model inference. "
                    "Args: model_name (str), features (dict of feature→value). "
                    "Available models: "
                    + ", ".join(
                        p.stem.rsplit("_v", 1)[0] for p in sorted(models_dir.glob("*_v*.pkl"))
                    )
                ),
                fn=predict_fn,
                parameters={"model_name": "str", "features": "dict"},
            )
        )

    if vector_store is not None:
        search_fn = _make_search_similar(vector_store, embed_fn)
        builtins.append(
            ToolSpec(
                name="search_similar",
                description=(
                    "Semantic similarity search over the movie catalog. "
                    "Finds movies similar to a natural-language query. "
                    "Args: query (str), top_k (int, default 5)."
                ),
                fn=search_fn,
                parameters={"query": "str", "top_k": "int (optional, default 5)"},
            )
        )

    for spec in builtins:
        tool_registry.register(spec)

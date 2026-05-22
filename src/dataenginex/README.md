# dataenginex

Unified Data + ML + AI **library**. Config-driven, self-hosted, production-ready.

`dataenginex` is a pure Python library — no HTTP server. Your application owns the server layer.

## Install

```bash
# Core (DuckDB, structlog, Pydantic, Click, arq, asyncpg, qdrant-client)
pip install dataenginex

# Optional extras
pip install "dataenginex[cloud]"          # S3 + GCS + BigQuery storage backends
pip install "dataenginex[observability]"  # Langfuse LLM call tracing
```

> **LiteLLM:** Install separately — it pins `python-dotenv==1.0.1` which conflicts
> with dataenginex's `python-dotenv>=1.2.2`.
> ```bash
> pip install 'litellm>=1.83.3' --no-deps
> ```

## Submodules

| Module | Description |
|--------|-------------|
| `dataenginex.engine` | `DexEngine` — single entry point; loads config, inits store, wires all backends |
| `dataenginex.store` | `DexStore` — DuckDB-backed persistence (`.dex/store.duckdb`) |
| `dataenginex.config` | `dex.yaml` schema, loader, env var resolution, layering |
| `dataenginex.core` | Exceptions, `Base*` ABCs, `BackendRegistry` |
| `dataenginex.cli` | `dex` CLI (`validate`, `version`, `init`) |
| `dataenginex.api` | HTTP helpers: error types, response models (no server bundled) |
| `dataenginex.data` | Connectors, pipeline runner, schema registry, profiler |
| `dataenginex.ml` | Classical ML: training, model registry, serving, drift detection |
| `dataenginex.ai` | LLM providers, agents, RAG, vectorstore, memory, observability |
| `dataenginex.orchestration` | `DriftScheduler`, background scheduling |
| `dataenginex.middleware` | structlog config, Prometheus metrics |
| `dataenginex.lakehouse` | Storage backends (local, S3, GCS), catalog, partitioning |
| `dataenginex.warehouse` | SQL transforms, lineage tracking |
| `dataenginex.plugins` | Entry-point plugin discovery |

## Quick Usage

```python
from pathlib import Path
from dataenginex.engine import DexEngine

# Load config and initialize all backends
engine = DexEngine(Path("dex.yaml"))

# Data
engine.run_pipeline("clean_users")
sources = list(engine.config.data.sources.keys())

# ML
models = engine.model_registry.list_models()
result = engine.model_registry.predict("churn_model", features)

# AI
response = engine.agents["assistant"].chat("summarize the latest run")

# Persistence (DuckDB)
runs = engine.store.list_pipeline_runs(limit=10)
```

```python
# Config system only
from dataenginex.config import load_config
cfg = load_config(Path("dex.yaml"))

# Core interfaces + registry
from dataenginex.core.interfaces import BaseConnector
from dataenginex.core.registry import BackendRegistry

# ML
from dataenginex.ml import ModelRegistry, SklearnTrainer

# AI
from dataenginex.ai.llm import get_llm_provider
from dataenginex.ai.vectorstore import VectorStoreBackend
```

## Source and Docs

- Repository: https://github.com/TheDataEngineX/DEX
- Documentation: https://docs.thedataenginex.org
- Release notes: `CHANGELOG.md`

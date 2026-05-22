# DEX — Data + ML + AI Framework

[![CI](https://github.com/TheDataEngineX/DEX/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/TheDataEngineX/DEX/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dataenginex)](https://pypi.org/project/dataenginex/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Unified Data + ML + AI **library**. One `dex.yaml` defines your entire project — from data ingestion through ML training to AI agents. Self-hosted, config-driven, production-ready.

`dataenginex` is a **pure Python library**. It has no HTTP server. Your application owns the server layer.

______________________________________________________________________

## Quick Start

```bash
pip install dataenginex
```

```python
from dataenginex.engine import DexEngine

engine = DexEngine("dex.yaml")          # loads config, inits DuckDB store
engine.run_pipeline("clean_users")      # execute a pipeline
models = engine.model_registry.list_models()
```

```bash
# Development
git clone https://github.com/TheDataEngineX/DEX && cd DEX
uv run poe check-all          # lint + typecheck + tests
dex validate dex.yaml         # validate a config file
dex version                   # show version + environment
```

______________________________________________________________________

## What It Does

```
dex.yaml
  ├── data:           CSV/Parquet/DuckDB → transforms → quality checks
  ├── ml:             Experiment tracking → training → serving → drift detection
  ├── ai:             LLM providers → retrieval (BM25/dense/hybrid) → agents
  └── observability:  structlog + Prometheus metrics
```

**Opinionated defaults, swappable backends.** Everything works out of the box with
built-in implementations. Swap any layer for industry tools via optional extras:

```bash
pip install "dataenginex[cloud]"          # S3 + GCS storage backends
pip install "dataenginex[observability]"  # Langfuse LLM tracing
```

______________________________________________________________________

## Project Structure

```
dataenginex/
├── src/dataenginex/
│   ├── cli/                # dex CLI (validate, version, init)
│   ├── config/             # dex.yaml schema, loader, env var resolution
│   ├── core/               # Exceptions, interfaces (Base* ABCs), registry
│   ├── engine.py           # DexEngine — single entry point for applications
│   ├── store.py            # DexStore — DuckDB-backed persistence (.dex/store.duckdb)
│   ├── api/                # HTTP helpers: error types, response models (no server)
│   ├── data/               # Connectors, schema registry, profiler, pipeline runner
│   ├── ml/                 # Classical ML: training, registry, serving, drift
│   ├── ai/                 # LLM providers, agents, RAG, vectorstore, observability
│   ├── orchestration/      # DriftScheduler, background workers
│   ├── middleware/         # structlog config, Prometheus metrics (library use)
│   ├── lakehouse/          # Catalog, partitioning, storage backends
│   ├── warehouse/          # SQL transforms, lineage
│   └── plugins/            # Plugin system (entry-point discovery)
│
├── examples/               # Runnable examples + dex.yaml templates
├── tests/                  # Unit + integration tests
├── docs/                   # MkDocs documentation
└── pyproject.toml          # Package config (version source of truth)
```

______________________________________________________________________

## Architecture

```
dex.yaml → DexEngine.__init__
               │
               ├── config/   load + validate → DexConfig
               ├── store/    DexStore (.dex/store.duckdb)
               ├── data/     register sources + pipelines
               ├── ml/       model registry + serving
               └── ai/       LLM providers + agents
```

**Backend Registry Pattern:** Every subsystem has a `Base*` ABC + `BackendRegistry`.
Built-in backends work out of the box. Extras implement the same interface.

**Tech Stack:**

| Layer | Built-in | Optional Extra |
|-------|----------|----------------|
| Data Engine | DuckDB | PySpark |
| Orchestration | croniter scheduler | Dagster |
| ML Tracking | JSON-based tracker | MLflow |
| Model Serving | Built-in predictor | — |
| LLM | Ollama / LiteLLM / vLLM | Any OpenAI-compatible |
| Vector Store | DuckDB VSS | Qdrant |
| Retrieval | BM25 + Dense + Hybrid | — |
| Persistence | DuckDB (`.dex/store.duckdb`) | — |
| Logging | structlog | — |

______________________________________________________________________

## Development

See [docs/development.md](docs/development.md) for full setup.

```bash
uv run poe check-all         # lint + typecheck + tests
uv run poe lint-fix          # auto-fix lint issues
uv run poe test-cov          # tests + coverage report
```

______________________________________________________________________

## Documentation

| Guide | Description |
|-------|-------------|
| [Quickstart](docs/quickstart.md) | Get running in 5 minutes |
| [Architecture](docs/architecture.md) | System design and patterns |
| [Development](docs/development.md) | Local setup and workflow |
| [API Reference](docs/api-reference/index.md) | Auto-generated module docs |

> Docs: [docs.thedataenginex.org](https://docs.thedataenginex.org)

______________________________________________________________________

## The DEX Ecosystem

```
TheDataEngineX/
├── dataenginex    — Core library (this repo, PyPI)
├── dex-studio     — Web UI (FastAPI + Jinja2) — single pane of glass
└── infradex       — Terraform + Helm + K3s deployment
```

dex-studio imports `dataenginex` directly — no HTTP server required.

______________________________________________________________________

## License

MIT License. See [LICENSE](LICENSE).

______________________________________________________________________

**Version**: [![PyPI](https://img.shields.io/pypi/v/dataenginex)](https://pypi.org/project/dataenginex/) | **License**: MIT | **Python**: 3.13+

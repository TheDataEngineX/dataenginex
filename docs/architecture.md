# DataEngineX Architecture

## Overview

**DataEngineX** is a unified Data + ML + AI **library** that wires industry tools through a
single config-driven interface. One `dex.yaml` defines the entire project.

**Design principle:** Pure Python library — no HTTP server bundled. Your application (DataEngineX Studio,
your own FastAPI/Flask app, a script) imports `dataenginex` and owns the server layer.

## Architecture

```
dex.yaml
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│                    Config System                         │
│  YAML → env var resolution → Pydantic validation         │
│  Layering: base + overlay (dex.prod.yaml)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    DexEngine                             │
│  Single entry point — loads config, inits backends       │
│  Exposes: run_pipeline, model_registry, agents, store    │
└──────┬──────────────┬──────────────┬────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Data Layer  │ │ ML Layer │ │   AI Layer   │
│              │ │          │ │              │
│ Connectors   │ │ Tracker  │ │ LLM Provider │
│ Transforms   │ │ Training │ │ Retriever    │
│ Quality      │ │ Serving  │ │ Vector Store │
│ Orchestrator │ │ Drift    │ │ Agent Runtime│
│ Feature Store│ │ Metrics  │ │ Memory       │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
        ┌─────────────────────────┐
        │       DexStore          │
        │  DuckDB — .dex/store.   │
        │  duckdb (project-local) │
        │  pipeline_runs · lineage│
        │  model_artifacts · etc. │
        └─────────────────────────┘
```

## Core Patterns

### Backend Registry

Every subsystem follows the same pattern:

1. **ABC** in `core/interfaces.py` — defines the contract (e.g. `BaseConnector`)
1. **BackendRegistry[T]** in `core/registry.py` — discovers and registers implementations
1. **Built-in** implements the ABC with zero external deps
1. **Extras** implement the same ABC, swapped in via config

```python
from dataenginex.core.registry import BackendRegistry
from dataenginex.core.interfaces import BaseConnector

connector_registry: BackendRegistry[BaseConnector] = BackendRegistry("connector")

@connector_registry.decorator("csv")
class CsvConnector(BaseConnector):
    ...
```

### DexEngine — Application Entry Point

`DexEngine` is the single object applications instantiate. It:

- Loads and validates `dex.yaml`
- Initialises `DexStore` (creates `.dex/store.duckdb` next to the config file)
- Registers data sources, pipelines, ML trackers, AI providers, agents
- Exposes domain methods: `run_pipeline`, `source_schema`, `warehouse_layers`, etc.

```python
from dataenginex.engine import DexEngine

engine = DexEngine("dex.yaml")
engine.run_pipeline("clean_users")
```

### DexStore — Persistence

Single DuckDB file at `.dex/store.duckdb` (project-local, next to `dex.yaml`).
Tables: `pipeline_runs`, `lineage_events`, `model_artifacts`, `quality_runs`,
`audit_log`, `ai_memory`, `ai_episodes`, `catalog_entries`.

### Config System

- Single `dex.yaml` → Pydantic validation → typed `DexConfig`
- Env var interpolation: `${VAR:-default}`
- Overlay layering: `dex.yaml` + `dex.prod.yaml`
- Cross-reference validation (pipeline sources, dependencies)
- Only `project.name` is required; everything else has defaults

### Exception Hierarchy

```
DataEngineXError
├── ConfigError → ConfigValidationError
├── PipelineError → PipelineStepError
├── RegistryError
└── BackendNotInstalledError
```

## Module Map

| Module | Purpose |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `engine.py` | `DexEngine` — application entry point |
| `store.py` | `DexStore` — DuckDB persistence layer |
| `config/` | Schema, loader, env resolution |
| `core/` | ABCs, registry, exceptions |
| `cli/` | `dex` CLI (validate, version, init) |
| `api/` | HTTP helpers: error types, response models |
| `data/connectors/` | Built-in connectors: CSV, Parquet, DuckDB, REST, Kafka, **Spark**, **dbt**, **delta**, **postgres**, **qdrant**, **sse**, **http**, **rest** |
| `data/pipeline/` | Pipeline runner, transforms, quality, profiler |
| `ml/` | Classical ML: training, registry, serving, drift, **feature engines**, **mlflow registry** |
| `ai/` | LLM, agents, RAG, vectorstore, memory, observability |
| `orchestration/` | DriftScheduler, background tasks |
| `middleware/` | structlog config, Prometheus metrics |
| `lakehouse/` | Storage backends, catalog, partitioning |
| `warehouse/` | SQL transforms, lineage |
| `secops/` | **PrivacyGuard** — PII detection, masking strategies, outbound-call audit |
| `plugins/` | Entry-point discovery |

## Tech Stack

| Component | Built-in | Extra |
| ----------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Data Engine | DuckDB | PySpark / dbt CLI (`[data]`) |
| Orchestration | croniter scheduler | — |
| ML Tracking | JSON-based | MLflow (`[tracking]`) |
| Model Serving | Built-in predictor | — |
| LLM Provider | Ollama / vLLM | LiteLLM (install separately) |
| Vector Store | DuckDB VSS | Qdrant (`[qdrant]`) |
| Retrieval | BM25 + Dense + Hybrid | — |
| Persistence | DuckDB | S3/GCS/BigQuery (`[cloud]`) |
| Logging | structlog | — |
| Config | Pydantic + YAML | — |
| CLI | Click | — |
| Privacy / Audit | PrivacyGuard — PII masking + audit | — |
| LLM Observability | — | Langfuse (`[observability]`) |
| Cloud Storage | — | S3/GCS/BigQuery (`[cloud]`) |
| Connectors | CSV, Parquet, DuckDB, SSE, HTTP (REST, SSE), JSON | Spark, dbt, Delta Lake (`[delta]`), PostgreSQL (`[postgres]`), Qdrant (`[qdrant]`) |
| ML | Basic | PyTorch (`[pytorch]`), scikit-learn (`[ml]`), sentence-transformers (`[ml]`), MLflow (`[ml]` + `[tracking]`) |

## Coverage Strategy

**Current Coverage**: 81% (meets 80% threshold)

**Why Coverage is Not 100%**: Optional dependency files are excluded from coverage to keep CI fast. Tests for these run only when the optional extras are installed.

```python
omit = [
    # Network & async connectors (require external deps)
    "*/src/dataenginex/data/connectors/http.py",
    "*/src/dataenginex/data/connectors/rest.py",
    "*/src/dataenginex/data/connectors/sse.py",

    # ML dependencies (require training packages)
    "*/src/dataenginex/ml/mlflow_registry.py",

    # Optional data connectors (require cloud tools)
    "*/src/dataenginex/data/connectors/delta.py",
    "*/src/dataenginex/data/connectors/postgres.py",  # Note: this may not exist, but if it does

    # Other excluded (from pyproject.toml)
    "*/src/dataenginex/data/connectors/delta.py",
    "*/src/dataenginex/lakehouse/storage.py",
    "*/src/dataenginex/worker.py",
]
```

**To install optional dependencies and achieve >90% coverage**:

```bash
uv run poe uv-sync
pip install "dataenginex[cloud]" "dataenginex[delta]" "dataenginex[postgres]" \
  "dataenginex[qdrant]" "dataenginex[queue]" "dataenginex[pytorch]" \
  "dataenginex[notebook]" "dataenginex[ml]" "dataenginex[tracking]" "dataenginex[data]"
uv run poe uv-sync
uv run poe test-cov
```

## Key Design Decisions

| ID | Decision | Rationale |
| ---- | ---------------------------------------------- | ------------------------------------------------------------- |
| AD1 | Pure library — no bundled HTTP server | Applications own the server layer; library stays lean |
| AD2 | DexEngine as single entry point | One object to instantiate; hides wiring complexity |
| AD3 | DuckDB for persistence | Embedded, zero-ops, single file next to dex.yaml |
| AD4 | structlog only | One logging standard across the entire codebase |
| AD5 | LiteLLM install separately | It pins `python-dotenv==1.0.1` which conflicts |
| AD6 | Embeddings require explicit opt-in | sentence-transformers + ONNX are 500 MB+; never auto-download |
| AD7 | Project isolation via separate DuckDB files | Each project's `.dex/store.duckdb` is self-contained |
| AD8 | Python 3.13+ | Full type parameter syntax, improved error messages |
| AD9 | `ai/` for LLM/agents, `ml/` for classical ML | Clear domain separation |
| AD10 | PrivacyGuard intercepts all outbound LLM calls | PII never leaves disk unmasked; audit trail is immutable |

## Ecosystem

```
TheDataEngineX/
├── dataenginex    — Core library (PyPI: dataenginex)
├── dex-studio     — Web UI (FastAPI + Jinja2) — single pane of glass
└── infradex       — Terraform + Helm + K3s deployment
```

- **Container images:** `ghcr.io/thedataenginex/dex`
- **Docs:** `docs.thedataenginex.org`

# DataEngineX Architecture

## Overview

**DataEngineX** is a unified Data + ML + AI framework that orchestrates industry tools through a single config-driven interface. One `dex.yaml` defines the entire pipeline.

**Design principle:** Opinionated defaults that work out of the box. Swap any layer for industry tools via extras.

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
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Data Layer  │ │ ML Layer │ │   AI Layer   │
│              │ │          │ │              │
│ Connectors   │ │ Tracker  │ │ LLM Provider │
│ Transforms   │ │ Training │ │ Retriever    │
│ Quality      │ │ Serving  │ │ Vector Store │
│ Orchestrator │ │ Drift    │ │ Agent Runtime│
│ Feature Store│ │          │ │              │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
        ┌─────────────────────────┐
        │    Backend Registry     │
        │  Base* ABC + registry   │
        │  Built-in or extras     │
        └─────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Built-in       [dagster]     [mlflow]
   (DuckDB,       (Dagster      (MLflow
    croniter,      orchestration) tracking)
    JSON tracker)
```

## Core Patterns

### Backend Registry

Every subsystem follows the same pattern:

1. **ABC** in `core/interfaces.py` — defines the contract (e.g. `BaseConnector`)
2. **BackendRegistry[T]** in `core/registry.py` — discovers and registers implementations
3. **Built-in** implements the ABC with zero external deps
4. **Extras** implement the same ABC, swapped in via config

```python
from dataenginex.core.registry import BackendRegistry
from dataenginex.core.interfaces import BaseConnector

connector_registry: BackendRegistry[BaseConnector] = BackendRegistry("connector")

@connector_registry.decorator("csv")
class CsvConnector(BaseConnector):
    ...
```

### Config System

- Single `dex.yaml` → Pydantic validation → typed `DexConfig` object
- Env var interpolation: `${VAR:-default}`
- Overlay layering: `dex.yaml` + `dex.prod.yaml`
- Cross-reference validation (pipeline sources, dependencies)
- Only `project.name` is required; everything else has defaults

### Exception Hierarchy

All framework exceptions inherit from `DataEngineXError`:

```
DataEngineXError
├── ConfigError → ConfigValidationError
├── PipelineError → PipelineStepError
├── RegistryError
├── BackendNotInstalledError
├── TrainingError
├── ServingError
└── AgentError → LLMProviderError
```

## Tech Stack

| Component | Built-in | Extra |
|-----------|----------|-------|
| Data Engine | DuckDB | PySpark (`[spark]`) |
| Orchestration | croniter scheduler | Dagster (`[dagster]`) |
| ML Tracking | JSON-based | MLflow (`[mlflow]`) |
| Model Serving | Built-in HTTP | BentoML (`[serving]`) |
| LLM Provider | Ollama / LiteLLM | Any OpenAI-compatible |
| Vector Store | DuckDB VSS | Qdrant, LanceDB (`[vectors]`) |
| Retrieval | BM25 + Dense + Hybrid | ColBERT (`[colbert]`) |
| Embeddings | — (requires opt-in) | sentence-transformers (`[embeddings]`) |
| Feature Store | DuckDB-based | Feast (`[feast]`) |
| API Framework | FastAPI + Uvicorn | — |
| Logging | structlog | — |
| Config | Pydantic + YAML | — |
| CLI | Click + Rich | — |

## Deployment Tiers

| Tier | Target | Infrastructure |
|------|--------|---------------|
| 1 | Laptop | `pip install dataenginex && dex serve` |
| 2 | VPS | `docker compose up` on Hetzner (~15/mo) |
| 3 | Production | K3s/EKS/GKE with Helm + ArgoCD |

## Ecosystem

```
TheDataEngineX/
├── DEX            — Core framework (PyPI: dataenginex)
├── dex-studio     — Web UI (Reflex) — single pane of glass
└── infradex       — Terraform + Helm + K3s deployment
```

- **Container images:** `ghcr.io/thedataenginex/dex`
- **Docs:** `docs.thedataenginex.org` (Cloudflare Pages)
- **Domain:** `thedataenginex.org`

## Key Design Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| AD1 | FastAPI is core dependency | Required by API, health, metrics — not optional |
| AD2 | structlog only (no loguru) | One logging standard across entire codebase |
| AD3 | DuckDB single-writer via asyncio queue | Serialized writes avoid WAL conflicts |
| AD4 | SQLite for tracker, DuckDB for data | Different access patterns need different engines |
| AD5 | Embeddings require explicit opt-in | sentence-transformers + ONNX are 500MB+; never auto-download |
| AD6 | Project isolation via separate DuckDB files | Each `dex init` project gets its own `.dex/` directory |
| AD7 | Python 3.13+ | 3.13 is minimum supported; full type parameter syntax + improved error messages |
| AD8 | Graceful degradation | Missing extras produce clear error messages, not crashes |

______________________________________________________________________

**Spec:** See `docs/superpowers/specs/2026-03-21-dataenginex-v2-system-redesign.md` for full design.

**Last Updated:** 2026-03-21

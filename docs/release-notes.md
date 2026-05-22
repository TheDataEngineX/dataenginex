# Release Notes

## v1.2.0 — 2026-05-21

### Highlights

- **Pure library architecture** — `dataenginex` is now a pure Python library with no bundled HTTP server. Applications (`dex-studio`, your own FastAPI/Flask app) own the server layer entirely. `DexEngine` is the single entry point; it loads `dex.yaml`, inits `DexStore`, and wires all backends.
- **`DexEngine` as application entry point** — single object instantiation hides all wiring complexity. Replaces the old `dex serve` pattern.
- **`DexStore` persistence** — single DuckDB file at `.dex/store.duckdb` next to `dex.yaml`. Self-contained per project.
- **`auth` extras removed** — `pyjwt`, `ldap3`, and `cryptography` removed from the package. Auth/RBAC lives in application layers (`dex-studio`) only.
- **Module clarification** — `ml/` is classical ML (training, registry, serving, drift); `ai/` is LLM/agents/RAG/vectorstore; `orchestration/` is background scheduling.
- **`*.duckdb` excluded from git** — generated store files are project-local and should not be committed.

### Breaking changes

- `dex serve` CLI command removed. Start your own ASGI app with `uvicorn` instead.
- `dataenginex[auth]` extra removed. Install `pyjwt` / `ldap3` directly in your application if needed.
- `dataenginex.api` no longer contains auth/RBAC/SCIM/LDAP. It now provides HTTP error types and response models only.

### Migration

```python
# Before (old server pattern)
# dex serve --config dex.yaml

# After — own the server layer
from dataenginex.engine import DexEngine
from fastapi import FastAPI
import uvicorn

engine = DexEngine("dex.yaml")
app = FastAPI()

@app.get("/health")
def health():
    return engine.health()

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Verification checklist

1. `uv run poe lint` — Ruff checks clean
1. `uv run poe typecheck` — mypy strict, 0 errors
1. `uv run poe test` — all tests pass
1. `uv run --with fastapi --with uvicorn python examples/02_api_quickstart.py` — server starts, `/health` returns `{"status":"healthy"}`

______________________________________________________________________

## v1.1.1 — 2026-05-07

### Highlights

- **Reflex compatibility** — `rich` fully removed from CLI layer (`cli/main.py`, `cli/run.py`, `cli/train.py`). Output now uses plain `click.echo`. Fixes `ImportError` when running alongside Reflex (which pins `rich<14`).

### Breaking changes

None. CLI output is functionally identical.

### Verification checklist

1. `uv run poe lint` — Ruff checks clean
1. `uv run poe typecheck` — mypy strict, 0 errors
1. `uv run poe test` — 790 passed, 20 skipped

______________________________________________________________________

## v1.1.0 — 2026-05-06

### Highlights

- **Enterprise auth & RBAC** — SCIM provisioning, role-based access, enterprise SSO integration
- **LiteLLM / vLLM routing** — unified LLM gateway with cost tracking and load balancing
- **Langfuse observability** — LLM trace logging, evals, and prompt management
- **LightRAG integration** — graph-based retrieval for hybrid RAG pipelines
- **AI agent memory** — persistent agent memory subsystem with configurable backends
- **Domain metadata layer** — structured domain extraction and plugin system
- **rich removed** — CLI output now uses `click.echo`; rich is no longer a framework dependency

### Breaking changes

None. All new features are additive.

### Verification checklist

1. `uv run poe lint` — Ruff checks clean
1. `uv run poe typecheck` — mypy strict (125 source files, 0 errors)
1. `uv run poe test` — 790 passed, 20 skipped
1. `curl http://localhost:17000/health` — returns `{"status":"healthy"}`

______________________________________________________________________

## v0.5.0 — 2026-03-01

### Highlights

- **Storage abstraction layer** — `list_objects(prefix)` and `exists(path)` on `StorageBackend` ABC with implementations across all 6 backends (Local, BigQuery, JSON, Parquet, S3, GCS). New `get_storage(uri)` factory resolves `s3://`, `gs://`, and local paths automatically (#89)
- **ML serving endpoints** — `POST /api/v1/predict`, `GET /api/v1/models`, `GET /api/v1/models/{name}` with Pydantic request/response models and ML-specific Prometheus metrics for latency, throughput, and in-flight predictions (#92)
- **Drift monitoring scheduler** — `DriftScheduler` runs background drift checks on registered models, publishes PSI scores to Prometheus gauges, and fires alert counters when drift exceeds thresholds. Includes Prometheus alert rules for moderate, severe, spike, and stale drift conditions (#93)
- **Comprehensive docstrings** — Google-style docstrings added across 55+ methods and 9 Pydantic models covering all public APIs (#88)
- **Cloud emulator testing** — Docker Compose stack with LocalStack (S3) and fake-gcs-server (GCS) plus 25 integration tests with auto-detection
- **Infrastructure fixes** — Dockerfile runtime stage now copies the core package; docs workflow uses `--frozen` sync

### Breaking changes

None. All new features are additive.

### Verification checklist

1. `uv run poe lint` — Ruff checks clean
1. `uv run poe typecheck` — mypy strict (40 files, 0 errors)
1. `uv run poe test` — 299 passed, 28 skipped
1. `docker compose build` — multi-stage Dockerfile builds successfully
1. `docker compose -f docker-compose.test.yml up -d` — emulators start healthy

______________________________________________________________________

## v0.4.11 — 2026-02-27

### Highlights

- **Environment-labeled metrics** — Added `environment` label support across HTTP metrics counters/histograms/gauges and middleware emission
- **Aligned alert rules** — Histogram quantile expressions use explicit bucket aggregation by `le` and `environment`
- **CSV-canonical roadmap** — Standardized docs and release prep metadata

______________________________________________________________________

## v1.0.0 — 2026-02-11

### Highlights

- **SLO-aware monitoring**: Alerting rules now track latency, error rates, and saturation per environment, routed through Alertmanager runbooks aligned with the SLO definitions documented in `monitoring/alerts/dataenginex-alerts.yml` and `monitoring/alertmanager.yml`.
- **Environment-labeled metrics**: The Prometheus client now exports all HTTP counters, histograms, and gauges with an `environment` label so dashboards & alerts can differentiate `dev`/`stage`/`prod` workloads without duplicating services.
- **Pyconcepts-facing API**: Added `/api/external-data` (wraps `pyconcepts.external_data.fetch_external_data`) and `/api/insights` (text/event-stream) so downstream runners can consume the helper data + streaming insights from `pyconcepts`.
- **Docs/tests**: `tests/test_main.py` and `tests/test_metrics.py` cover the new endpoints and metrics labels, and the documentation now explains how to validate the new alerts and APIs.

### Verification checklist

1. `uv run poe lint` — Ruff/mypy checks green
1. `uv run pytest -v` — 31 tests including the new endpoints pass
1. `docker compose build` — multi-stage Dockerfile builds

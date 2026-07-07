# CLAUDE.md — DataEngineX (dataenginex)

Brief answers only. No explanations unless asked.
Goal is to save Claude code tokens for lower cost without losing quality.

> Repo-specific context. Workspace-level rules, coding standards, and git conventions are in `../CLAUDE.md`.

## Project Overview

**DataEngineX** — unified Data + ML + AI library. Config-driven, self-hosted, local-first. Pure Python — no bundled HTTP server.

| Package | Location | Purpose |
|---------|----------|---------|
| `dataenginex` | `src/dataenginex/` | Core library — config, registry, CLI, pipelines, ML, AI, PrivacyGuard |

**Stack:** Python 3.13+ · DuckDB · structlog · Pydantic · Click · pyarrow · croniter · httpx · prometheus-client · uv · Ruff · mypy strict · pytest

**Version:** `uv run poe version`

**Domain:** thedataenginex.org | **Org:** github.com/TheDataEngineX

______________________________________________________________________

## Build & Run Commands

```bash
# Quality
uv run poe lint           # Ruff lint
uv run poe lint-fix       # Ruff lint + auto-fix
uv run poe typecheck      # mypy --strict (src/dataenginex/ only)
uv run poe check-all      # lint + typecheck + test

# Test
uv run poe test           # All tests
uv run poe test-unit      # Unit tests only
uv run poe test-integration  # Integration tests only
uv run poe test-cov       # Tests with coverage

# CLI
dex validate dex.yaml     # Validate config file
dex version               # Show version + environment

# Dev
uv run poe dev            # Dev server (uvicorn reload, port 17000) — for examples/API testing only (dataenginex has no built-in HTTP server)

# Deps
uv run poe uv-sync        # Sync deps from lockfile
uv run poe uv-lock        # Regenerate lockfile
uv run poe security       # Audit deps for vulnerabilities
```

## Optional Extras

```bash
pip install "dataenginex[cloud]"        # S3, GCS, BigQuery connectors
pip install "dataenginex[postgres]"     # asyncpg for Postgres lineage
pip install "dataenginex[qdrant]"       # Qdrant vector store
pip install "dataenginex[queue]"        # arq background jobs
pip install "dataenginex[delta]"        # Delta Lake connector
pip install "dataenginex[pytorch]"      # PyTorch ML
pip install 'litellm>=1.83.3' --no-deps # LLM routing (separate: pins python-dotenv)

# Kafka, RabbitMQ, Elasticsearch, GraphQL, SQLAlchemy are in the base install (no extra needed).
```

______________________________________________________________________

## Validation

After any code change run: `uv run poe check-all` (lint + typecheck + test).
Tests passing ≠ app working — run `dex validate dex.yaml` to verify config.

## TMDB Data-Intelligence Re-Architecture (2026-07-06)

**Core vs custom boundary:** moviedex-specific logic (TMDB connector, Kafka topics, RabbitMQ handlers, ES mappings, GraphQL resolvers) stays in the moviedex project's own `plugins/` dir — never added to dataenginex. Only genuinely reusable capability (new connector types, transform types, generic backends/ABCs) goes in core.

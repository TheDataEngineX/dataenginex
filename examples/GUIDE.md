# DataEngineX Examples

Runnable examples demonstrating key features of the `dataenginex` framework.

## Quick Start

```bash
# Install the package (from repo root)
uv sync

# Run an example
uv run python examples/01_hello_pipeline.py
uv run python examples/02_api_quickstart.py
uv run python examples/03_quality_gate.py
uv run python examples/04_ml_training.py
uv run python examples/05_rag_demo.py
uv run python examples/06_llm_quickstart.py

# PySpark examples (require Java + PySpark)
uv sync --group data
uv run python examples/07_api_ingestion.py
uv run python examples/08_spark_ml.py
uv run python examples/09_feature_engineering.py
uv run python examples/10_model_analysis.py

# Dashboard (requires streamlit)
uv sync --group dashboard
streamlit run examples/dashboard/run_dashboard.py
```

## Template Projects

Full end-to-end templates showing all platform features together.

- **MovieDex** — Real IMDB + Wikidata data (no API keys). Data + ML + AI: pipelines, quality,
  lineage, rating prediction, drift, RAG, two agents.
  `uv run python examples/movie-dex/run_all.py`

- **ShopMetrics** — Synthetic e-commerce. Customer churn ML, product RAG, medallion architecture.
  `uv run python examples/ecommerce/run_all.py`

Refresh live MovieDex data:

```bash
uv run python examples/movie-dex/scripts/fetch_data.py
```

---

## Examples

| # | File | Description |
|---|------|-------------|
| 1 | `01_hello_pipeline.py` | Minimal pipeline: profiler + medallion config (e-commerce orders) |
| 2 | `02_api_quickstart.py` | Launch FastAPI app with health checks & endpoints |
| 3 | `03_quality_gate.py` | Quality checks with QualityGate & QualityStore (product inventory) |
| 4 | `04_ml_training.py` | Train, register, and evaluate a model (customer churn) |
| 5 | `05_rag_demo.py` | RAG pipeline: ingest docs, query vector store, generate with LLM |
| 6 | `06_llm_quickstart.py` | LLM providers: mock, Ollama, OpenAI-compatible, factory function |
| 7 | `07_api_ingestion.py` | HTTP API ingestion with Bronze → Silver → Gold medallion pipeline |
| 8 | `08_spark_ml.py` | PySpark feature engineering + RandomForest training via ModelRegistry |
| 9 | `09_feature_engineering.py` | Time, lag, rolling window, and interaction feature construction |
| 10 | `10_model_analysis.py` | Drift detection (PSI) + prediction error analysis by city/hour/condition |
| — | `dashboard/run_dashboard.py` | Streamlit dashboard with pipeline status, quality scores, model drift panels |

## Prerequisites

- Python ≥ 3.13
- `uv` installed (`pip install uv`)
- For ML examples (01–06): `uv sync` (scikit-learn included via dev deps)
- For PySpark examples (07–10): `uv sync --group data` + Java runtime (set `JAVA_HOME`)

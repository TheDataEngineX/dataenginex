# Observability: Metrics, Logging & Tracing

**Library-level observability for `dataenginex`.** For application-level monitoring (HTTP middleware, health endpoints, Grafana dashboards), see [dex-studio/docs/observability.md](https://github.com/TheDataEngineX/dex-studio/blob/main/docs/observability.md).

## Logging

`dataenginex` uses `structlog` for structured logging throughout the library. All loggers are configured by the host application (e.g., dex-studio). The library does not configure handlers itself.

### Logging in your application

```python
import structlog
from dataenginex.engine import DexEngine

structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
)
engine = DexEngine("dex.yaml")
```

## Metrics

Prometheus metrics are exposed via `dataenginex.observability.metrics`:

```python
from dataenginex.observability.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    PIPELINE_RUN_DURATION,
)
```

### Available library-level metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `pipeline_run_duration_seconds` | Histogram | Pipeline execution time | pipeline_name, status |
| `model_prediction_latency_seconds` | Histogram | Model inference time | model_name |
| `llm_request_duration_seconds` | Histogram | LLM call time | provider, model |
| `data_connector_rows_read` | Counter | Rows read by source connectors | connector_type |

## Tracing

OpenTelemetry tracing is available via `dataenginex.tracing`:

```python
from dataenginex.tracing import get_tracer

tracer = get_tracer(__name__)

with tracer.start_as_current_span("pipeline_run") as span:
    span.set_attribute("pipeline.name", "ingest")
    engine.run_pipeline("ingest")
```

Enable OTLP export:

```bash
export OTLP_ENDPOINT="http://localhost:4317"
```

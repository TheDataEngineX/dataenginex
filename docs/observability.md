# Observability: Metrics, Logging & Tracing

**Complete guide to monitoring, debugging, and understanding DataEngineX in production.**

> **Quick Links:** [Metrics](#prometheus-metrics) · [Tracing](#opentelemetry-tracing) · [Grafana](#grafana-dashboards) · [Local Testing](#local-testing) · [Troubleshooting](#troubleshooting)

______________________________________________________________________

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prometheus Metrics](#prometheus-metrics)
- [OpenTelemetry Tracing](#opentelemetry-tracing)
- [Grafana Dashboards](#grafana-dashboards)
- [Local Testing](#local-testing)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)
- [Related Documentation](#related-documentation)

______________________________________________________________________

## Overview

DataEngineX implements comprehensive observability using **Prometheus** for metrics, **OpenTelemetry** for distributed tracing, and **Structlog** for structured logging.

## Architecture

```mermaid
flowchart TB
    subgraph client["Client"]
        Browser["Browser/API Client"]
    end

    subgraph app["DataEngineX Application"]
        direction TB
        FastAPI["FastAPI App"]
        LogMW["RequestLoggingMiddleware"]
        MetricsMW["PrometheusMetricsMiddleware"]
        Tracing["OpenTelemetry Instrumentation"]

        FastAPI --> LogMW
        LogMW --> MetricsMW
        MetricsMW --> Tracing
    end

    subgraph observability["Observability Stack"]
        direction LR
        Prometheus["Prometheus<br/>(Metrics)"]
        Jaeger["Jaeger<br/>(Traces)"]
        Logs["Structured Logs<br/>(JSON/Console)"]
    end

    Browser -->|HTTP Request| FastAPI
    FastAPI -->|Response + X-Request-ID| Browser

    MetricsMW -.->|/metrics endpoint| Prometheus
    Tracing -.->|OTLP gRPC :4317| Jaeger
    LogMW -.->|stdout/stderr| Logs

    style FastAPI fill:#e1f5ff
    style LogMW fill:#fff3cd
    style MetricsMW fill:#d4edda
    style Tracing fill:#f8d7da
    style Prometheus fill:#d1ecf1
    style Jaeger fill:#d1ecf1
    style Logs fill:#d1ecf1
```

### Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant LogMW as RequestLoggingMiddleware
    participant MetricsMW as PrometheusMetricsMiddleware
    participant Tracing as OpenTelemetry
    participant App as Application Logic

    Client->>+FastAPI: HTTP GET /
    FastAPI->>+LogMW: Process Request
    Note over LogMW: Generate UUID<br/>Bind context
    LogMW->>LogMW: Log "request_started"

    LogMW->>+MetricsMW: Continue
    Note over MetricsMW: Increment in_flight gauge

    MetricsMW->>+Tracing: Continue
    Note over Tracing: Create span<br/>"GET /"

    Tracing->>+App: Execute endpoint
    App-->>-Tracing: Return response
    Note over Tracing: End span<br/>Export to Jaeger

    Tracing-->>-MetricsMW: Response
    Note over MetricsMW: Record duration histogram<br/>Increment requests counter<br/>Decrement in_flight gauge

    MetricsMW-->>-LogMW: Response
    LogMW->>LogMW: Log "request_completed"
    Note over LogMW: Add X-Request-ID header

    LogMW-->>-FastAPI: Response
    FastAPI-->>-Client: HTTP 200 OK<br/>X-Request-ID: uuid
```

______________________________________________________________________

## Prometheus Metrics

### Available Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `http_requests_total` | Counter | Total HTTP requests | method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request duration | method, endpoint |
| `http_requests_in_flight` | Gauge | Requests currently processing | - |
| `http_exceptions_total` | Counter | Total exceptions | exception_type |

### Metrics Endpoint

Access Prometheus metrics at:

```
GET /metrics
```

**Example output:**

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/",method="GET",status="200"} 1543.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/",le="0.005",method="GET"} 1234.0
http_request_duration_seconds_bucket{endpoint="/",le="0.01",method="GET"} 1456.0
http_request_duration_seconds_sum{endpoint="/",method="GET"} 143.2
http_request_duration_seconds_count{endpoint="/",method="GET"} 1543.0
```

### Prometheus Configuration

Add this scrape config to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'dataenginex'
    scrape_interval: 15s
    static_configs:
      - targets: ['dataenginex:17000']
    metrics_path: '/metrics'
```

If you run the API outside Docker, use `localhost:17000` as the target.

### Grafana Dashboard

**Key Queries:**

1. **Request Rate (RPS)**:

   ```promql
   rate(http_requests_total[5m])
   ```

1. **P95 Latency**:

   ```promql
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   ```

1. **Error Rate**:

   ```promql
   rate(http_requests_total{status=~"5.."}[5m])
   ```

1. **In-Flight Requests**:

   ```promql
   http_requests_in_flight
   ```

### Metrics Collection Flow

```mermaid
flowchart TB
    subgraph request["HTTP Request Lifecycle"]
        Start["Request Arrives"]
        Process["Process Request"]
        End["Response Sent"]
    end

    subgraph metrics["Metrics Updates"]
        InFlight["http_requests_in_flight<br/>+1"]
        Duration["http_request_duration_seconds<br/>observe(duration)"]
        Counter["http_requests_total<br/>+1"]
        Exception["http_exceptions_total<br/>+1 (if error)"]
        InFlightDec["http_requests_in_flight<br/>-1"]
    end

    subgraph prometheus["Prometheus"]
        Scrape["Scrape /metrics<br/>every 15s"]
        Store["Time Series DB"]
        Query["PromQL Queries"]
    end

    Start --> InFlight
    InFlight --> Process
    Process -->|Success| Duration
    Process -->|Error| Exception
    Duration --> Counter
    Exception --> Counter
    Counter --> InFlightDec
    InFlightDec --> End

    Counter -.->|Expose| Scrape
    Scrape --> Store
    Store --> Query

    style request fill:#e1f5ff
    style metrics fill:#d4edda
    style prometheus fill:#d1ecf1
```

______________________________________________________________________

## OpenTelemetry Tracing

### Configuration

#### Environment Variables

```bash
# OTLP Collector endpoint (Jaeger, Tempo, etc.)
# Accepts formats: "localhost:4317" or "http://localhost:4317"
export OTLP_ENDPOINT="http://localhost:4317"

# Enable console trace export for debugging (optional)
export ENABLE_CONSOLE_TRACES="true"
```

### Tracing Flow

```mermaid
flowchart LR
    subgraph app["Application"]
        Request["HTTP Request"]
        Instrumentation["FastAPI<br/>Instrumentation"]
        Span["Span Creation"]
        Export["OTLP Exporter"]
    end

    subgraph collectors["Collectors"]
        OTLP["OTLP Endpoint<br/>:4317"]
        Console["Console Export<br/>(Debug)"]
    end

    subgraph backend["Backend"]
        Jaeger["Jaeger UI<br/>:16686"]
    end

    Request --> Instrumentation
    Instrumentation --> Span
    Span -->|Attributes:<br/>method, path,<br/>status, duration| Export
    Export -->|if OTLP_ENDPOINT set| OTLP
    Export -->|if ENABLE_CONSOLE_TRACES| Console
    OTLP --> Jaeger

    style app fill:#e1f5ff
    style collectors fill:#fff3cd
    style backend fill:#d1ecf1
```

### Automatic Instrumentation

FastAPI is automatically instrumented with OpenTelemetry. Every request creates:

- **Span** with request details (method, path, status)
- **Trace ID** for distributed tracing
- **Timing** information

### Manual Instrumentation

Add custom spans to your code:

```python
from dataenginex.tracing import get_tracer

tracer = get_tracer(__name__)

def my_function():
    with tracer.start_as_current_span("database_query") as span:
        span.set_attribute("query.table", "users")
        span.set_attribute("query.limit", 100)
        # ... do database work ...
        span.set_attribute("query.results", 42)
```

### Jaeger Setup

Run Jaeger with OTLP support:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -e SPAN_STORAGE_TYPE=memory \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 14250:14250 \
  jaegertracing/all-in-one:1.60
```

Access Jaeger UI: http://localhost:16686

### Example Trace

```
Trace ID: 7f8a3b2c1d4e5f6a
│
├─ [150ms] GET /api/users
│  ├─ [80ms] database_query (users table)
│  ├─ [30ms] redis_cache_check
│  └─ [40ms] response_serialization
│
Total: 150ms
```

______________________________________________________________________

## Grafana Dashboards

Prebuilt dashboards are available in [infradex/monitoring/grafana](https://github.com/TheDataEngineX/infradex/blob/main/monitoring/grafana/GUIDE.md):

- **DEX Metrics**: request rate, latency, error rate, in-flight.
- **DEX Logs**: log volume, error spikes, recent logs, and request IDs (Loki).
- **DEX Traces**: trace list, top endpoints, and span latency (Tempo/TraceQL).

### Import Steps

1. Open Grafana → **Dashboards** → **New** → **Import**.
1. Upload the JSON from `monitoring/grafana/dashboards/` in the [infradex repo](https://github.com/TheDataEngineX/infradex/tree/main/monitoring/grafana/dashboards).
1. Select Prometheus/Loki/Tempo data sources when prompted.

### Notes

Dashboards assume default labels (e.g., `app=dataenginex`). If your labels differ, edit the dashboard variables and panel queries.

______________________________________________________________________

## Local Testing

### Quick Start

1. **Run the application**:
   ```bash
   ```

uv lock
uv sync
uv run poe api

````

2. **Test metrics endpoint**:
```bash
curl http://localhost:17000/metrics
````

**Expected output:**

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/",method="GET",status="200"} 1.0
...
```

3. **Generate traffic to see metrics**:
   ```bash
   # Make some requests
   curl http://localhost:17000/
   curl http://localhost:17000/health
   ```

curl http://localhost:17000/ready

# Check updated metrics

curl http://localhost:17000/metrics

````

### Local Observability Stack (Prometheus + Grafana + Jaeger)

Use the bundled compose file for one-command local testing:

```bash
docker compose -f docker-compose.yml up -d
````

Then open:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin / admin)
- Jaeger: http://localhost:16686

### Test with Jaeger (Optional)

1. **Start Jaeger locally**:

   ```bash
   docker run -d --name jaeger \
     -e COLLECTOR_OTLP_ENABLED=true \
     -e SPAN_STORAGE_TYPE=memory \
     -p 16686:16686 \
     -p 4317:4317 \
     -p 4318:4318 \
     -p 14250:14250 \
     jaegertracing/all-in-one:1.60
   ```

1. **Run application with tracing**:

   ```bash
   export OTLP_ENDPOINT="http://localhost:4317"
   ```

uv run poe api

````

3. **Generate traces**:
```bash
# Make several requests
for i in {1..10}; do curl http://localhost:17000/; done
````

4. **View traces in Jaeger UI**:
   - Open: http://localhost:16686
   - Select service: "dataenginex"
   - Click "Find Traces"

### Test Console Traces (No Jaeger Required)

Enable console trace export to see traces in logs:

```bash
export ENABLE_CONSOLE_TRACES="true"
uv run poe api
```

Make a request and check console output:

```bash
curl http://localhost:17000/
```

**Console output:**

```json
{
  "name": "GET /",
  "context": {
    "trace_id": "0x7f8a3b2c1d4e5f6a...",
    "span_id": "0x1234567890abcdef"
  },
  "kind": "SpanKind.SERVER",
  "parent_id": null,
  "start_time": "2026-02-05T10:30:00.000000Z",
  "end_time": "2026-02-05T10:30:00.150000Z",
  "status": {
    "status_code": "UNSET"
  },
  "attributes": {
    "http.method": "GET",
    "http.route": "/",
    "http.status_code": 200
  }
}
```

### Run Tests

Verify metrics and tracing implementation:

```bash
# Run observability tests
uv run poe test

# Run all tests with coverage
uv run poe test-cov
```

**Expected:**

- 23 tests passing
- Coverage >90%

______________________________________________________________________

## Integration Examples

### Docker Compose

```yaml
version: '3.8'

services:
  dataenginex:
    build: .
    ports:
      - "17000:17000"
    environment:
      - LOG_LEVEL=INFO
      - OTLP_ENDPOINT=http://tempo:4317

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"

  tempo:
    image: grafana/tempo:2.4.0
    ports:
      - "3200:3200"   # query
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

> Full monitoring stack (Prometheus, Loki, Tempo, Grafana, Alertmanager) is defined in
> [infradex/docker-compose.monitoring.yml](https://github.com/TheDataEngineX/infradex/blob/main/docker-compose.monitoring.yml).
> Run it from the infradex repo: `docker compose -f docker-compose.monitoring.yml up -d`

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: dataenginex
  labels:
    app: dataenginex
spec:
  ports:
    - port: 17000
      name: http
  selector:
    app: dataenginex

---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dataenginex
spec:
  selector:
    matchLabels:
      app: dataenginex
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

______________________________________________________________________

## Alerts

### Prometheus alert rules (SLO-aligned)

The actual rule definitions live in [`infradex/monitoring/alerts/dataenginex-alerts.yml`](https://github.com/TheDataEngineX/infradex/blob/main/monitoring/alerts/dataenginex-alerts.yml). They expose three alerts—latency, error rate, and saturation—scoped to prod. Every alert annotation links to the [deployment runbook](https://github.com/TheDataEngineX/dataenginex/blob/main/docs/DEPLOY_RUNBOOK.md).

| Alert | Environment | Threshold | Severity | Receiver |
|-------|-------------|-----------|----------|----------|
| `DataEngineXLatencyHigh` | prod | P95 latency > 0.75s (5m window) | `page` | critical slack (#dex-alerts) |
| | stage | P95 latency > 1.0s | `page` | same |
| | dev | P95 latency > 1.5s | `warning` | email (ops alias) |
| `DataEngineXErrorRateHigh` | prod | 5xx fraction > 1% | `page` | critical slack |
| | stage | 5xx fraction > 3% | `page` | critical slack |
| | dev | 5xx fraction > 5% | `warning` | email |
| `DataEngineXSaturationHigh` | prod | In-flight > 25 | `page` | critical slack |
| | stage | In-flight > 15 | `warning` | email |
| | dev | In-flight > 10 | `warning` | email |

The production `alertmanager` configuration in [`infradex/monitoring/alertmanager.yml`](https://github.com/TheDataEngineX/infradex/blob/main/monitoring/alertmanager.yml) routes all `severity=page` alerts to a Slack webhook (`#dex-alerts`) while `severity=warning` alerts go to the ops email alias. Alerts sharing the same `alertname` are deduplicated via inhibit rules so warnings do not trigger when a page is active.

### Reloading Alert Rules

Whenever the alert rules or Alertmanager config changes, reapply the manifests so Prometheus and Alertmanager scrape the latest thresholds. Reload the rules in the following order to avoid gaps:

1. Reapply the Prometheus rule set managed in GitOps (from infradex repo):

```bash
kubectl apply -f https://raw.githubusercontent.com/TheDataEngineX/infradex/main/monitoring/alerts/dataenginex-alerts.yml
kubectl rollout restart deployment/prometheus
```

2. Reconfigure Alertmanager so receivers and runbooks stay up to date:

```bash
kubectl apply -f https://raw.githubusercontent.com/TheDataEngineX/infradex/main/monitoring/alertmanager.yml
kubectl rollout restart deployment/alertmanager
```

3. Verify the alerts appear in Alertmanager UI and reference the release runbook described in [`docs/DEPLOY_RUNBOOK.md`](https://github.com/TheDataEngineX/dataenginex/blob/main/docs/DEPLOY_RUNBOOK.md).

If you manage the stack via ArgoCD, push the changes to the kustomize overlay and let ArgoCD sync the deployments automatically rather than running the commands above manually.

### Proof-of-concept API endpoints

These endpoints surface the modules under `src/pyconcepts` so that you can explore how the application mixes external data and streaming insights.

1. **External data** — `GET /api/external-data?currency=USD`

   - Uses `pyconcepts.external_data.fetch_external_data` to call the Coindesk API and return the latest BTC rate for the requested currency.
   - Returns a JSON object with `symbol`, `currency`, `value`, `timestamp`, and `source` fields.
   - Example: `curl "http://localhost:17000/api/external-data?currency=eur"`

1. **Streaming insights** — `GET /api/insights?count=5&interval=0.75`

   - Streams conservative synthetic metrics via Server-Sent Events (`text/event-stream`).
   - Honors `count` (1–20) and `interval` seconds per event to throttle data for demos.
   - Consume it with `curl -N http://localhost:17000/api/insights` and parse each `data: {...}` chunk as JSON.

______________________________________________________________________

## Best Practices

### Metrics

1. **Use labels wisely**: Keep cardinality low (< 1000 unique label combinations)
1. **Histogram buckets**: Adjust buckets based on your latency distribution
1. **Counter vs Gauge**: Use counters for totals, gauges for current values
1. **Naming**: Follow Prometheus naming conventions (`_total`, `_seconds`)

### Tracing

1. **Sampling**: In high-traffic scenarios, sample traces (e.g., 1% of requests)
1. **Span attributes**: Add relevant context but avoid PII
1. **Error tracking**: Mark spans with errors using `span.set_status()`
1. **Span naming**: Use consistent, hierarchical names

### Performance

- Metrics collection: ~0.1ms overhead per request
- Tracing overhead: ~1-2ms per request (depends on sampling)
- `/metrics` endpoint: Excluded from metrics to avoid recursion

______________________________________________________________________

## Health Checks

DEX provides three health endpoints for Kubernetes probes:

- **/health** (liveness) — returns component status and overall health
- **/ready** (readiness) — returns readiness based on dependency checks
- **/startup** (startup) — indicates app initialization completion

### Configure Dependency Checks

Set these environment variables to enable component checks:

```bash
export DEX_DB_HOST="db"
export DEX_DB_PORT="5432"

export DEX_CACHE_HOST="redis"
export DEX_CACHE_PORT="6379"

export DEX_EXTERNAL_API_URL="https://api.example.com/health"
```

If a component is not configured, it will show **skipped** in the response.

______________________________________________________________________

## Troubleshooting

### Metrics not appearing

1. Check `/metrics` endpoint is accessible
1. Verify Prometheus can scrape the endpoint
1. Check Prometheus targets: http://localhost:9090/targets

### Service not appearing in Jaeger UI

**Troubleshooting steps:**

1. **Verify Jaeger is running**:

   ```bash
   docker ps | grep jaeger
   ```

1. **Check OTLP_ENDPOINT is set**:

```bash
echo $OTLP_ENDPOINT
```

Should output: `http://localhost:4317`

3. **Generate traffic** - Jaeger only shows services that have sent traces:
   ```bash
   # Make several requests
   curl http://localhost:17000/
   curl http://localhost:17000/health
   ```

curl http://localhost:17000/ready

````

4. **Verify service name** - Check application logs on startup:
```json
{
  "event": "application_started",
  "service.name": "dataenginex"
}
````

5. **Check Jaeger received traces**:

   - Open Jaeger UI: http://localhost:16686
   - Click the "Service" dropdown
   - Look for "dataenginex" (matches APP_NAME env var)
   - If not visible, select time range "Last Hour" and click "Find Traces"

1. **Check for export errors** in application output:

   ```
   StatusCode.UNAVAILABLE - Jaeger not reachable
   StatusCode.INVALID_ARGUMENT - Configuration error
   ```

1. **Enable console traces for debugging**:

   ```bash
   export ENABLE_CONSOLE_TRACES="true"
   # Restart app - you'll see spans printed to console
   ```

1. **Verify port 4317 is accessible**:

   ```bash
   # Check if Jaeger is listening on OTLP port
   netstat -an | grep 4317
   # or
   curl -v telnet://localhost:4317
   ```

### High memory usage

1. Reduce trace sampling rate
1. Check for metric label cardinality explosion
1. Monitor `/metrics` response size

______________________________________________________________________

## Testing

Run observability tests:

```bash
uv run poe test
```

______________________________________________________________________

## Related Documentation

**Deployment & Operations:**

- **[CI/CD Pipeline](ci-cd.md)** - Automated deployments
- **Deployment Runbook** (in `infradex` repo) - Deploy procedures
- **Local K8s Setup** (in `infradex` repo) - Kubernetes setup

**Development:**

- **[SDLC](sdlc.md)** - Development workflow
- **[Contributing](contributing.md)** - Contribution guide

______________________________________________________________________

**[← Back to Documentation](index.md)**

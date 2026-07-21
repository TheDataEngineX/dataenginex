# dataenginex.data

Data connectors, pipeline execution, quality checks, transforms, profiling, and the connector registry.

## Quick import

```python
from dataenginex.data import (
    CsvConnector, DuckDBConnector, ParquetConnector,
    RestApiConnector, HttpConnector, SseConnector,
    DbtConnector, DeltaConnector, SparkConnector,
    connector_registry,
    DataProfiler,
    PipelineRunner,
)
```

______________________________________________________________________

## Connectors

### CsvConnector

`dataenginex.data.connectors.csv`

Read CSV files into Arrow/DuckDB tables with schema inference and column mapping.

::: dataenginex.data.connectors.csv

```python
from dataenginex.data.connectors.csv import CsvConnector

conn = CsvConnector(path="data/events.csv", delimiter=",", has_header=True)
df = conn.fetch()
```

______________________________________________________________________

### DuckDBConnector

`dataenginex.data.connectors.duckdb`

Execute SQL queries against local DuckDB databases or in-memory relations.

::: dataenginex.data.connectors.duckdb

```python
from dataenginex.data.connectors.duckdb import DuckDBConnector

# database can be a real DuckDB file or ":memory:" — NOT .dex/store.duckdb,
# which is dataenginex's own SQLite (WAL) metadata store despite the filename
conn = DuckDBConnector(database="data/warehouse.duckdb")
conn.connect()
rows = conn.read(table="events")
```

______________________________________________________________________

### ParquetConnector

`dataenginex.data.connectors.parquet`

Read Parquet files (local or remote) with optional predicate pushdown.

::: dataenginex.data.connectors.parquet

```python
from dataenginex.data.connectors.parquet import ParquetConnector

conn = ParquetConnector(path="data/silver/events/*.parquet", filters=[("year", "=", 2024)])
df = conn.fetch()
```

______________________________________________________________________

### RestApiConnector

`dataenginex.data.connectors.rest`

Paginated REST API connector with retry, auth headers, and response mapping.

::: dataenginex.data.connectors.rest

```python
from dataenginex.data.connectors.rest import RestApiConnector

conn = RestApiConnector(
    url="https://api.example.com/v1/events",
    headers={"Authorization": "Bearer token"},
    params={"page_size": 200},
)
records = conn.fetch()
```

______________________________________________________________________

### HttpConnector

`dataenginex.data.connectors.http`

HTTP file downloader with caching and automatic decompression. Downloads to local DuckDB-queryable cache.

::: dataenginex.data.connectors.http

```python
from dataenginex.data.connectors.http import HttpConnector

conn = HttpConnector(
    url="https://datasets.example.com/data.tsv.gz",
    cache_dir="~/.dex/cache",
    max_age_hours=24,
)
df = conn.fetch()
```

______________________________________________________________________

### SseConnector

`dataenginex.data.connectors.sse`

Server-Sent Events (SSE) streaming connector for real-time data ingestion.

::: dataenginex.data.connectors.sse

```python
from dataenginex.data.connectors.sse import SseConnector

conn = SseConnector(url="https://stream.example.com/events")
for event in conn.stream():
    process(event)
```

______________________________________________________________________

### DbtConnector

`dataenginex.data.connectors.dbt`

Run dbt models and expose results as DEX datasets.

::: dataenginex.data.connectors.dbt

______________________________________________________________________

### DeltaConnector

`dataenginex.data.connectors.delta`

Read Delta Lake tables via `deltalake` (requires `dataenginex[cloud]`).

::: dataenginex.data.connectors.delta

______________________________________________________________________

### SparkConnector

`dataenginex.data.connectors.spark`

PySpark DataFrame connector for large-scale cluster workloads.

::: dataenginex.data.connectors.spark

______________________________________________________________________

## Connector Registry

`dataenginex.data.registry`

Central registry mapping connector names to connector classes. Used by config-driven pipelines.

::: dataenginex.data.registry

```python
from dataenginex.data.registry import connector_registry

# Register custom connector
@connector_registry.decorator("my_source")
class MyConnector(BaseConnector):
    ...

# Look up by name (used internally by PipelineRunner)
cls = connector_registry.get("csv")
```

______________________________________________________________________

## Pipeline

### PipelineRunner

`dataenginex.data.pipeline.runner`

Executes config-defined pipelines step by step, wiring connectors → transforms → storage.

::: dataenginex.data.pipeline.runner

```python
from dataenginex.data.pipeline.runner import PipelineRunner

runner = PipelineRunner(config=engine.config)
result = runner.run("ingest_events")
print(result.rows_written)
```

______________________________________________________________________

### Pipeline DAG

`dataenginex.data.pipeline.dag`

DAG representation of pipeline step dependencies for ordering and parallelism.

::: dataenginex.data.pipeline.dag

______________________________________________________________________

### Run History

`dataenginex.data.pipeline.run_history`

Persists pipeline run metadata (start time, duration, rows, status) to a local JSON file.

::: dataenginex.data.pipeline.run_history

______________________________________________________________________

## Quality

### Quality Gates

`dataenginex.data.quality.gates`

Data-layer quality gate implementations that operate on DataFrames at pipeline boundaries.

::: dataenginex.data.quality.gates

______________________________________________________________________

### Spark Quality

`dataenginex.data.quality.spark`

Quality gate implementations for Spark DataFrames.

::: dataenginex.data.quality.spark

______________________________________________________________________

## Transforms

`dataenginex.data.transforms.sql`

SQL transform executor — runs DuckDB SQL expressions against in-memory DataFrames within a pipeline step.

::: dataenginex.data.transforms.sql

```python
from dataenginex.data.transforms.sql import SqlTransform

t = SqlTransform(query="SELECT user_id, COUNT(*) AS events FROM input GROUP BY 1")
result_df = t.run(df)
```

______________________________________________________________________

## Profiler

`dataenginex.data.profiler`

Column-level statistical profiling — nulls, cardinality, min/max, quantiles, type distribution.

::: dataenginex.data.profiler

```python
from dataenginex.data.profiler import DataProfiler

profiler = DataProfiler()
profile = profiler.profile(df)
for col in profile.columns:
    print(col.name, col.null_pct, col.cardinality)
```

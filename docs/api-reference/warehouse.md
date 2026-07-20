# dataenginex.warehouse

SQL-style transforms and persistent data lineage tracking for warehouse workloads.

## Quick import

```python
from dataenginex.data.transforms import transform_registry
from dataenginex.warehouse.lineage import PersistentLineage, LineageEvent
```

______________________________________________________________________

## Transforms

`dataenginex.data.transforms.sql`

DuckDB SQL-based transforms for pipeline steps (`filter`, `derive`, `cast`, `deduplicate`, `sql`, `rename`, `drop_columns`, `fill_null`, `aggregate`, `window`, `explode`, `json_normalize`). Each transform registers itself into `transform_registry`; the `PipelineRunner` looks transforms up by their config `type` and chains them: `input_table -> transform1 -> transform2 -> ...`.

::: dataenginex.data.transforms.sql

**Key registry:** `transform_registry` (from `dataenginex.data.transforms`)

```python
from dataenginex.data.transforms import transform_registry

# Look up a transform class by its config "type" key
cls = transform_registry.get("aggregate")
transform = cls(group_by=["user_id"], agg_exprs={"events": "COUNT(*)"})
output_table = transform.apply(conn, input_table="silver_events")
```

______________________________________________________________________

## Lineage

`dataenginex.warehouse.lineage`

Column-level and dataset-level data lineage tracking. Records source → transform → destination relationships for audit and impact analysis. `PersistentLineage` persists to a local JSON file; `PostgresLineage` persists to PostgreSQL (falls back to `PersistentLineage` when `asyncpg`/the database is unavailable).

::: dataenginex.warehouse.lineage

**Key classes:** `PersistentLineage`, `PostgresLineage`, `LineageEvent`

```python
from dataenginex.warehouse.lineage import PersistentLineage

lineage = PersistentLineage("data/lineage.json")

ev = lineage.record(
    operation="ingest",
    layer="bronze",
    source="events_api",
    input_count=1250,
    output_count=1250,
)
lineage.record(
    operation="transform",
    layer="silver",
    parent_id=ev.event_id,
    input_count=1250,
    output_count=1200,
    quality_score=0.88,
)

upstream_chain = lineage.get_chain(ev.event_id)
by_pipeline = lineage.get_by_pipeline("clean_users")
```

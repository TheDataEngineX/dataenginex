# dataenginex.lakehouse

Storage backends, data catalog, and partitioning strategies for lakehouse-style architectures.

## Quick import

```python
from dataenginex.lakehouse import (
    ParquetStorage,
    StorageFormat,
    DataCatalog,
    PartitionStrategy,
)
```

______________________________________________________________________

## Storage

`dataenginex.lakehouse.storage`

Pluggable storage backends for reading and writing datasets across local, S3, GCS, and Delta Lake targets. `ParquetStorage` ships by default (falls back to `JsonStorage` when `pyarrow` isn't installed); cloud backends require `dataenginex[cloud]`.

::: dataenginex.lakehouse.storage

**Key classes:** `ParquetStorage`, `JsonStorage`, `StorageFormat`

```python
from dataenginex.lakehouse.storage import ParquetStorage, StorageFormat

storage = ParquetStorage(
    base_path="data/gold",
    compression="zstd",
)
storage.write(records, path="events", format=StorageFormat.PARQUET)
```

______________________________________________________________________

## Catalog

`dataenginex.lakehouse.catalog`

Dataset catalog — registers, discovers, and resolves named datasets to their storage locations. `DataCatalog` is a thin facade over `DexStore`, so it's persisted to SQLite (WAL mode), not a JSON file or DuckDB.

::: dataenginex.lakehouse.catalog

**Key class:** `DataCatalog`

```python
from dataenginex.lakehouse.catalog import DataCatalog, CatalogEntry

# persist_path=... for a dedicated SQLite file, or store=engine.store to
# share the engine's DexStore and avoid a second DB file
catalog = DataCatalog(persist_path=".dex/catalog.db")

catalog.register(CatalogEntry(name="events_gold", layer="gold", format="parquet", location="data/gold/events"))
entry = catalog.get("events_gold")
print(entry.location, entry.record_count)
```

______________________________________________________________________

## Partitioning

`dataenginex.lakehouse.partitioning`

Partition strategy definitions (date-based, hash-based) and helpers for computing partition keys/paths from a record.

::: dataenginex.lakehouse.partitioning

**Key classes:** `PartitionStrategy`, `DatePartitioner`, `HashPartitioner`

```python
from dataenginex.lakehouse.partitioning import HashPartitioner

partitioner = HashPartitioner(fields=["user_id"], n_buckets=16)
path = partitioner.partition_path({"user_id": "u-123"}, base="data/silver/events")
```

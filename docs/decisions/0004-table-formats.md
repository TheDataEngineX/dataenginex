# Decision log

## 0004 - Table formats (ADR-002, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Context: earlier docs assumed Delta Lake as the writable format on
DuckDB. The DuckDB 2.0 delta extension docs say otherwise: CREATE,
append, checkpoints and time travel work, but UPDATE, DELETE,
MERGE INTO and ALTER do not. A medallion with upserts and SCD2
cannot be built on that. DuckDB's Iceberg extension documents
MERGE/UPDATE/DELETE/ALTER, and DuckLake (metadata in a SQL database,
Parquet data files; 1.0 released 2026-04-13) fits the DuckDB-native
path.

Decision: a table-format adapter in Layer 0 with DuckLake as the
default writable format, Iceberg as the interoperable path, and
Delta as read/append-only.

Consequences: medallion upserts and SCD2 run on DuckLake or Iceberg.
The adapter keeps the formats swappable behind one interface.

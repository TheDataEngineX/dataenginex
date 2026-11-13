# Decision log

## 0007 - State store (ADR-005, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Context: dbt's statelessness versus SQLMesh's state and intervals
is the documented lesson. Backfills and idempotent re-runs need
owned state; adding it later is a migration.

Decision: the state store is owned from day one. SQLite locally,
Postgres in cloud, ONE schema: pipeline intervals, snapshots, and
the receipt index.

Consequences: M0 includes the minimal SQLite state store. The cloud
reuses the same schema on Postgres - no second design.

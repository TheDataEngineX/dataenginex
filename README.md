# dataenginex

The data layer foundation for small and medium business data work.

Define your data structures, contracts, and layers in Python. Run them
into a fixed Bronze / Silver / Gold medallion on DuckDB, with contract
checks, quarantine for bad rows, idempotent re-runs, and one receipt
per run.

This package is Layer 0 of the DataEngineX rebuild: the abstract data
layer system. It contains definitions and one local engine. No UI, no
accounts, no cloud, no domain logic. Apps (the dex runtime, the future
cloud service, and domain apps) depend on this package, never the other
way around.

Status: fresh start (2026-10-28). The previous v0.7.0 codebase was
removed in full; this rebuild starts at version 0.0.1. Only what is
listed below exists - nothing else is promised yet.

Exists now:
- Definitions (structures, contracts, pipelines), the DuckDB engine
  with contract gates and quarantine, the state store, receipts, and
  the retail example (M0/M1a)
- Decision log (docs/decisions/)

Next milestone (M0 kernel spike, from the 2026-10-28 design study):
- [x] Structure and Contract definitions (Python-first, Pydantic v2)
- [x] dataenginex check: validate a project without running it
- [x] State store (SQLite: pipeline intervals, snapshots, receipt
      index) - owned from day one (decision 0007)
- [x] Receipt v1 (OpenLineage-shaped superset + cost/quality facets)
- [x] One pipeline run on DuckDB + DuckLake with a run receipt
- [x] Retail golden dataset as the canonical example (examples/retail/)

Gate: Jay builds the retail starter using only the public API
(if he cannot, the API is wrong - decision 0021).

Next milestone (M1 dex local, from the 2026-10-28 design study):
- [x] Contract gates: not-null and unique violations move to
      queryable quarantine tables (M1a)
- [x] Idempotent re-runs: an unchanged definition refuses to re-run
      after success unless forced (M1a)
- [ ] init template with the retail sample data (M1b)
- [ ] Docker image, PyPI releases, old versions yanked (M1c)
- Gate: 3 external users finish the tutorial unaided.

The milestone sequence M0-M5 (PRODUCT_DESIGN) and decisions
0003-0023 live in docs/decisions/.

License: Apache-2.0 (decision 0003).

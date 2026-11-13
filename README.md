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
- Package skeleton, decision log (docs/decisions/)
- Structure and Contract definitions (Python-first, Pydantic v2)

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

The milestone sequence M0-M5 (PRODUCT_DESIGN) and decisions
0003-0023 live in docs/decisions/.

License: Apache-2.0 (decision 0003).

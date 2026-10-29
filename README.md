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

Next milestone (M0 kernel spike):
- Structure and Contract definitions (Python-first, Pydantic v2)
- dex check: validate a project without running it
- One pipeline run on DuckDB + DuckLake with a run receipt

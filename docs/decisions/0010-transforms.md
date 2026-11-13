# Decision log

## 0010 - Transforms (ADR-008, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: transforms are native SQL and Python in v1. No dbt or
SQLMesh compile target until someone actually demands it.

Consequences: transforms live in project definitions and run on the
DuckDB engine. Layer 0 stays dependency-light.

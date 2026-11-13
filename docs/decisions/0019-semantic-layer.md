# Decision log

## 0019 - Semantic layer (ADR-017, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: no semantic or metric layer in v1. Gold stays plain
tables, and must remain OSI-exportable later.

Consequences: no metric-store abstraction in Layer 0. The domain
apps (retail first) own their KPI definitions in Gold.

# Decision log

## 0013 - Tenant isolation (ADR-011, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: the bridge model - a pooled control plane (Postgres with
row-level security) and a siloed data plane: per-tenant bucket (or
bucket prefix with per-tenant scoped credentials), per-tenant
DuckLake catalog, per-job ephemeral compute. Isolation is storage,
credentials and compute - never just a WHERE clause.

Consequences: customer data never enters the control-plane
database; only job specs, schedules and receipts cross.

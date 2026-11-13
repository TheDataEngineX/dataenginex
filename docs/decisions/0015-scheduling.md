# Decision log

## 0015 - Scheduling (ADR-013, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: a Postgres job table plus a small dispatcher we own. No
Airflow, no Temporal, until a NAMED limitation is hit and written
into an ADR amendment.

Consequences: one fewer infrastructure system to operate solo.
Scheduling is a cloud-layer concern (M3+); Layer 0 and the local
runtime do not schedule.

# Decision log

## 0022 - Vertical order (ADR-020, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: retail first, then services businesses (agencies, front
office, trades), then healthcare - and healthcare only through a
non-PHI wedge (operations, scheduling, finance data with no patient
health information). Each vertical is gated by a readiness audit.

Consequences: the retail pilot is the reference implementation
everything else is templated from. Full HIPAA scope waits for
revenue; it breaks the cheap-PaaS cost model.

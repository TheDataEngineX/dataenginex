# Decision log

## 0008 - Receipts (ADR-006, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: receipts are versioned JSON shaped as an OpenLineage
superset (run, job, facets) plus our own facets: rows per layer,
per-rule quality results, definition versions, duration, and cost
fields (zero-filled locally). Files are the record; any database is
only an index over them.

Consequences: receipts are the trust chain for reconciliation,
lineage, and - once the AI services layer exists - citations on
every AI answer (decision 0023). Receipt v1 lands in M0.

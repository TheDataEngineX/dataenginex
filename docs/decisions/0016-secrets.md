# Decision log

## 0016 - Secrets (ADR-014, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: secrets never appear in definitions, receipts, or images.
Jobs get short-lived, tenant-scoped credentials minted per run.

Consequences: Layer 0 models have no secret fields by
construction - anything that needs a credential is a runtime or
cloud concern with its own review.

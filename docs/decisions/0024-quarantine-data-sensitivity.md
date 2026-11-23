# Decision log

## 0024 - Quarantined row sensitivity (proposed)

Status: proposed; requires maintainer review before acceptance.

Context: M1a moves rows that fail contract checks into quarantine tables
and materializes those tables as Parquet files in the local workspace.
These files retain the complete rejected rows, which may be as sensitive
as their source data. Run receipts currently record aggregate quality
results and counts rather than the row values.

Proposal: treat quarantine artifacts as sensitive data with the same
access and retention expectations as their source files. Do not add row
values to receipts or routine diagnostics. Do not describe quarantine as
redacted, encrypted, or automatically deleted unless an implementation
provides that guarantee. Users operating locally remain responsible for
workspace access and cleanup, consistent with decision 0011.

Scope: this proposal describes the local M1a behavior. It does not define
cloud tenant isolation, retention automation, or a redaction feature.
Those require separate design and review.

Review question: should this policy be accepted as written, revised, or
deferred until the cloud execution boundary is designed?

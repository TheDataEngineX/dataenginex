# Decision log

## 0018 - Cloud-only boundary (ADR-016, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: the never-cloud-only list is contractual: definition
parsing, check, local run, receipts, and localhost serve. The cloud
runs the IDENTICAL image at the IDENTICAL foundation pin.

Consequences: any feature that cannot ship in the local image does
not ship at all. Cloud-only things are limited to accounts,
scheduling, secrets vaulting, and the catalog UI.

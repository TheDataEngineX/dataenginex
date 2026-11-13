# Decision log

## 0009 - Ingestion (ADR-007, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: ingestion merge and SCD2 semantics are delegated to dlt's
documented behaviour (_dlt_valid_from/_to), not reinvented. Layer 0
builds no home-built source connectors.

Consequences: dlt's LICENSE file is read before it becomes a core
dependency (standing rule). Sources in v1 are files, per the
file-upload-before-OAuth product order.

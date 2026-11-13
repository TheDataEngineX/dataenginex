# Decision log

## 0006 - Compatibility vocabulary (ADR-004, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: compatibility uses the Avro/Confluent vocabulary:
backward, forward, full, none. Required levels: backward at Silver,
full at Gold. A breaking change means a new major dataset version,
with the old version still readable during migration (the dbt
model-versions pattern). Contracts export to ODCS v3.1.0 (pin 3.1.0;
re-check the Bitol repo before publishing - one validator site
lists a 3.2.0).

Consequences: Contract.compatibility implements the vocabulary
today. Layer-level enforcement arrives with the contracts milestone
(M2). ADR-004 references in the code now point at this file.

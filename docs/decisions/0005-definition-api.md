# Decision log

## 0005 - Definition API (ADR-003, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Context: the research compared Pydantic, Pandera and dataclasses for
definition ergonomics. Pydantic v2 wins. Neither Pandera nor Great
Expectations becomes a hard core dependency.

Decision: definitions are data-shaped Pydantic v2 models, written in
Python first. Data checks are our own small set compiled to DuckDB
SQL, so validation runs where the data is. YAML, JSON and ODCS are
exports only, never inputs.

Consequences: implemented by src/dataenginex/definitions.py
(Structure, Contract, Project, validate_project). Exports (ODCS,
YAML) are additive and do not change the models.

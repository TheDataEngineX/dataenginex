# Decision log

## 0020 - MCP and agents (ADR-018, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: a read-only MCP server over serve in v2. No write tools.
Row limits and receipt citation are required on every answer.

Consequences: this is the data-access surface for the AI services
product (decision 0023). It is the only way dex touches Gold data.

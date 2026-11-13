# Decision log

## 0012 - Distribution (ADR-010, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: container-first - one signed, multi-arch image with the
DuckDB extensions baked in - plus a thin PyPI shim. Native binaries
are deferred with a named trigger (repeated user demand), because
per-OS builds, signing and antivirus false positives are a support
tax a solo founder should not pre-pay.

Amendment (2026-11-12): the CLI command installed by the shim is
`dataenginex`. The name `dex` belongs to the AI assistant product
(decision 0023), so the runtime command cannot claim it.

Consequences: dex-studio ships the `dataenginex` console script.

# Decision log

## 0021 - Domain apps (ADR-019, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: domain apps use public APIs only. A needed private API
is a Layer 0 bug and blocks the app milestone until fixed.

Consequences: the dogfood rule is enforced by the build - shipped
apps install the foundation from PyPI, never from a sibling folder.
The M0 gate (Jay builds the retail starter on the public API only)
is the first enforcement.

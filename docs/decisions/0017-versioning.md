# Decision log

## 0017 - Versioning (ADR-015, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Decision: SemVer, a 12-month support window, a requires-pin in the
project manifest (`requires-data-layer = ">=x.y,<2"`, the
require-dbt-version pattern), and deprecation only after a feature
has been superseded for at least two minor releases.

Consequences: the runtime refuses incompatible projects with a
readable error instead of a traceback. The rebuild's 0.0.1 start
(decision 0001) is compatible; the old PyPI versions are scrapped
before the first rebuild release.

# Decision log

## 0001 - Fresh start (2026-10-28)

Context: the v0.7.0 codebase (403 Python files, 16 core dependencies,
ML/AI/orchestration/secops sprawl) was removed in full at the founder's
direction - overwrite everything, archive nothing. The old tree,
including its git history, sits in the Mac Trash until emptied.

Decisions carried into the rebuild:
- Layered architecture: this package is Layer 0 (foundation). The dex
  runtime (dex-studio repo) is Layer 1 and depends on this package.
  Dependencies point one way only: apps -> runtime -> foundation.
- Fixed medallion (Bronze / Silver / Gold) first. Reversible later.
- Python-first definitions. YAML or other spec formats are parked.
- Table format: DuckLake default (DuckDB cannot MERGE into Delta);
  Iceberg interoperable; Delta read/append only.
- Rebuild versioning starts at 0.0.1 (founder's call, 2026-10-28,
  superseding the 0.8.0 PyPI-continuity idea). If 0.0.1 was ever
  published to PyPI by the old project, the first rebuild release
  takes the next free number at publish time.
- License: MIT for now (continuity with v0.7.0). The research pack
  proposed Apache-2.0 + DCO; confirm before the first rebuild release.
- One milestone at a time. The job hunt and life outrank this project.

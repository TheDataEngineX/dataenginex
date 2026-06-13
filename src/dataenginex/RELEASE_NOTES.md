# dataenginex Release Notes

See [docs/release-notes.md](docs/release-notes.md) for the complete release history.

This document tracks published package releases for `dataenginex` only.
Only include changes that modify files under `src/dataenginex/**`.

## v0.3.5 - 2026-02-20

- Released package version `0.3.5`.
- Tag: `v0.3.5`
- Release title: `Release v0.3.5`
- Changes in this release:
  - Hardened `PyPI Publish` workflow for trusted publishing.
  - Added release-only publish gating and build-only behavior for manual dispatch.
  - Switched publish job environment names to repo vars for stricter workflow validation compatibility.

## v0.3.4 - 2026-02-20

- Released package version `0.3.4`.
- Tag: `v0.3.4`
- Release title: `Release v0.3.4`
- Changes in this release:
  - Repo hygiene updates after monorepo/package-layout migration.
  - Canonicalized package/app path references across docs and workflow guidance.
  - Removed standalone `careerdex` and `weatherdex` package scaffolds from `packages/`.
  - Updated CI/package validation and project metadata/docs to align with current structure.

## v0.3.3 - 2026-02-16

- Released package version `0.3.3`.
- Tag: `v0.3.3`
- Release title: `Release v0.3.3`
- Changes in this release (`src/dataenginex` only):
  - Significant package expansion and refactor across API, core, data, lakehouse, middleware, ML, and warehouse modules.
  - Added/expanded API modules including auth, pagination, rate limiting, and v1 router wiring.
  - Consolidated middleware layout (logging, metrics, tracing) and moved logging config under middleware.
  - Package diff from `v0.2.0` to `v0.3.3`: 39 files changed, 4213 insertions, 247 deletions.

## v0.2.0 - 2026-02-12

- Released package version `0.2.0`.
- Tag: `v0.2.0`
- Release title: `Release v0.2.0 - Production Hardening`
- Changes in this release (`src/dataenginex` only):
  - Established core package structure and initial module organization.
  - Added API readiness/health behavior and improved probe handling.
  - Added structured request logging with request ID tracking.
  - Added Prometheus metrics and OpenTelemetry tracing support in package middleware.
  - Added validation and error-handling improvements in API/core paths.

# CI/CD Pipeline

**Complete guide to DataEngineX continuous integration and release automation.**

> **Quick Links:** [CI Workflow](#continuous-integration-ci) · [Release Automation](#release-automation) · [Troubleshooting](#troubleshooting) · [Quick Reference](#quick-reference)

______________________________________________________________________

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Continuous Integration (CI)](#continuous-integration-ci)
- [Release Automation](#release-automation)
- [Rollback Procedures](#rollback-procedures)
- [Pipeline Metrics](#pipeline-metrics)
- [CI/CD Evolution](#cicd-evolution)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Related Documentation](#related-documentation)
- [Quick Reference](#quick-reference)

______________________________________________________________________

## Overview

DEX is a pure Python library published to PyPI. The pipeline is:

- **CI**: Automated testing, linting, and security scanning on every PR
- **Release**: Push a `v{X.Y.Z}` tag to `main` → `release.yml` builds, publishes, and creates a GitHub Release with CycloneDX SBOM

```mermaid
graph LR
    Dev[Developer] --> PR[Create PR to dev]
    PR --> CI[CI: Quality/Test/Security]
    CI --> Review[Code Review]
    Review --> MergeDev[Merge to dev]
    MergeDev --> PRMain[PR dev → main]
    PRMain --> MergeMain[Merge to main]
    MergeMain --> Tag[Push tag vX.Y.Z]
    Tag --> Release[release.yml]
    Release --> Build[Build wheel + sdist]
    Build --> PyPI[Publish to PyPI<br/>Trusted Publishing OIDC]
    Build --> GHRelease[GitHub Release<br/>+ CycloneDX SBOM]

    style CI fill:#e1f5ff
    style Release fill:#f8f5ff
    style PyPI fill:#d4edda
    style GHRelease fill:#d4edda
```

______________________________________________________________________

## Project Structure

DEX is a single-package repo:

| Component | Location | Purpose | Release |
| --- | --- | --- | --- |
| **dataenginex** | `src/dataenginex/` | Core framework (API, middleware, storage, ML) | PyPI (`v{version}`) |

### Unified Testing

The **root `pyproject.toml`** defines the package and test config:

- `name = "dataenginex"`, `version = "<current>"` (see `pyproject.toml`)
- `[tool.hatch.build.targets.wheel] packages = ["src/dataenginex"]`
- Dependency groups: `dev` (required), `data` (PySpark), `notebook` (pandas), `ml` (sentence-transformers)

**CI workflow** (`ci.yml`) runs two sequential jobs:

- `quality` job: `uv sync --group ml` + `poe quality` (lint + imports-check + typecheck + security audit)
- `test` job (needs quality): `poe test-cov-core` — pytest with coverage, uploads to Codecov
- `test-compat` job: weekly schedule only — Python 3.11/3.12 compatibility matrix
- `concurrency: cancel-in-progress: true` — stale runs cancelled on new push

### Release Automation

- **Release**: Push tag `v{X.Y.Z}` to `main` → `release.yml` triggers three parallel jobs: build wheel+sdist, publish to PyPI via OIDC trusted publishing, and create GitHub Release with CycloneDX SBOM attached

______________________________________________________________________

## Continuous Integration (CI)

**Workflow**: [`.github/workflows/ci.yml`](https://github.com/TheDataEngineX/dataenginex/blob/main/.github/workflows/ci.yml)

**Triggers**:

- Push to `main` or `dev` branches
- Pull requests targeting `main` or `dev`

**Jobs**:

### 1. Code Quality (`quality` job)

```bash
uv run poe quality  # lint + imports-check + typecheck + pip-audit
```

**Requirements**: Must pass before the `test` job starts.

### 2. Tests (`test` job)

```bash
uv run poe test-cov-core  # pytest --cov, coverage uploaded to Codecov
```

Coverage threshold: 80%. Results uploaded to Codecov with `flags: dataenginex`.

### 3. Python Compatibility (`test-compat` job)

Runs on a **weekly schedule** only (not on every PR). Tests against Python 3.11 and 3.12 to catch compatibility regressions before they affect users on older versions.

### 4. Security Scans

Runs via the shared reusable workflow at [`.github/workflows/security.yml`](https://github.com/TheDataEngineX/.github/blob/main/.github/workflows/security.yml):

- **Trivy**: Misconfig and secret scan — results uploaded to GitHub Security tab; HIGH/CRITICAL misconfiguration gate blocks the job
- **CodeQL**: Static analysis — handled by GitHub's default setup (results in Security tab)

**Results**: Available in the GitHub Security tab.

______________________________________________________________________

## Release Automation

**Workflow**: [`.github/workflows/release.yml`](https://github.com/TheDataEngineX/dataenginex/blob/main/.github/workflows/release.yml)

**Trigger**: Push a tag matching `v[0-9]+.[0-9]+.[0-9]+` to `main`

**Jobs**:

1. **build** — `uv build` → upload wheel + sdist as artifact
1. **publish-pypi** — download artifact → `pypa/gh-action-pypi-publish` (OIDC trusted publishing, no API token needed)
1. **github-release** — generate CycloneDX SBOM → `gh release create` with SBOM attached

**How to release**:

```bash
# After merging to main, create and push the tag
git tag v1.2.3
git push origin v1.2.3

# Monitor the release workflow
gh run list --workflow=release.yml --limit 5
gh run watch
```

**PyPI trusted publishing**: Configured at `pypi.org/manage/project/dataenginex/settings/publishing/`. Environment name: `pypi`. No API tokens — uses GitHub OIDC.

**Flow**:

```text
feature → PR to dev → PR to main → merge → git tag vX.Y.Z → push tag → release.yml → PyPI + GitHub Release
```

______________________________________________________________________

## Rollback Procedures

### Rollback a PyPI Release

PyPI does not support deleting releases, but you can:

1. Yank the release on PyPI (marks it as broken; `pip install` avoids it by default):

   ```bash
   # Via PyPI web UI: manage release → yank
   # Or via twine/API
   ```

1. Publish a patch release with the fix:

   ```bash
   # The pre-commit hook auto-bumps the patch version on commit
   git commit -m "fix: revert breaking change"
   git push origin main
   git tag v<new-patch>
   git push origin v<new-patch>
   ```

### Rollback a Git Tag

```bash
# Delete tag locally and remotely
git tag -d v<version>
git push origin :refs/tags/v<version>

# Delete the GitHub release via gh CLI
gh release delete v<version> --yes
```

______________________________________________________________________

## Pipeline Metrics

### Build Times

- **CI (Lint + Test)**: ~2 minutes
- **Package validation**: ~1 minute
- **PyPI publish**: ~2 minutes

### Success Rates (Target)

- **CI Pass Rate**: >95%
- **Release Success Rate**: >99%

### Monitoring

```bash
# Recent CI runs
gh run list --workflow ci.yml --limit 10

# Recent releases
gh run list --workflow release.yml --limit 10

# Failed builds
gh run list --workflow release.yml --status failure
```

______________________________________________________________________

## CI/CD Evolution

### Current State ✅

- [x] Automated CI with lint, test, type checks
- [x] Security scanning (CodeQL, Semgrep)
- [x] Automated PyPI release on tag push
- [x] Package validation (wheel + twine check)
- [x] GitHub Pages documentation deployment

### Future Enhancements 🚀

- [ ] **E2E smoke tests**: Post-release validation (install from PyPI and run examples)
- [ ] **Slack notifications**: Release status updates
- [ ] **Release notes**: Auto-generated from commits
- [ ] **Canary releases**: TestPyPI smoke test before PyPI promotion

______________________________________________________________________

## Troubleshooting

### CI Fails with Lint Errors

```bash
# Run lint checks locally
uv run poe lint

# Auto-fix
uv run poe lint-fix
```

### PyPI Publish Not Triggering

- Confirm tag `v{X.Y.Z}` was pushed to `main` (not `dev`)
- Verify PyPI trusted publisher matches: workflow `release.yml`, environment `pypi`
- View workflow logs: `gh run list --workflow release.yml`

### Package Build Fails

```bash
# Build locally to diagnose
uv build
twine check dist/*

# Verify pyproject.toml metadata
uv run python -c "import dataenginex; print(dataenginex.__version__)"
```

______________________________________________________________________

## Best Practices

### Development Workflow

1. **Create feature branch** from `dev`
1. **Develop and test locally**
1. **Run quality checks** before committing: `uv run poe lint`, `uv run poe typecheck`, `uv run poe test`
1. **Create PR** targeting `dev`
1. **Wait for CI** to pass
1. **Get code review** approval
1. **Merge to dev** → integration testing
1. **Create release PR** from `dev` → `main`
1. **Merge to main** → bump version if releasing

### Commit Messages

Use conventional commits for clarity:

```bash
feat: add new endpoint for data processing
fix: resolve memory leak in pipeline
chore: update dependencies
docs: improve deployment runbook
test: add integration tests for API
```

### PR Guidelines

- **Keep PRs small**: \<500 lines of code
- **Single purpose**: One feature/fix per PR
- **Test coverage**: Include tests for new code
- **Documentation**: Update docs for API changes

______________________________________________________________________

## Related Documentation

**Next Steps:**

- **Deployment Runbook** (in `infradex` repo) - Release procedures
- **[Observability](observability.md)** - Monitor applications built on DEX
- **[Contributing Guide](contributing.md)** - Development workflow

______________________________________________________________________

## Quick Reference

### Workflows Overview

| Workflow | Trigger | Purpose | File |
| --- | --- | --- | --- |
| **CI** | `push main/dev`, PRs to main/dev | Code quality (`poe quality`) + tests + weekly compat | [ci.yml](.github/workflows/ci.yml) |
| **Security** | `push main/dev`, PRs to main/dev | Trivy (misconfig + secrets) + CodeQL (default setup) | [security.yml](.github/workflows/security.yml) |
| **Release** | Push tag `v*.*.*` to main | Build → PyPI (trusted publishing) + GitHub Release + CycloneDX SBOM | [release.yml](.github/workflows/release.yml) |

### Local Commands

```bash
# Local development
uv lock
uv sync
uv run poe test
uv run poe lint

# Local with all dependencies (data + notebook)
uv sync --group data --group notebook
uv run poe test-cov

# Create PR
gh pr create --title "feat: add feature" --body "Description"

# Trigger optional integration tests
gh pr edit <pr-number> --add-label full-test

# Check CI status
gh pr checks <pr-number>

# Monitor CI
gh run list --workflow ci.yml
gh run view <run-id> --log

# Release: push tag to trigger release.yml
git tag v<version> && git push origin v<version>
gh run list --workflow release.yml
```

______________________________________________________________________

**[← Back to Documentation](index.md)**

# Decision log

## 0002 - Branching and SDLC (2026-10-28)

Development follows a main + feature branches flow, worked from the
Mac in the Zed editor. This applies to both repos (dataenginex and
dex-studio).

- main is the only long-lived branch. It stays green and releasable;
  no direct commits to main after the bootstrap skeleton.
- All work happens on short-lived feature branches named
  feature/<short-name> (example: feature/m0-definitions). One branch
  per milestone or task, matching the one-milestone-at-a-time rule.
- Flow: pull main in Zed, create the feature branch, build and commit
  there, push, open a pull request into main, review, merge, then
  delete the feature branch.
- Releases are tagged from main only.
- Jay works in Zed on the Mac; Muse prepares code, tests, and docs
  for his review, and nothing merges without his review.

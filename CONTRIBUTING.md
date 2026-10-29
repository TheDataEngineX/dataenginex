# Contributing

How work happens in this repo: main plus feature branches, everything
through a pull request, nothing merges without the founder's review
(decision 0002 in docs/decisions/).

## Branching

- main is the only long-lived branch. It stays green and releasable.
- All work happens on short-lived feature branches named
  feature/<short-name> - one branch per milestone or task.
- No direct commits to main. GitHub branch protection enforces the
  pull-request requirement.

## Workflow (Mac, Zed editor)

1. Pull the latest main.
2. Create the feature branch: git checkout -b feature/<short-name>
3. Build in small commits, scoped to one milestone or task.
4. Run the tests before pushing: python -m pytest
5. Push the branch and open a pull request into main. Say what
   changed and how it was tested.
6. After review and merge, delete the feature branch.

## Rules

- One milestone at a time. Park new ideas in the decision log or an
  issue instead of expanding a branch.
- New decisions (architecture, scope, licensing) go in
  docs/decisions/ as the next numbered entry, in the same pull
  request as the change they explain.
- Code is promoted into this foundation package only by the rule of
  two: a second consumer must need it first.
- Plain ASCII in code and docs.

# Contributing and branching

## Branching strategy (GitHub flow)

- **`main` is protected and always releasable.** Nothing is pushed to it directly. Every change arrives as a pull request.
- Work happens on short-lived branches, named by type:

  | Prefix | For |
  |---|---|
  | `feat/…` | New features |
  | `fix/…` | Bug fixes |
  | `docs/…` | Documentation only |
  | `chore/…` | Tooling, CI, housekeeping |
  | `export/…` | Configuration snapshots (private config repo) |

- **Pull requests:**
  - Must pass the checks.
  - Must be approved by the code owner (`@davidteles`). Only the owner approves and merges.
  - Are **squash-merged**, so `main` gets one clean commit per PR, titled after the PR. The branch is deleted after merging.
- **Releases** (integrations and cards) are tagged `vMAJOR.MINOR.PATCH` (semantic versioning) on `main`, with release notes.
  - Patch: fixes.
  - Minor: new features.
  - Major: anything that breaks existing setups.

## Commit messages

Imperative and short ("Add water tank sensor"), with a body explaining *why* when it isn't obvious.

## Privacy

No personal data, keys, tokens, codes or private hostnames, ever. Screenshots are people-free, with maps and balances blurred.

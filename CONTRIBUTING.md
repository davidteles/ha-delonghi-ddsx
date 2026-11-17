# Contributing and branching

## Branching strategy (GitHub flow)

- **`main` is protected and always releasable.** Nothing is pushed to it directly. Every change arrives as a pull request.
  A ruleset enforces it: no direct pushes, no force-pushes or deletion, and pull requests need the code owner's approval.
- Work happens on short-lived branches, named by type:

  | Prefix | For |
  |---|---|
  | `feat/…` | New features |
  | `fix/…` | Bug fixes |
  | `docs/…` | Documentation only |
  | `chore/…` | Tooling, CI, housekeeping |

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

## Tests

`pip install -r requirements_test.txt && pytest` (Python 3.13). The tests in `tests/` run Home Assistant with a fake unit (`tests/conftest.py`) that behaves like a real DDSX: one job at a time, and the purifier switched off turns the whole unit off. They assert which writes are sent, not just the final state. They run on every pull request.

## On-device checklist

A fake unit can't show the real 20-second shutdown or a real HomeKit session. Before releasing a change to the mode, alarm or connection code, check on a real unit and say in the pull request which you did:

1. **Dehumidify → Purify only:** the unit stops dehumidifying; Mode shows *Purify only* at once.
2. **Purify only → Dehumidify:** wait **60 s**; the unit is still **on** and dehumidifying.
3. **Off:** the unit turns off; Mode shows *Off* after the next poll.
4. **Tank out:** *Water tank* turns on within 30 s; **tank back:** it turns off and the unit resumes.
5. **Connection:** unplug the unit for a minute; entities go unavailable, then come back by themselves.

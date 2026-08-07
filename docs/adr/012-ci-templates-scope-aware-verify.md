# ADR-012: CI templates call the scope-aware verify entrypoint

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-08-06 · **Status:** accepted
**Deciders:** Chief Architect (defect surfaced during a CI-reinforcement review, no live incident report — caught before a consumer hit it)

## Context

ADR-002 fixed exactly one defect: `tools/doctrine_verify.py` ran `ruff check
tools tests` and `unittest discover -s tests -v` unconditionally, which in a
**consumer** repo (Doctrine installed alongside a host's own code) linted the
host's files under Doctrine's ruff config and ran the host's entire test
suite alongside Doctrine's own — observed live in MAPLE: hundreds of foreign
ruff findings, the test gate hung until interrupted. The fix made
`doctrine_verify.py` scope-aware via `is_source_repo()`: the full suite
(lint → ruff → tests → gold → state) only runs where Doctrine's own
`pyproject.toml` (`name = "doctrineos"`) is present; a consumer gets
lint + gold + state only.

That fix was never propagated to the three CI templates the installer ships
under `--ci`: `.github/workflows/doctrine.yml`, `.Doctrine/templates/ci/
gitlab-ci.yml`, `.Doctrine/templates/ci/azure-pipelines.yml`. Each
independently re-implemented the same four raw steps — `doctrine_lint.py`,
then an unconditional `pip install ruff && ruff check tools tests`, then an
unconditional `unittest discover -s tests -v`, then `doctrine_gold.py gate`
— predating ADR-002 and never updated when it landed. `doctrine.yml` is
installed byte-identical into a consumer repo (the installer's `CI_TARGETS`
maps source path to the same destination path), so any team that opted into
`--ci` inherited the exact defect ADR-002 already diagnosed and fixed one
layer up: Doctrine's ruff config against their own code, Doctrine's test
suite racing theirs. Two parallel implementations of "what does verify mean
here" had drifted, and the CI copy carried the older, unfixed one.

## Decision

The three CI templates no longer re-implement the verify sequence. Each now
runs two steps: install the pinned ruff (`doctrine_verify.py` checks
availability but does not install packages — installing dependencies is not
its job) and then a single call to `python tools/doctrine_verify.py`. Scope
detection is defined in exactly one place; the CI templates consume it
instead of shadowing it.

In the Doctrine source repo (this repo's own `.github/workflows/doctrine.yml`
run) `is_source_repo()` is true, so lint and ruff and tests are unchanged.
The gold gate is *not* unconditional under the new entrypoint the way the
old raw `doctrine_gold.py gate` step was: `doctrine_verify.py` only runs it
when `docs/releases/gold` exists, has a manifest, or git's history has ever
tracked it — otherwise it prints an announced skip. In this repo today none
of those hold yet (no gold record has been promoted), so CI currently skips
that gate entirely rather than running it and getting a "nothing promoted"
pass; the observable result is the same (a green run, no false confidence),
but the binary itself stops being exercised by CI until the first gold
record exists. In a consumer repo that installs any of these templates with
`--ci`, `doctrine_verify.py` now correctly skips ruff and the test suite
against the host's own code, matching what `doctrine_verify.py` already does
when run locally.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| A (chosen): CI templates call `doctrine_verify.py` | one source of truth; future scope fixes propagate to CI automatically; matches "same command locally and in CI" (skills/repo-devops.md) | CI logs collapse to one step instead of four named ones | acceptable — `doctrine_verify.py`'s own per-gate `=== name: PASS/FAIL` markers preserve step-level readability inside the one job |
| B: re-derive `is_source_repo()` logic separately in each CI YAML (conditional steps) | keeps four named CI steps | reintroduces exactly the duplication that caused this defect — a THIRD copy of the same scoping logic to keep in sync | rejected on the operating principle "fix the class, not the instance" |
| C: leave the CI templates as-is; document the gap | zero work | `--ci` remains a live foot-gun for every future adopter until they hit it in production, as MAPLE did for the local command | not acceptable — this is a known, already-fixed bug class recurring in an unfixed sibling |

## Consequences

- **Positive:** `--ci` is now safe to recommend by default for a consumer
  wanting real enforcement — it can no longer flood their code with
  Doctrine's own lint findings or hang on Doctrine's own test suite mixed
  into theirs. One entrypoint means one place to strengthen CI going
  forward (e.g. adding required hygiene checks) instead of three.
- **Negative / debt accepted:** the pinned-ruff install step still runs
  unconditionally in a consumer's CI (a few wasted seconds installing a
  linter `doctrine_verify.py` will then skip, since it isn't the source
  repo) — accepted for simplicity over adding a second conditional that
  would itself need to stay in sync with `is_source_repo()`.
- **Invalidation triggers:** `doctrine_verify.py`'s gate sequence changes in
  a way that should NOT reach CI unchanged (would argue for the CI template
  calling a different, CI-specific entrypoint instead of the shared one).

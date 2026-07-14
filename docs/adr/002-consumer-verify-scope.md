# ADR-002: doctrine_verify scopes to Doctrine's surface in a consumer repo

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-07-14 · **Status:** accepted (resolves the debt parked in ADR-001)
**Deciders:** Chief Architect (defect surfaced by the human in a real consumer, MAPLE)

## Context

`doctrine_verify` ran `ruff check tools tests` and `unittest discover -s tests`
unconditionally. In the Doctrine source repo those dirs hold only Doctrine's own
code, so it was correct. In a **consumer** repo (Doctrine installed alongside a host
project) `tools/` and `tests/` also hold the host's code: running there linted the
host's files under Doctrine's ruff config (hundreds of foreign findings) and ran the
host's entire test suite plus Doctrine's own heavyweight self-tests (which spawn `git`
subprocesses and run for minutes). Observed live in the MAPLE repo: ruff flooded with
MAPLE's own style findings and the test gate hung until interrupted. ADR-001 named this
as parked debt ("which gates belong in a consumer verify vs. the source repo"); it is
now a real, reported defect.

## Decision

We will make `doctrine_verify` **scope-aware**. `is_source_repo(root)` is true only when
`pyproject.toml` declares the `doctrineos` package (the installer never copies
pyproject.toml, so a consumer never matches). In the **source** repo the full dev suite
runs unchanged: lint → ruff → unittest → state. In a **consumer** repo only Doctrine's
own surface is verified — corpus **lint** and **state** — and ruff/tests are skipped with
a one-line note pointing to `unittest discover -s tests -p "test_doctrine_*.py"` for
anyone who wants Doctrine's own tool tests. Doctrine never lints the host's code or runs
the host's suite; that is the host's own tooling's job.

## Alternatives considered

| Option | Pros | Cons | Why not |
|--------|------|------|---------|
| A (chosen): detect source via `doctrineos` pyproject; consumer = lint+state | one command "just works" in both; no host-code linting; fast | detection keys on a package name string | robust enough (installer never ships pyproject; consumers name their own) |
| B: scope ruff/tests to `doctrine_*.py`/`test_doctrine_*.py` globs, always run | no source detection | still runs Doctrine's ~9-min self-tests + git subprocesses in every consumer | consumer doesn't need to re-run the tooling's unit tests each verify |
| C: add a `--full`/`--consumer` flag | explicit | pushes the choice onto every user; the turnkey ethos is "just works" | worse default UX |
| D / do nothing | zero work | verify is unusable in any repo with its own code (the reported defect) | not acceptable |

## Consequences

- **Positive:** `doctrine_verify` is usable in every consumer repo (MAPLE included); fast
  (lint+state, seconds); never imposes Doctrine's lint config or test runner on the host.
- **Negative / debt accepted:** source detection keys on the literal `name = "doctrineos"`
  in pyproject; a fork that renames the package must update `is_source_repo`. Documented in
  the function. A consumer that genuinely wants Doctrine's tool tests must run the named
  `-p` command explicitly.
- **Invalidation triggers:** the package is renamed away from `doctrineos`; or a future
  need for a consumer to run the full tool suite by default (would argue for option C's
  opt-in flag instead).

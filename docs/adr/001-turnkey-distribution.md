# ADR-001: Turnkey one-command install, verified in place

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-07-13 · **Status:** accepted
**Deciders:** Chief Architect (+ human: brief confirmed, "ready for next")

## Context

The productization brief (kept private) makes v0.1 a *turnkey
distribution*: acceptance criterion 1 requires "one documented command → full stack
installs and `doctrine_verify` passes 4 green gates, no manual fixups." Today the
installer (`tools/doctrine_install.py`) copies the law + tools but stops at a printed
"next steps: init, then verify" — so a real install is three commands (install → state
init → verify) plus flag knowledge. The law also "travels by repo" (05-packaging): the
wheel carries only tools, so the source must be a doctrine clone. The repo is private,
so a public `curl | bash` or PyPI bootstrap is not available yet (that unlocks if/when
the repo goes public). MAPLE runtime opt-in currently has no install-time affordance.

## Decision

We will make the **existing installer** the single command by adding two flags, not a
new tool: `--verify` runs `doctrine_state init` then `doctrine_verify` in the target
after copying (via `subprocess` with `sys.executable`, cross-platform), so one command
ends in a proven-green state and reports the 4 gates; `--maple` seeds `Workforce
runtime: maple` into the target's `docs/brief.md` (mirroring `--enterprise`/`--startup`)
and the quickstart points to the `integrations/maple.md` smoke path. `--source` keeps
auto-detecting the doctrine root, so from a clone the command is
`python tools/doctrine_install.py --target <repo> --verify`. A `QUICKSTART.md` documents
zero-to-verified. The public registry/`curl|bash` bootstrap is explicitly deferred to
the OSS-launch phase; it is a §5 external action and needs the repo public first.

## Alternatives considered

| Option | Pros | Cons | Why not |
|--------|------|------|---------|
| A (chosen): `--verify`/`--maple` flags on the installer | smallest change, one command, no new carrier, reuses tested code | install can run long (full gate suite) | — |
| B: new `doctrine-init` console script wrapping install+verify | tidy verb | adds a console-script + py-module version carrier to keep synced; duplicates logic | more surface for no new capability |
| C: `curl \| bash` / PyPI bootstrap now | true zero-clone install | repo is private (registry 404s); publishing is §5-gated; premature | deferred to OSS launch, recorded as a phase |
| D / do nothing (keep 3 steps + printed next-steps) | zero work | fails acceptance criterion 1 outright | not turnkey |

## Consequences

- **Positive:** one documented command from a doctrine clone to a verified install;
  MAPLE opt-in has a first-class affordance; no new version carrier to keep in sync;
  the verify step is the honest proof the install actually works.
- **Negative / debt accepted:** with `--verify` the full gate suite (incl. the ~100
  doctrine self-tests) can run for minutes on a consumer repo — thorough but heavy.
  Which gates belong in a *consumer* verify vs. the *source* repo (a consumer arguably
  needs lint + state-verify, not the tooling's own unit tests) is a refinement parked
  for a later phase, noted so it is not forgotten.
- **Invalidation triggers:** the repo going public (unlocks the `curl|bash`/PyPI
  bootstrap and reopens the "one command from a fresh machine, no clone" goal); or a
  decision to split the consumer test surface from the source test surface — **now
  decided in ADR-002** (consumer verify = lint + state; the parked debt is resolved).

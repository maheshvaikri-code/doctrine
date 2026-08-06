# Brief — Doctrine Enforcement Tooling (v0.2.0)
<!-- G0 artifact. Task class: L (new module). -->

## Problem
The doctrine is markdown law with no mechanical enforcement. The state
plane (`.Doctrine/state-plane/`) is a spec with no implementation; the
corpus's internal consistency (references, counts, formats, version sync)
is only checked by hand.

## Scope
1. `tools/doctrine_state.py` — stdlib-only Python reference implementation
   of the state plane: `init · checkpoint · verify · hydrate [--check] ·
   prune · status`, canonical JSON writer, hash-chained checkpoints,
   schema validation (subset validator, no third-party deps).
2. `tools/doctrine_lint.py` — CI gate for the doctrine corpus: reference
   resolution, role/skill format, agent↔role pairing, numeric-claim sync,
   version↔CHANGELOG sync, template gate tags, state-plane example
   validity + canonicality.
3. Tests (stdlib `unittest`), `Makefile` targets, GitHub Actions workflow.

## Non-goals
A separate binary serialization format (sibling pack not shipped — markdown bundle
only, per the HYDRATION.md fallback); external effect and intent writers (the CLI
reads those dirs if present).

## Acceptance criteria
- `doctrine_state` round-trip on a fresh temp repo: init → checkpoint →
  verify OK; tampered chain → verify fails; prune merges dead_ends forward;
  `hydrate --check` compiles twice to identical bundle hashes.
- Examples in `state-plane/examples/` validate against the schemas via the
  shipped validator and are byte-canonical.
- `doctrine_lint` exits 0 on the current corpus and nonzero when seeded
  with a broken reference (covered by test).
- All tests pass locally with real output shown; CI workflow runs both.

## Constraints
Python ≥3.11, stdlib only. Windows + POSIX. Canonicalization: UTF-8, LF,
sorted keys, no trailing whitespace, single trailing newline.

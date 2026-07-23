# Implementation Plan — Productization v0.1 (turnkey distribution)

<!-- G2 artifact. File as docs/plans/<task>.md. Update as reality diverges. -->

**Brief:** (private) · **Design/ADRs:** `docs/adr/001-turnkey-distribution.md` · **Class:** L (program) / this slice M

## Slices (ordered; each leaves the tree green)

| # | Slice | Role | Files touched | Proven by (tests) | Status |
|---|-------|------|---------------|-------------------|--------|
| 1 | `--verify` flag: after copy, run `state init` + `doctrine_verify` in target via `sys.executable`; report gates; exit non-zero if any gate fails | DevOps | `tools/doctrine_install.py` | new test: install `--verify` into a temp target exits 0 and prints gate summary | done+evidence |
| 2 | `--maple` flag: seed `Workforce runtime: maple` in target `docs/brief.md` (mirror `--enterprise`/`--startup`) | DevOps | `tools/doctrine_install.py` | new test: `--maple` writes the brief line; absent by default | done+evidence |
| 3 | `QUICKSTART.md`: zero-to-verified, honest about the clone prerequisite + MAPLE opt-in step | Tech Writer | `QUICKSTART.md` | manual: steps match the flags exactly (criterion 2) | done+evidence |
| 4 | CHANGELOG entry + doc pointers (05-packaging "next steps", README link) | DevOps | `CHANGELOG.md`, `.Doctrine/05-packaging.md` | lint (version sync), verify | done+evidence |

## Threat sketch (required for Class L)

Assets touched: the installer, which writes files into a target repo and now *executes*
`python` in that target (`state init`, `verify`). Entry points / untrusted inputs:
`--target` path, `--source` path (already resolve/nest-guarded). Worst plausible abuse:
`--verify` runs the target's `tools/*.py`; if the target already carried a *different*
`doctrine_verify.py`/`doctrine_state.py`, `copy_file` SKIPS it (skip-on-diff without
`--force`) — so without a guard `--verify` would execute code this installer did not
write and could print a false "gates green" (G5 MAJOR-1, found and fixed in review).
Mitigation (implemented): `--verify` refuses to run when any `TOOL_FILES` entry is in
`report.skipped_diff` — it will not execute a verifier it did not write; the operator
resolves the conflict or passes `--force`. On a clean/forced install the files executed
are the doctrine's own. subprocess uses an argv list, no `shell=True`, `sys.executable`,
`cwd=target`; no network, no new dependency. `--verify` never weakens a gate; it surfaces
the real exit code and a failing suite makes the install exit non-zero (criterion 5).

## Risks & rollback points

- Risk: `--verify` runs long on slow machines → mitigation: it is opt-in (default install
  unchanged, still prints next-steps) → rollback: drop the flag, installer behaves as before.
- Risk: subprocess portability (Windows vs POSIX) → mitigation: `sys.executable` + argv
  list, no shell → rollback: revert to printed next-steps.
- Risk: a consumer repo's full self-test suite is noisy → accepted as debt in ADR-001,
  parked for a later phase.

## Deviation log (append-only, as they happen)

- 2026-07-13: G5 security review found MAJOR-1 — `--verify` executed the *target's*
  tool files, but `copy_file` skips different-content files (no `--force`), so a
  pre-existing/hostile `doctrine_verify.py` would run and print a false "gates green"
  (reviewer reproduced it live). Routed back to G3. Fix: `run_post_install`'s caller now
  refuses `--verify` when any `TOOL_FILES` entry is in `report.skipped_diff` (exit 2);
  threat sketch corrected; regression test `test_verify_refuses_on_tool_conflict` added.

## Status snapshot (update at session end / handoff)

Done (with evidence): slices 1-4 built; real end-to-end `--verify` into a temp target
exited 0 with `Workforce runtime: maple` seeded; source `doctrine_verify` = 4 gates
green; G5 security review = conditional sign-off, MAJOR-1 remediated + re-tested. · Next:
commit + tag v0.6.12 + checkpoint; then v0.2 (daemon) at its own G0/G1 with Head of AI +
CISO. · Blocked on: nothing.

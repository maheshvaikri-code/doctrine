# QA / Security Report — Productization v0.1 (turnkey distribution)

<!-- G5 artifact. File as docs/qa/<task>.md -->

**Date:** 2026-07-13 · **Brief:** `docs/briefs/productization.md` · **Plan:** `docs/plans/productization-v0.1.md`

## Acceptance criteria — evidence

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | one command → install + verify green, no fixups | PASS | real end-to-end `python tools/doctrine_install.py --target <tmp> --maple --verify` exited 0; final line `turnkey: installed and verified - gates green` |
| 2 | quickstart path works end to end | PASS | `QUICKSTART.md` steps match the flags; the `--verify` run above exercises install→init→gates |
| 3 | cross-platform | PARTIAL | verified on Windows/Py3.12 (this host); `doctrine_verify` is make-free and stdlib-only, macOS/Linux legs run in CI — not re-run here, stated honestly |
| 4 | MAPLE opt-in recorded + smoke path | PASS | seeded `docs/brief.md` contained `Workforce runtime: maple`; smoke path documented in `integrations/maple.md` |
| 5 | no criterion met by weakening a check; no secret path | PASS | security review confirmed exit-code plumbing honest; guard added so a false green cannot originate from unvetted target code |

## Gate suite (source repo)

`python tools/doctrine_verify.py` → `VERIFY OK: 4 gate(s) green` (lint, ruff, tests, state).
Test count 116 (source), incl. 6 new installer tests.

## Security review (G5)

Fresh-context security-reviewer, adversarial, on the installer diff. Verdict: **conditional
sign-off, no ship veto**, one MAJOR remediated:

- **MAJOR-1 (fixed):** `--verify` executed the target's `tools/*.py`; `copy_file` skips
  different-content files without `--force`, so a pre-existing/hostile `doctrine_verify.py`
  would execute and print a false "gates green". Reviewer reproduced it live. **Fix:**
  `--verify` now refuses when any `TOOL_FILES` entry is in `report.skipped_diff` (exit 2);
  threat-sketch mitigation corrected; regression `test_verify_refuses_on_tool_conflict`.
- **MINOR-1 (accepted):** no subprocess timeout — acceptable for an opt-in interactive CLI.
- **NIT-1 (accepted):** `init or verify` returncode drops the second code when both fail;
  still non-zero, no security impact.
- **Clean:** no shell/argv injection (fixed argv list, `shell=False`, only `sys.executable`
  is variable); path guards intact before the new code; exit code honestly surfaced; no
  secrets logged; only new import is stdlib `subprocess` (dependency policy not triggered).

Post-fix: full source suite re-run green (see gate suite above); the new guard is
regression-tested. Unconditional sign-off / any veto override remains the human's.

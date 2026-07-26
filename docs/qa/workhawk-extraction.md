# QA + Security Report - WorkHawk application extraction @ 43d1a30

**QA Engineer / Security Reviewer:** serial role-hat validation
**Date:** 2026-07-25
**Build under test:** `43d1a3055244560558022c69bc6c4f52c52562e3`

## Acceptance criteria verification

| # | Criterion | How executed | Evidence | Pass |
|---|---|---|---|---|
| 1 | The application is tracked only under `workhawk/` and identifies as WorkHawk. | Git rename review plus source contract test. | No tracked `dashboard/package.json`; package name `workhawk`; required Sites plug-in present in a fresh hosted checkout. | yes |
| 2 | WorkHawk owns the shell while Doctrine is the active governance module. | Production render and hosted Chromium live-state scenario. | Title `WorkHawk | Doctrine`, WorkHawk brand lockup, Doctrine breadcrumb/module, and connected Doctrine state rendered. | yes |
| 3 | The v1 Doctrine snapshot and fixed verification operation remain wired. | Fourteen Python bridge tests, typed client contract, production tests, and hosted Doctrine matrix. | Existing v1 paths unchanged; snapshot parsing and fixed verifier action retained; all bridge and repository tests passed. | yes |
| 4 | MAPLE, STIX, and Trust remain honestly unavailable. | Registry contract plus per-row browser assertions. | Only Doctrine declares `doctrine-api-v1`; each of MAPLE, STIX, and Trust rendered “Unavailable” with no action. | yes |
| 5 | Loading, empty, partial, error, and live states remain accessible. | Hosted Playwright Chromium with Axe and keyboard scenarios. | Seven of seven passed in 18.5 seconds, including focus trap, skip link, reduced motion, and 390 x 600 navigation. | yes |
| 6 | WorkHawk gates pass on Windows and Ubuntu. | GitHub Actions run 30189259820 from the lockfile. | Lint, TypeScript, build, five tests, and audit passed on both systems; Chromium job passed. | yes |
| 7 | A Windows production preview serves every rendered asset. | Real production-server regression in the Windows job. | Five-test suite passed; every rendered CSS/JavaScript request returned the correct non-empty content type. | yes |
| 8 | Doctrine consumers do not receive WorkHawk source or CI. | Installer/workflow contract assertion. | Installer contains no WorkHawk workflow path; source-only workflow runs from `workhawk/`. | yes |

## Adversarial and edge matrix

| Input/scenario | Expected | Observed | Pass |
|---|---|---|---|
| Empty/non-Doctrine repository | No fabricated metrics; actionable empty state | Empty-state scenario rendered and exposed retry | yes |
| Partial/stale evidence | Preserve known fields and name missing/stale evidence | Partial banner retained repository identity and reason | yes |
| Bridge error | Fail closed with accessible retry | Alert contained server error and retry action | yes |
| Delayed bridge response | Loading state precedes live state | Delayed fixture rendered both states in order | yes |
| Short narrow viewport | Sidebar remains keyboard reachable and scrollable | 390 x 600 scenario passed with `overflow-y: auto` | yes |
| Reduced motion | Animations collapse without losing interaction | Media query active; transition duration at or below 1 ms | yes |
| Invalid E2E port: text, zero, or greater than 65535 | Configuration rejects before starting a server | Range/digits validation is enforced by config and source contract | yes |
| Malformed production port | Launcher exits nonzero | `3011junk` regression passed | yes |
| Disconnected future modules | No connected status, capabilities, or actions | Three modules individually rendered unavailable | yes |

## Regression

```text
Local WorkHawk
npm run lint                                      exit 0
npm run typecheck                                 exit 0
npm test                                          5 pass; 0 fail
npm run audit                                     0 vulnerabilities

Local Doctrine boundary
python -m unittest discover ...                   14 pass; 0 fail
python -m ruff check ...                          All checks passed
python tools/doctrine_lint.py                     corpus clean

Hosted WorkHawk run 30189259820
Ubuntu                                              success
Windows                                             success
Chromium                                            7 passed (18.5s)

Hosted Doctrine run 30189259821
Ubuntu/Python 3.11                                  186 tests; success
Ubuntu/Python 3.12                                  186 tests; success
Windows/Python 3.11                                 186 tests; success
Windows/Python 3.12                                 186 tests; success
```

Flakes observed: none. The earlier run `30189192792` failed deterministically
on an ambiguous test locator; it was corrected and the exact-commit rerun is
green.

## Bugs found

| # | Minimal reproduction | Severity | Fixed @ | Re-verified | Regression test |
|---|---|---|---|---|---|
| 1 | Move the app while `build/` is globally ignored, then inspect staged paths. | blocker | `b61a086` | hosted fresh checkout | required Sites plug-in access assertion |
| 2 | Open mobile navigation at 390 x 600 after adding four module rows. | minor | `b61a086` | hosted Chromium | narrow keyboard scenario |
| 3 | Run live browser fixture containing WorkHawk in brand, activity, and footer. | minor | `43d1a30` | 7/7 hosted Chromium | exact brand locator |

## Security sweep

Secrets scan: clean. Injection review: no dynamic HTML, eval, arbitrary command,
or shell path. Dependency audit: zero vulnerabilities on local, Ubuntu, and
Windows runs. Dangerous constructs: bounded shell-free production test process
only. Bounds/fail-closed: typed API parsing, exact API version, loopback origin,
bounded verifier, validated ports, and explicit unavailable module states.

The local interactive browser controller exposed no installed backend, and the
local Playwright Chromium executable was absent. Hosted CI installed Chromium
from a clean checkout and is the real-browser authority for this report. No
manual assistive-technology certification or public deployment was performed.

**Security verdict:** SIGN-OFF for the documented local-only boundary.

**QA verdict:** PASS.

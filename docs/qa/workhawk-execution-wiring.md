# QA + Security Report - WorkHawk verification execution wiring @ 4c9f26c

**QA Engineer / Security Reviewer:** serial role-hat validation  
**Date:** 2026-07-26  
**Build under test:** `4c9f26c251440f90d451f786d4772311e15975e4`

## Acceptance criteria verification

| # | Criterion | How executed | Evidence | Pass |
|---|---|---|---|---|
| 1 | One immediate start, all triggers disabled | Chromium accepted-run scenario with delayed POST and request counters | Starting state and pending ID appeared before acceptance; primary action disabled; one POST observed | yes |
| 2 | Poll only current verification while running | Dynamic current/snapshot routes | First running poll produced `Live sync`; snapshot count remained one until terminal; two current reads total | yes |
| 3 | One terminal reconciliation with authoritative metadata | Passed terminal fixture and exact request counts | One post-terminal snapshot (two snapshots total); ID, commit, 47-second duration, exit code, and 186 tests rendered | yes |
| 4 | Dirty snapshot blocks both triggers | Dirty browser fixture and POST counter | Primary and palette commands disabled; commit-or-stash reason visible; zero POST | yes |
| 5 | Rejected start is exact and recoverable | 409 error-envelope fixture | `A verification is already running.` announced in an alert; primary action restored; one POST | yes |
| 6 | Poll failure preserves evidence and degrades sync | Running fixture plus 503 current resource | Run `run-degraded` remained visible; `Sync delayed` and recovery text appeared; full snapshot was not replaced | yes |
| 7 | Keyboard, responsive, reduced motion, and WCAG | Desktop/dialog/390-pixel Chromium and Axe | No A/AA violations; focus loop/restoration passes; 390-pixel width has no overflow; reduced motion collapses transition time | yes |
| 8 | No dependency, API, or authority expansion | Exact diff and security scan | No manifest, lockfile, OpenAPI, or bridge file changed; audit found zero vulnerabilities | yes |

## Adversarial and edge matrix

| Input/scenario | Expected | Observed | Pass |
|---|---|---|---|
| Duplicate interaction while POST unsettled | One accepted request | Immediate disabled state plus client lock; one POST | yes |
| Snapshot still loading | No execution authority | Palette verification disabled with wait-for-evidence reason; zero POST | yes |
| Disconnected repository | Empty state, no verifier authority | Empty state rendered; readiness guard requires `repository.connected` | yes |
| Dirty repository | No POST | Both triggers disabled; zero POST | yes |
| Concurrent bridge job / 409 | Exact error, controls recover | Exact error announced; eligible control restored after reconciliation | yes |
| Current resource unavailable | Preserve last good evidence | Running ID/status retained; degraded warning; bounded retry continues | yes |
| Passed terminal result | Healthy final record | Final ID/commit/duration/exit/tests and passed gates rendered | yes |
| Failed terminal result | Blocked final record | Failed summary, run ID, exit data, and blocked semantics rendered | yes |
| Partial repository evidence | Preserve known fields | Exact partial reason plus known repository data remained visible | yes |
| Empty repository | Retryable empty state | Doctrine-enabled-folder guidance and retry control rendered | yes |
| Bridge snapshot error | Accessible failure, retry available | Exact bridge error in alert and retry control | yes |
| Modal background | Inaccessible while dialog owns focus | Sidebar/workspace inert and ARIA-hidden; dialog focus loop and restoration pass | yes |
| 390 x 600, reduced motion | No overflow or animation dependency | Scroll width did not exceed viewport; transition at most 1 ms | yes |

The operation sends a fixed empty JSON object and accepts no user payload, so
string-size, Unicode, negative-number, and limit+1 mutation cases are not
applicable to this client change. Those HTTP bounds remain bridge-owned and
covered by the unchanged Doctrine dashboard suite.

## Regression

```text
CANDIDATE 4c9f26c251440f90d451f786d4772311e15975e4

npm run lint                                      exit 0
npm run typecheck                                 exit 0
npm test                                          6 pass; 0 fail
npm run audit                                     0 vulnerabilities
WORKHAWK_E2E_PORT=3317 npm run test:e2e           12 pass; 0 fail

python tools/doctrine_verify.py
doctrine_lint                                      pass
ruff                                               pass
unittest                                           186 pass; 0 fail
state                                              28 checkpoints; pass
VERIFY OK                                          4 gates green
```

Flakes observed: none. Port 3003 was occupied by a stale local 404 service, so
the documented `WORKHAWK_E2E_PORT` path used fresh loopback port 3317. The
expected Playwright Chromium binary was initially absent and was installed to
the machine test cache; no repository dependency or lockfile changed.

## Bugs found and re-verified

| # | Minimal reproduction | Severity | Fixed @ | Re-verified | Regression |
|---|---|---|---|---|---|
| 1 | Open command palette before delayed snapshot resolves and inspect verification eligibility | major | `4c9f26c` | yes | loading-state zero-POST scenario |
| 2 | Run Axe with command dialog open | minor | `4c9f26c` | yes | dialog Axe + focus scenario |
| 3 | Render initial execution metadata and run Axe | minor | `4c9f26c` | yes | desktop/dialog/narrow Axe |
| 4 | Render a failed terminal verification | minor | `4c9f26c` | yes | blocked final-record scenario |

## Security sweep

Secret scan: clean. Injection review: all operations use fixed endpoint paths
and a fixed `{}` body; no dynamic HTML, executable string, path, or shell input.
Dependency audit: zero vulnerabilities. Dangerous constructs: none added.
Bounds/fail-closed: every response is strictly parsed, every request is
abortable and timed, unknown repository eligibility disables execution, dirty
and duplicate starts are blocked in the UI and independently rejected by the
bridge.

**Security verdict:** SIGN-OFF.  
**QA verdict:** PASS.

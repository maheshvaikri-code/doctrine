# QA + Security Report - WorkHawk enterprise UI @ ae04e20

**QA Engineer / Security Reviewer:** serial role-hat validation
**Date:** 2026-07-26
**Build under test:** `ae04e20f31e26db99fbc6ee7d910afb4bdebcd07`

## Acceptance criteria verification

| # | Criterion | How executed | Evidence | Pass |
|---|---|---|---|---|
| 1 | Command search filters, exposes empty state, contains focus, and restores trigger focus. | Hosted keyboard/browser scenario with Axe. | Search receives focus; “release” removes unrelated commands; unmatched text yields an explicit status; reverse-tab wraps; Escape restores the trigger. | yes |
| 2 | KPI cards pair exact values with text status and only truthful progress. | Source contract and live browser roles. | Four cards carry status; exactly two progressbars exist for activation and four verification gates. | yes |
| 3 | Gate score is a native meter derived from passed gates divided by four. | Live fixture role/value assertion. | Four passed gates produce `aria-valuenow="100"` on “Verification gate score”. | yes |
| 4 | Trend chart derives geometry and accessible text from the selected series. | Exact accessible-name assertion. | 30D chart exposes total `35` and series `1, 2, 2, 3, 4, 3, 5, 4, 6, 5`. | yes |
| 5 | Desktop and 390 px remain accessible, keyboard operable, non-overflowing, and reduced-motion aware. | Desktop, dialog, and narrow Axe scans plus keyboard and computed-style assertions. | Seven browser scenarios passed; narrow document width stays within the viewport; reduced-motion transition is at most 1 ms. | yes |
| 6 | Motion remains the sole animation runtime and component source is local. | Package/source contract and review. | Lock graph unchanged; Motion retained; Anime.js absent; no external registry source copied. | yes |
| 7 | Production serves the app, generated assets, and official logo. | Real production-server tests on Windows and Ubuntu. | Six of six tests passed on each OS; rendered CSS/JS and 1,195,360-byte PNG return successful non-empty responses. | yes |

## Adversarial and edge matrix

| Input/scenario | Expected | Observed | Pass |
|---|---|---|---|
| Search matches one action | Only matching action remains | “release” retained release and removed verification | yes |
| Search matches nothing | Explicit non-action state | “No matching Doctrine actions.” status | yes |
| Shift+Tab from first dialog control | Wrap to last enabled action | Release action received focus | yes |
| Escape after filtering | Close and restore launcher focus | Dialog hidden; launcher focused | yes |
| All gates pass | Meter bounded at 100 | `aria-valuenow=100` | yes |
| Exact ten-value series | Total and values are named | Total 35 and all ten values matched | yes |
| 390 x 600 viewport | No horizontal overflow | document scroll width did not exceed viewport | yes |
| Reduced-motion preference | Essential information remains; duration collapses | Complete chart DOM remained; transition at most 1 ms | yes |
| Disconnected modules | Visual polish must not imply connection | MAPLE, STIX, and Trust remained individually unavailable | yes |

## Regression

```text
Local
npm run lint                                      exit 0
npm run typecheck                                 exit 0
npm test                                          6 pass; 0 fail
npm run audit                                     0 vulnerabilities
python tools/doctrine_lint.py                     corpus clean

Hosted WorkHawk run 30190168835
Ubuntu                                              success
Windows                                             success
Chromium                                            7 passed (16.6s)

Hosted Doctrine run 30190168794
Ubuntu/Python 3.11                                  186 tests; success
Ubuntu/Python 3.12                                  186 tests; success
Windows/Python 3.11                                 186 tests; success
Windows/Python 3.12                                 186 tests; success
```

Flakes observed: none. Run `30189823057` failed deterministically on the stale
pre-search focus expectation. The corrected behavior passed runs
`30189959751`, `30190079309`, and the stronger exact-criterion run
`30190168835`.

## Security sweep

Secrets scan: clean. Injection review: fixed client-side command metadata only;
no bridge query or executable string. Dependency audit: zero vulnerabilities.
Dangerous constructs: none added. Bounds/fail-closed: gate score clamped to
0-100, chart has a zero-safe series fallback, values are API-validated
non-negative integers, and disconnected modules remain non-actionable.

The local interactive browser service exposed no installed backend, so hosted
fresh Chromium is the browser authority. Automated Axe is not a substitute for
manual assistive-technology certification.

**Security verdict:** SIGN-OFF.

**QA verdict:** PASS.

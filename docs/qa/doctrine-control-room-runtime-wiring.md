# QA + Security Report - Doctrine Control Room runtime wiring @ 704d7b2085d4

**QA Engineer / Security Reviewer / Date:** serial role-hat review, 2026-07-25
**Build under test:** `704d7b2085d4`

## Acceptance criteria verification

| # | Criterion | How executed | Evidence | Pass |
|---|---|---|---|---|
| 1 | Dashboard receives truthful repository, activation, state, evidence, release, and activity data. | Live `GET /api/v1/snapshot` plus snapshot/HTTP unit tests. | `doctrineos` `0.6.46`, branch `main`, commit `704d7b2085d4`, clean tree, activation `9/9`, state checkpoint `23`, eight recent commits; snapshot tests pass. | yes |
| 2 | One clean verification is accepted, polled, and rendered with gates/test count. | Bridge lifecycle tests and prior live loopback POST/poll. | Accepted job reached `passed`; all four gates were present. Final clean evidence is rerun after the report/checkpoint commit so it cannot be misattributed. | yes, automated/HTTP |
| 3 | Bridge outage produces an accessible retryable error without prototype values. | Production server render and source contract inspection. | `role="alert"`, start instruction, retry button, loading live region; rendered test rejects prototype strings. | automated pass; real browser unavailable |
| 4 | Missing/stale evidence produces exact partial/empty states while retaining known fields. | Snapshot and rendered-contract tests; live stale-verification snapshot. | Snapshot named `The latest verification belongs to another commit.` while retaining repository data; all five state identifiers are covered. | yes |
| 5 | Invalid origins, dirty tree, wrong media type/body, oversize body, and concurrency fail without command execution. | 14 bridge tests plus live dirty-tree `POST`. | `403`, `409 worktree_dirty`, `415`, `400`, `413`, and concurrent `409` paths pass. | yes |
| 6 | Only the fixed verifier runs, without a shell, with bounded time/output. | Source review and adversarial tests. | Argument array is `[sys.executable, repo/tools/doctrine_verify.py]`; loopback bind; 180s timeout; 32KiB tail; 1KiB request; no command/path input. | yes |
| 7 | Build, lint, tests, verification, and dependency audit pass. | Clean commands shown below. | Clean install and audit: zero vulnerabilities; dashboard: 2/2; bridge: 14/14; Doctrine: 186 tests and four gates. | yes |

## Adversarial and edge matrix

| Input/scenario | Expected | Observed | Pass |
|---|---|---|---|
| Unknown browser origin | `403`, no snapshot/action | rejected | yes |
| Mutation with `text/plain` | `415`, no action | rejected | yes |
| Malformed or non-empty JSON | `400`, no action | rejected | yes |
| Body at limit + 1 | `413` before body read/action | rejected | yes |
| Dirty worktree | `409 worktree_dirty` | reproduced live and in test | yes |
| Second concurrent request | `409 verification_in_progress` | regression passes | yes |
| Output beyond 32KiB | retain only newest 32KiB | regression passes | yes |
| Repository changes mid-run | invalidate all gate evidence | regression passes | yes |
| Worker raises unexpectedly | terminal failed state, never stuck running | regression passes | yes |
| Exit zero with a reported failed gate | overall failed | regression passes | yes |
| Missing project metadata | truthful disconnected/empty snapshot | regression passes | yes |

## Regression

```text
python -m unittest discover -s tests -p test_doctrine_dashboard.py -v
Ran 14 tests in 5.322s
OK

npm ci
added 328 packages, and audited 329 packages in 20s
found 0 vulnerabilities

npm run lint
exit 0

npm test
2 tests; 2 pass; 0 fail
Build complete (Vite 8.1.5)

python tools/doctrine_verify.py
Ran 186 tests in 41.896s
OK
=== lint: PASS
=== ruff: PASS
=== tests: PASS
=== state: PASS
VERIFY OK: 4 gate(s) green
```

Flakes observed: none.

## Bugs found

| # | Minimal repro | Severity | Fixed @ | Re-verified | Regression test |
|---|---|---|---|---|---|
| 1 | Return exit zero with one `=== ...: FAIL` marker and a terminal `VERIFY OK`. | major | `704d7b2` | yes | `test_exit_zero_with_a_failed_gate_fails_closed` |
| 2 | Run `npm audit --audit-level=moderate` against the prior lockfile. | major | `8204192` | yes; zero vulnerabilities | clean `npm ci` + audit |

Earlier G4 defects involving dirty/mid-run worktrees, unexpected worker
exceptions, reduced motion, touch targets, and signed exit codes were also
re-executed through their named regressions or lint/build checks.

## Security sweep

- Secrets scan: no credential-assignment patterns in the task diff.
- Injection review: fixed paths and subprocess argument arrays only; no shell,
  command, repository, or path input crosses the HTTP mutation boundary.
- Dependency audit: `npm audit --audit-level=moderate` reports
  `found 0 vulnerabilities`; Python runtime adds no third-party dependency.
- Dangerous constructs: no `shell=True`, `eval`, `exec`, pickle deserialization,
  disabled TLS, or remote bind in the task diff.
- Bounds/fail-closed: exact origin allowlist, JSON-only empty object, 1KiB
  request cap, one-job lock, 5s Git timeout, 180s verifier timeout, 32KiB output
  tail, clean-tree checks before and after execution, contradictory evidence
  rejected.

**Security verdict:** SIGN-OFF for the local loopback design; remote exposure
would require a new ADR and authentication/threat review.

**QA verdict:** automated and HTTP criteria pass, but full G5 UI sign-off is
release-blocked. The required real-browser keyboard, focus-order, responsive,
reduced-motion, and screen-reader pass was not executed because the available
browser controller reported zero browser backends. No deployment or publishing
is approved by this report.

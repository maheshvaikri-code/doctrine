# Code Review - Doctrine Control Room runtime wiring @ 704d7b2085d4

**Reviewer roles:** Code Reviewer, Security Reviewer, Project Reviewer
**Date:** 2026-07-25
**Reviewed against:** [runtime wiring brief](../briefs/doctrine-control-room-runtime-wiring.md),
[implementation plan](../plans/doctrine-control-room-runtime-wiring.md), and
[ADR-008](../adr/008-doctrine-control-room-local-bridge.md)

**Review method:** Serial role-hat review by the implementing agent. This was
not an independent fresh-context reviewer pass; that limitation is recorded
rather than represented as fan-out.

## Executed

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
vinext build (Vite 8.1.5): complete

python tools/doctrine_verify.py
Ran 186 tests in 41.896s
OK
lint PASS; ruff PASS; tests PASS; state PASS
VERIFY OK: 4 gate(s) green
```

Security scans over files changed since checkpoint `0aa8de5` found no
credential-assignment patterns and no `shell=True`, `eval`, `exec`, pickle,
disabled-TLS, or equivalent dangerous constructs.

## Findings

| # | Sev | Location | Finding | Suggested fix | Resolution |
|---|---|---|---|---|---|
| 1 | [MAJOR] | `tools/doctrine_dashboard.py` verification parser | Exit code zero plus four reported gates was sufficient for an overall pass even if one gate explicitly said `FAIL`. This violated fail-closed evidence semantics. | Require exact gate identity, every verdict `PASS`, an exit code of zero, and a matching terminal `VERIFY OK` count. Add a contradictory-output regression. | fixed@`704d7b2` |
| 2 | [MAJOR] | verification request/start boundary | A run accepted from a dirty worktree could attribute uncommitted behavior to `HEAD`. | Reject dirty worktrees before accepting a job and test the HTTP `409 worktree_dirty` response. | fixed@`cf3b769` |
| 3 | [MAJOR] | verifier lifecycle | A repository change during a run could leave apparently valid evidence attached to the starting commit. | Compare commit and worktree after exit; force all gates failed when either changed. | fixed@`2849b27` |
| 4 | [MAJOR] | `dashboard/package-lock.json` | The current registry audit disclosed 12 vulnerabilities, including 10 high severity, in the frontend toolchain. | Upgrade patched Vite/Cloudflare/React packages and replace the vulnerable aggregate ESLint config with current flat-config components. | fixed@`8204192`; `npm audit` now reports zero |
| 5 | [MINOR] | verification worker/client boundary | Unexpected worker exceptions could leave the public job running; signed exit codes were not accepted by the client parser. | Settle unexpected failures and validate exit codes as signed integers. | fixed@`cf3b769` |
| 6 | [MINOR] | dashboard interaction styles | Programmatic smooth scrolling ignored reduced-motion preference and some compact controls were below the 44px touch target. | Switch to automatic scrolling under reduced motion and raise compact targets. | fixed@`0237b17` |
| 7 | [NIT] | dashboard stylesheet | Prototype-only selectors survived after the live component replaced the prototype. | Remove dead selectors and rename the evidence badge. | fixed@`493e722` |

All blocker and major findings are resolved. The original dirty-tree
verification result was discarded as evidence; the clean full-suite result
above is the reviewed baseline.

## Scope check

The diff matches the seven acceptance criteria: a loopback-only bridge,
versioned contract, one fixed verification action, validated client boundary,
five truthful UI states, operating documentation, and tests. MAPLE,
Shield/STIX, Trust, portfolio aggregation, remote access, authentication,
publishing, and arbitrary execution remain explicitly out of scope. No remote
service or deployment was created.

## Verdict

- [x] Pass (0 open BLOCKER or MAJOR findings)
- [ ] Return to build

G4 passes. This verdict does not replace the real-browser G5 interaction check
recorded as unavailable in the QA report.

# Code Review - WorkHawk verification execution wiring @ 4c9f26c

**Reviewer roles:** Code Reviewer, Security Reviewer, Project Reviewer  
**Date:** 2026-07-26  
**Reviewed against:** [project brief](../briefs/workhawk-execution-wiring.md),
[implementation plan](../plans/workhawk-execution-wiring.md), and
[ADR-010](../adr/010-workhawk-verification-execution-lifecycle.md)

**Review method:** Serial fresh-hat review by the implementing agent. Sub-agent
delegation was not authorized, so this is not represented as an independent
reviewer pass.

## Executed evidence

Exact implementation commit:
`4c9f26c251440f90d451f786d4772311e15975e4`.

```text
npm run lint
exit 0

npm run typecheck
exit 0

npm test
tests 6; pass 6; fail 0

npm run audit
found 0 vulnerabilities

WORKHAWK_E2E_PORT=3317 npm run test:e2e
12 passed (25.2s)

python tools/doctrine_verify.py
Ran 186 tests in 54.870s
OK
ruff: PASS
state: PASS - 28 checkpoint(s), chain intact
VERIFY OK: 4 gate(s) green
```

## Findings

| # | Sev | Location | Finding | Resolution |
|---|---|---|---|---|
| 1 | [MAJOR] | `workhawk/app/doctrine-module.tsx:790,919` | The command palette is available while the initial snapshot is loading or unavailable. Its verification command and imperative guard originally checked only dirty/running state, so a keyboard user could POST before repository eligibility was known. | Require a ready, connected snapshot in both the rendered command state and `runVerification`; browser loading state proves a disabled command and zero POST. fixed@`4c9f26c` |
| 2 | [MINOR] | `workhawk/app/doctrine-module.tsx:821` | A rejected or lost start response launched snapshot rediscovery without awaiting it, leaving a short retry window before an accepted server-side job could be rediscovered. | Await bounded snapshot reconciliation before releasing the client start lock. fixed@`4c9f26c` |
| 3 | [MINOR] | `workhawk/app/doctrine-module.tsx:396` | Failed and timed-out final records used the neutral execution tone and refresh icon. | Map both terminal failure states to the blocked semantic treatment and add a failed-record browser scenario. fixed@`4c9f26c` |
| 4 | [MINOR] | command-dialog background | Keyboard focus was trapped, but the dashboard behind the modal remained exposed to assistive technology; the dialog Axe scan also evaluated obscured background content. | Apply `inert` and `aria-hidden` to the sidebar/workspace while the command dialog is open; focus restoration remains verified. fixed@`4c9f26c` |
| 5 | [MINOR] | execution metadata colors | Initial metadata text measured 4.42:1, below the WCAG AA 4.5:1 threshold. | Darken the local execution metadata token; desktop, dialog, and 390-pixel Axe scans pass. fixed@`4c9f26c` |

All findings are resolved. There are zero open BLOCKER or MAJOR findings.

## Scope check

The diff implements the existing bounded verification lifecycle only:
immediate start locking, current-job reads, terminal snapshot reconciliation,
dirty/loading/disconnected preflight, exact bridge errors, and an
evidence-derived execution record. It does not add arbitrary commands,
cancellation, logs, durable history, connectors, authentication, publishing,
or remote repository authority.

The OpenAPI document, bridge implementation, package manifests, and lockfile
are unchanged. Motion remains the sole animation runtime.

## Security review

- Secret-like assignment scan: none.
- Dangerous DOM/execution scan: no `dangerouslySetInnerHTML`, `eval`,
  `child_process`, `exec`, `new Function`, `document.write`, or `innerHTML`
  assignment.
- Fixed browser endpoints remain `/snapshot`, `/verifications/current`, and
  `/verifications`; no command, path, or operator input enters a URL or body.
- All bridge responses pass the existing strict snapshot/verification parsers.
- Requests are abortable and time bounded; recursive polling has one timer and
  one controller per running record.
- Dependency audit reports zero vulnerabilities; dependency and lock graphs
  did not change.
- Loopback binding, exact-origin checks, dirty-tree validation, single-job
  concurrency, fixed argument-array execution, and output/time bounds remain
  enforced by the unchanged bridge.

**Security verdict:** SIGN-OFF.

## Project review

Every brief criterion maps to executed exact-commit evidence in the
[QA report](../qa/workhawk-execution-wiring.md). Delivered scope equals
briefed scope: the existing fixed verifier is fully projected from preflight
through terminal evidence, while deferred cancellation, output streaming,
durable history, connectors, authentication, export, publishing, and
deployment remain absent.

The behavior, architecture decision, operating instructions, changelog,
review, and QA evidence are filed under `docs/` or `workhawk/README.md`.
There are no open BLOCKER or MAJOR findings. The implementation commit is
conventional and exact-commit local gates pass.

The repository still contains the human's pre-existing untracked
`workhawk/logo/` and `workhawk/public/brand/` folders. They were neither
modified nor staged by this task, so the global worktree is not represented as
clean. Task-owned changes are attributable and committed.

**G6 entry:** SIGNED for local integration. External push, deployment, tag, and
publication remain human-authority gates.

## Verdict

- [x] Pass (0 open BLOCKER or MAJOR findings)
- [ ] Return to build

G4 passes.

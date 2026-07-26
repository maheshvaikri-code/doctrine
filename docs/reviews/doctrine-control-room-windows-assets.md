# Code Review - Doctrine Control Room Windows asset repair @ f371825

**Reviewer roles:** Code Reviewer, Security Reviewer, Project Reviewer
**Date:** 2026-07-25
**Reviewed against:** [implementation plan](../plans/doctrine-control-room-windows-assets.md)
and [ADR-008](../adr/008-doctrine-control-room-local-bridge.md)

**Review method:** Serial fresh-hat review by the implementing agent. Sub-agent
delegation was not authorized for this task, so this is not represented as an
independent reviewer pass.

## Scope and evidence

The repair is limited to the dashboard production-launch boundary, local font
selection, regression coverage, and operating documentation. It adds no
runtime dependency, changes no bridge exposure or command boundary, and does
not deploy the local Control Room.

```text
npm run lint
exit 0

npm run typecheck
exit 0

npm test
5 tests; 5 pass; 0 fail

npm audit --audit-level=moderate
0 vulnerabilities

python tools/doctrine_verify.py
Ran 186 tests in 56.050s
OK
VERIFY OK: 4 gate(s) green

GitHub Actions dashboard run 30186825337
Windows: success; Ubuntu: success; Chromium: 7 passed

GitHub Actions Doctrine run 30186825339
Windows/Python 3.11 and 3.12: success
Ubuntu/Python 3.11 and 3.12: success
```

## Findings

| # | Sev | Location | Finding | Resolution |
|---|---|---|---|---|
| 1 | [MAJOR] | vinext production static-file cache on Windows | Cache keys were produced with backslashes while browser asset URLs used forward slashes. The HTML returned `200`, but all six CSS/JavaScript requests returned `404`, leaving the server-rendered connecting shell in place. | Add a Windows-only launcher that normalizes `path.relative` during vinext server/cache construction and restores it immediately; prove the real built server boundary. fixed@`f371825` |
| 2 | [MAJOR] | generated document font URLs | `next/font/google` emitted host-absolute `D:/...` font URLs in the Windows build. | Use explicit native UI and code font stacks; reject Windows absolute font URLs in the production regression. fixed@`f371825` |
| 3 | [BLOCKER] | first launcher location | The first review candidate lived under ignored `dashboard/build/`, so the repair would have disappeared from the commit and CI checkout. | Move the launcher to tracked `dashboard/scripts/start.mjs` and assert that path in the rendered contract test. fixed@`f371825` |
| 4 | [MINOR] | production launcher port parsing | Permissive integer parsing accepted values such as `3011junk`. | Require a digits-only port in the valid TCP range and cover malformed input. fixed@`f371825` |
| 5 | [MINOR] | CSS font token names | The first repair draft retained Geist-named tokens despite no longer loading Geist. | Rename the tokens to honest UI/code semantics. fixed@`f371825` |
| 6 | [MINOR] | PowerShell operating instructions | A multiline shell continuation was not portable to the documented Windows environment. | Use a cross-shell single-line bridge command. fixed@`f371825` |

All findings are resolved. The Windows-only compatibility patch is tightly
scoped, restored in `finally`, and backed by a production HTTP regression that
starts the real built server on an ephemeral port.

## Security review

- No credential-like assignments were found in the task diff.
- No new package or Python dependency was added; the package audit is clean.
- The only subprocess creation is in the regression harness, uses an argument
  array without a shell, and has deterministic termination with a kill
  fallback.
- The bridge remains loopback-only with its existing exact-origin policy.

**Security verdict:** SIGN-OFF for the existing local-only boundary.

## Verdict

- [x] Pass (0 open BLOCKER or MAJOR findings)
- [ ] Return to build

G4 passes.

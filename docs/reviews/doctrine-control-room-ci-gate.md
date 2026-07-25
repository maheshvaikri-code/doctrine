# Code Review - Doctrine Control Room CI gate @ 11ed8779b961

**Reviewer role:** Code Reviewer
**Date:** 2026-07-25
**Reviewed against:** [CI gate plan](../plans/doctrine-control-room-ci-gate.md)

**Review method:** serial fresh-hat review by the implementing agent because
subagent delegation was not authorized. This is not represented as an
independent reviewer session.

## Executed

```text
npm ci
added 328 packages, and audited 329 packages in 16s
found 0 vulnerabilities

npm run lint
exit 0

npm run typecheck
tsc --noEmit --incremental false
exit 0

npm test
tests 3; pass 3; fail 0
Build complete (Vite 8.1.5)

npm run audit
found 0 vulnerabilities

python tools/doctrine_verify.py
Ran 186 tests in 40.404s
lint PASS; ruff PASS; tests PASS; state PASS
VERIFY OK: 4 gate(s) green
```

## Findings

| # | Sev | Location | Finding | Suggested fix | Resolution |
|---|---|---|---|---|---|
| 1 | [MAJOR] | `dashboard/worker/index.ts:6` | The newly added TypeScript gate failed because the Worker referenced an undeclared global `Fetcher` type. Builds had not exposed the missing compile-time contract. | Define the narrow owned asset-fetch interface actually used by the Worker; add no platform package. | fixed@`73ef1a8`; original `npm run typecheck` failure rerun green |
| 2 | [MINOR] | `.github/workflows/dashboard.yml:11` | The first workflow draft ran only on Linux even though the repository's supported development path and prior defects are Windows-relevant. | Add a bounded Ubuntu/Windows OS matrix and require both in the contract test. | fixed@`11ed877` |

No blocker or major finding remains.

## Scope check

The workflow is source-only and does not alter
`tools/doctrine_install.py` or the consumer `doctrine.yml`. It uses the
committed dashboard lockfile, the minimum declared Node version, read-only
repository permissions, two official actions pinned to full SHAs, and a
ten-minute timeout. No dependency, deploy step, artifact publication, secret,
or runtime behavior was added.

The contract test is intentionally small: it proves scripts, permissions,
action pins, OS matrix, working directory, cache lockfile, command order, and
installer isolation. It does not claim to emulate GitHub Actions.

## Verdict

- [x] Pass
- [ ] Return to build

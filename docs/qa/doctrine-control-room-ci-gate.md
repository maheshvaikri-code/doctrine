# QA + Security Report - Doctrine Control Room CI gate @ 11ed8779b961

**QA Engineer / Security Reviewer / Date:** serial role-hat verification,
2026-07-25

**Build under test:** `11ed8779b961`

## Acceptance criteria verification

| # | Criterion | How executed | Evidence | Pass |
|---|---|---|---|---|
| 1 | Pushes and pull requests use the lockfile on minimum Node. | Workflow contract test and source inspection. | Triggers include push/PR; Node `22.13.0`; `npm ci`; lockfile cache path; Ubuntu/Windows matrix. | yes, configuration |
| 2 | Lint, types, build/tests, and moderate audit fail the job. | Contract test plus each local script executed after `npm ci`. | Every command exits zero locally; workflow steps have no `continue-on-error`. | yes |
| 3 | Local commands and workflow order match. | `npm test`. | `source CI enforces every dashboard gate...` passes; 3/3 dashboard tests. | yes |
| 4 | Consumer workflow remains dashboard-agnostic. | Contract test and installer diff review. | Installer still copies only `.github/workflows/doctrine.yml`; `dashboard.yml` is not referenced. | yes |
| 5 | Workflow cannot publish or request write authority. | Permission and step review. | Only `contents: read`; no secret, environment, upload, deploy, publish, or write step. | yes |

## Regression evidence

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
✔ server-renders the Doctrine control room
✔ ships an accessible, state-complete, dependency-scoped surface
✔ source CI enforces every dashboard gate without changing consumer CI
tests 3; pass 3; fail 0

npm run audit
found 0 vulnerabilities

python tools/doctrine_verify.py
Ran 186 tests in 40.404s
OK
VERIFY OK: 4 gate(s) green
```

Flakes: none. The first `npm ci` attempt failed with Windows `EPERM` because
the local preview held a native module open. After stopping the preview, the
same command passed on the next and only retry. This is a local process-lock
condition; CI starts from a clean runner.

## Bugs found

| # | Repro | Severity | Fixed @ | Re-verified | Regression |
|---|---|---|---|---|---|
| 1 | Run `npm run typecheck` before the fix. | major | `73ef1a8` | yes | permanent typecheck CI step |
| 2 | Inspect the initial Linux-only workflow against Windows support. | minor | `11ed877` | yes | OS-matrix contract assertions |

## Security sweep

- Secrets: no credential-assignment pattern in commits since checkpoint 25.
- Permissions: repository contents read-only; no OIDC, packages, deployments,
  issues, pull-request writes, environments, or secrets.
- Supply chain: checkout and setup-node use full official commit SHAs;
  dependencies install from `package-lock.json`; audit reports zero findings.
- Execution: pull-request code necessarily runs its own package scripts, but
  receives no repository write permission or secret in this workflow.
- Dangerous constructs: none introduced.

**Security verdict:** SIGN-OFF.

**QA verdict:** local configuration and regression pass. The GitHub-hosted
execution is pending the first push and is not claimed as observed. The parent
Control Room's real-browser keyboard/screen-reader G5 blocker also remains open:
the browser controller again reported zero available backends, and no fallback
browser software was installed.

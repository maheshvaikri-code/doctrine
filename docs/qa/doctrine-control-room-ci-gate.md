# QA + Security Report - Doctrine Control Room CI gate @ c8907975aab9

**QA Engineer / Security Reviewer / Date:** serial role-hat verification,
2026-07-25

**Build under test:** `c8907975aab98dddded98a7176498709f40dcfc9`

## Acceptance criteria verification

| # | Criterion | How executed | Evidence | Pass |
|---|---|---|---|---|
| 1 | Pushes and pull requests use the lockfile on minimum Node. | Workflow contract test, exact-toolchain local run, and hosted run. | Node `22.13.0` / npm `10.9.2`; `npm ci`; Ubuntu and Windows both pass. | yes |
| 2 | Lint, types, build/tests, and moderate audit fail the job. | Contract test, local execution, and hosted step results. | Every command exits zero locally and on both hosted OS legs; no `continue-on-error`. | yes |
| 3 | Local commands and workflow order match. | `npm test`. | `source CI enforces every dashboard gate...` passes; 3/3 dashboard tests; all workflow action refs are SHA-pinned. | yes |
| 4 | Consumer workflow remains dashboard-agnostic. | Contract test and installer diff review. | Installer still copies only `.github/workflows/doctrine.yml`; `dashboard.yml` is not referenced. | yes |
| 5 | Workflow cannot publish or request write authority. | Permission and step review. | Only `contents: read`; no secret, environment, upload, deploy, publish, or write step. | yes |

## Local regression evidence

```text
npx --package node@22.13.0 --package npm@10.9.2 --call "npm ci ..."
added 328 packages, and audited 329 packages
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
Ran 186 tests in 45.206s
OK
VERIFY OK: 4 gate(s) green
```

Flakes: none. The first `npm ci` attempt failed with Windows `EPERM` because
the local preview held a native module open. After stopping the preview, the
same command passed on the next and only retry. This is a local process-lock
condition; CI starts from a clean runner.

## Hosted regression evidence

| Commit | Workflow | Matrix result | Evidence |
|---|---|---|---|
| `9fdde17` | doctrine-dashboard | failed | [run 30179680083](https://github.com/aroora-ai-labs/doctrine/actions/runs/30179680083): Ubuntu `npm ci` rejected the npm-11-generated lockfile; Windows was cancelled by matrix fail-fast. |
| `abb949d` | doctrine-dashboard | passed | [run 30179904285](https://github.com/aroora-ai-labs/doctrine/actions/runs/30179904285): Ubuntu and Windows passed clean install, lint, typecheck, build/tests, and audit. |
| `abb949d` | doctrine | passed | [run 30179904288](https://github.com/aroora-ai-labs/doctrine/actions/runs/30179904288): Python 3.11/3.12 on Ubuntu/Windows all passed. |
| `c890797` | doctrine-dashboard | passed | [run 30180068322](https://github.com/aroora-ai-labs/doctrine/actions/runs/30180068322): both OS legs passed with SHA-pinned Node 24 action runtimes and no deprecation annotation. |
| `c890797` | doctrine | passed | [run 30180068321](https://github.com/aroora-ai-labs/doctrine/actions/runs/30180068321): all four Python/OS legs passed with independent matrix execution. |

The repair loop consumed two of the three allowed iterations: first lockfile
portability and matrix observability, then action-runtime/supply-chain
hardening. No unchanged retry was used.

## Bugs found

| # | Repro | Severity | Fixed @ | Re-verified | Regression |
|---|---|---|---|---|---|
| 1 | Run `npm run typecheck` before the fix. | major | `73ef1a8` | yes | permanent typecheck CI step |
| 2 | Inspect the initial Linux-only workflow against Windows support. | minor | `11ed877` | yes | OS-matrix contract assertions |
| 3 | Run hosted CI at `9fdde17` with Node 22/npm 10. | major | `abb949d` | yes, both hosted OS legs | npm `10.9.2` manifest pin plus npm-10-compatible lockfile |
| 4 | Observe Windows cancellation after Ubuntu failed. | minor | `abb949d` | yes | `strategy.fail-fast: false` assertion |
| 5 | Inspect enabled Pages/wiki workflows after GitHub emitted a Node 20 action warning. | major | `c890797` | yes, hosted source workflows | every repository workflow action reference is a verified 40-character SHA |
| 6 | Observe deprecated Node 20 runtimes on checkout/setup actions. | minor | `c890797` | yes, annotation absent | current official Node 24-based action releases |

## Security sweep

- Secrets: no credential-assignment pattern in commits since checkpoint 25.
- Permissions: repository contents read-only; no OIDC, packages, deployments,
  issues, pull-request writes, environments, or secrets.
- Supply chain: every `uses:` reference in all four repository workflows is a
  full official commit SHA and contract-enforced; dependencies install from
  `package-lock.json`; audit reports zero findings.
- Execution: pull-request code necessarily runs its own package scripts, but
  receives no repository write permission or secret in this workflow.
- Dangerous constructs: none introduced.

**Security verdict:** SIGN-OFF.

**QA verdict:** local and GitHub-hosted CI pass on the exact tested commits.
The parent Control Room's real-browser keyboard/screen-reader G5 blocker remains
open: the browser controller reported zero available backends, and no fallback
browser software was installed.

**Publishing note:** repository variables `DOCTRINE_PAGES_PUBLISH` and
`DOCTRINE_WIKI_PUBLISH` were both `on` when inspected. The earlier `9fdde17`
push therefore ran both publishing workflows successfully. Neither `abb949d`
nor `c890797` matched their path filters, so this repair loop caused no further
Pages or wiki publication.

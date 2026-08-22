# QA Report - Doctrine Control Room Windows asset repair @ f371825

**QA Engineer / Date:** serial role-hat validation, 2026-07-25
**Build under test:** `f3718255bc63297c7e3f39f3e54cc193d430cc68`

## Acceptance criteria

| # | Criterion | Evidence | Pass |
|---|---|---|---|
| 1 | Windows production preview returns its HTML, CSS, and JavaScript. | Before repair: page `200`, all six rendered assets `404`. After repair at `127.0.0.1:3011`: page `200`, six of six assets `200`, correct CSS/JavaScript content types, non-empty bodies. The production regression starts the built server on an ephemeral port and checks every rendered asset. | yes |
| 2 | Rendered output exposes no host filesystem font URL. | Local probe reported `broken-font-path=False`; regression rejects Windows absolute font URLs. | yes |
| 3 | Startup rejects malformed ports. | `npm test` proves `3011junk` exits nonzero with an actionable error. | yes |
| 4 | The local bridge remains correctly connected. | `GET /api/v1/snapshot` returned `200`, `Access-Control-Allow-Origin: http://127.0.0.1:3011`, passed verification, and zero partial reasons. | yes |
| 5 | Linux and existing browser behavior are preserved. | Hosted Ubuntu dashboard job passed; hosted Chromium completed all seven accessibility/state scenarios. | yes |
| 6 | Repository gates remain green. | Local lint, typecheck, five dashboard tests, dependency audit, 186-test Doctrine verification; hosted Windows/Ubuntu and Python 3.11/3.12 jobs all passed. | yes |

## Regression detail

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
=== lint: PASS
=== ruff: PASS
=== tests: PASS
=== state: PASS
VERIFY OK: 4 gate(s) green
```

Hosted evidence:

- [Dashboard run 30186825337](https://github.com/maheshvaikri-code/doctrine/actions/runs/30186825337):
  Windows success, Ubuntu success, Chromium `7 passed (18.1s)`.
- [Doctrine run 30186825339](https://github.com/maheshvaikri-code/doctrine/actions/runs/30186825339):
  Windows and Ubuntu on Python 3.11 and 3.12 all succeeded.

Flakes observed: none.

## Boundary and accessibility notes

The regression covers the exact boundary that failed: browser-visible asset
URLs against the real production server, rather than only build success or
component rendering. Hosted Chromium also re-ran keyboard, state, reduced
motion, and automated accessibility scenarios.

The available local interactive browser controller reported no browser
backends, so no additional local interactive or manual screen-reader session
was possible. This limitation does not weaken the fixed asset boundary or the
hosted automated-browser result, but manual assistive-technology certification
remains a separate release activity.

**QA verdict:** PASS for this loading defect and its automated browser
regression. The Control Room is operational locally at
`http://127.0.0.1:3011/`; no remote deployment was part of this repair.

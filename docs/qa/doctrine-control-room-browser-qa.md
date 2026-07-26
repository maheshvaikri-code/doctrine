# QA + Security Report - Doctrine Control Room browser QA @ 55cee5d3b863

**QA Engineer / Security Reviewer / Date:** serial role-hat verification,
2026-07-25

**Build under test:** `55cee5d3b863a572a0d50081ef98f8822ead2571`

## Acceptance criteria verification

| # | Criterion | How executed | Evidence | Pass |
|---|---|---|---|---|
| 1 | Production Control Room boots under hosted Chromium from the lockfile and minimum Node version. | Browser CI builds and starts the production server after `npm ci`. | Final browser job passed under Node 22.13.0 with the npm-10 lockfile. | yes |
| 2 | Keyboard interaction proves skip navigation and complete modal focus behavior. | Playwright keyboard-only sequences. | Skip link moves focus to `#main-content`; command focus enters, cycles in both directions, closes with Escape, and returns to the trigger. | yes |
| 3 | Loading, live, partial, empty, and error states preserve evidence semantics. | Deterministic route interception and state assertions. | All five state paths are included in the seven passing scenarios; no prototype copy appears in live state. | yes |
| 4 | Narrow navigation and reduced motion work. | 390 x 844 viewport plus emulated reduced-motion preference. | Navigation opens by keyboard, exposes the close control, closes with Escape, and metric transition duration resolves to at most 1 ms. | yes |
| 5 | Automated WCAG A/AA analysis is clean. | Axe 4.12.1 in Chromium on the settled live surface and open command dialog. | Final run reports no Axe violations. | yes |
| 6 | Gate stays source-only, bounded, read-only, and consumer-absent. | Workflow and rendered-contract review. | Separate ten-minute job, `contents: read`, SHA-pinned actions, no upload/deploy/secrets, and no installer reference. | yes |

## Hosted browser evidence

| Iteration | Commit | Result | Named outcome |
|---|---|---|---|
| 1 | `d682301` | [run 30185556600](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185556600): 4 passed, 3 failed | Found chart semantics, color contrast, and ambiguous test locators. |
| 2 | `6f87761` | [run 30185733031](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185733031): 6 passed, 1 failed | Axe was clean; one obsolete dialog-label assertion remained. |
| 3 | `55cee5d` | [run 30185799191](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185799191): 7 passed in 18.0 s | Chromium gate, Ubuntu dashboard, and Windows dashboard all green. |

The final hosted browser was Chrome Headless Shell 151.0.7922.34. The ratchet
used its three planned iterations; no unchanged retry was used.

Final Doctrine regression:
[run 30185799199](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185799199)
passed Python 3.11 and 3.12 on Ubuntu and Windows.

## Regression evidence

```text
npm run lint
exit 0

npm run typecheck
exit 0

npm test
tests 3; pass 3; fail 0

npm audit --audit-level=high
found 0 vulnerabilities

npm run test:e2e -- --list
Total: 7 tests in 1 file

python tools/doctrine_verify.py
Ran 186 tests in 55.452s
VERIFY OK: 4 gate(s) green

hosted browser-qa
Running 7 tests using 1 worker
7 passed (18.0s)
```

## Security sweep

- Authority: workflow permissions are limited to `contents: read`.
- Inputs: browser responses are in-process deterministic fixtures; no external
  service or untrusted credential is used.
- Secrets: no secrets, tokens, environments, OIDC, or write-capable APIs are
  referenced.
- Supply chain: Playwright and Axe are exact development dependencies installed
  from the committed lockfile; official actions are pinned to full SHAs.
- Outputs: no browser artifact, deployment, package, comment, or publication is
  uploaded.
- Isolation: the dashboard browser workflow is not copied by
  `tools/doctrine_install.py` and does not alter consumer CI.

**Security verdict:** SIGN-OFF.

**QA verdict:** G5 automated browser QA passes. Manual NVDA, JAWS, VoiceOver, or
TalkBack sign-off remains open because the connected local browser controller
reported no available backend. Axe and keyboard automation are not represented
as a manual screen-reader session.

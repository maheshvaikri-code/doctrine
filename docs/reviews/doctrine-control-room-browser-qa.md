# Code Review - Doctrine Control Room browser QA @ 55cee5d3b863

**Reviewer role:** Code Reviewer
**Date:** 2026-07-25
**Reviewed against:** [browser QA plan](../plans/doctrine-control-room-browser-qa.md)

**Review method:** serial fresh-hat review by the implementing agent because
subagent delegation was not authorized. This is not represented as an
independent reviewer session.

## Reviewed surface

- the Playwright 1.62.0 and Axe 4.12.1 harness;
- seven deterministic browser scenarios;
- production-build web-server configuration;
- keyboard, dialog, responsive, reduced-motion, and UI-state behavior;
- the source-only GitHub Actions browser job;
- accessibility repairs prompted by hosted Chromium.

## Executed

```text
npm run lint
exit 0

npm run typecheck
tsc --noEmit --incremental false
exit 0

npm test
Build complete (Vite 8.1.5)
tests 3; pass 3; fail 0

npm audit --audit-level=high
found 0 vulnerabilities

npm run test:e2e -- --list
Total: 7 tests in 1 file

python tools/doctrine_verify.py
Ran 186 tests in 55.452s
lint PASS; ruff PASS; tests PASS; state PASS
VERIFY OK: 4 gate(s) green
```

The connected Codex browser controller reported no available browser backend,
so no local interactive-browser result is claimed. Real-browser execution came
from the committed hosted Chromium gate.

Hosted evidence:

- first dashboard
  [run 30185556600](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185556600):
  four browser scenarios passed and three failed with actionable findings;
- second dashboard
  [run 30185733031](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185733031):
  Axe and six scenarios passed; one stale-label focus assertion failed;
- final dashboard
  [run 30185799191](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185799191):
  seven browser scenarios, Ubuntu dashboard, and Windows dashboard passed;
- final Doctrine
  [run 30185799199](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185799199):
  Python 3.11 and 3.12 on Ubuntu and Windows passed.

## Findings

| # | Sev | Location | Finding | Resolution |
|---|---|---|---|---|
| 1 | [MAJOR] | `dashboard/app/live-control-room.tsx` | The commit-trend chart had an accessible name on a generic `div`, which Axe rejected as a prohibited ARIA attribute. | fixed@`6f87761`: the visual is a named `role="img"` and its decorative bars/grid remain hidden |
| 2 | [MAJOR] | `dashboard/app/globals.css` | Muted text fell below WCAG AA on canvas and surface backgrounds; the initial scan also ran during opacity transitions, multiplying the reported nodes. | fixed@`6f87761`: accessible light/dark muted tokens, corrected component colors, and a settled-panel assertion before Axe |
| 3 | [MINOR] | `dashboard/tests/browser/control-room.spec.mjs` | Global role locators matched both hero and dialog controls, and both mobile close controls. | fixed@`6f87761`: locators are scoped to the dialog and complementary navigation |
| 4 | [MINOR] | `dashboard/tests/browser/control-room.spec.mjs` | A focus-cycle assertion used an obsolete command label, so the element could not be found after the product locator ambiguity was removed. | fixed@`55cee5d`: assertion uses the rendered `Inspect release identity` label |

No blocker or major finding remains.

## Design and scope check

The suite starts the production dashboard, intercepts only the local snapshot
and verification endpoints, and supplies deterministic data. It covers loading,
live, partial, empty, and error states without inserting prototype evidence into
the product.

The browser job is separate from the Ubuntu/Windows build matrix, has a
ten-minute timeout, uses the committed lockfile and minimum Node version,
installs only Chromium, grants only `contents: read`, and uses full-SHA official
actions. It does not upload artifacts, deploy, publish, access secrets, mutate
the repository, or enter the consumer installer.

The focus test verifies the initial command focus, reverse/forward containment,
Escape close, and restoration to the invoking control. The narrow test verifies
skip navigation, keyboard-operated mobile navigation, Escape close, and reduced
motion. Axe scans the settled live surface and open command dialog against WCAG
A/AA tags.

## Verdict

- [x] Pass
- [ ] Return to build

Manual screen-reader behavior is not signed off. That remains an explicit
operator QA item rather than being inferred from Axe or keyboard automation.

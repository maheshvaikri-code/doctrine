# Implementation Plan - Doctrine Control Room browser QA

**Parent brief:** `docs/briefs/doctrine-control-room-runtime-wiring.md`

**Class:** M

**Gate:** G5 UI verification

## Problem

The dashboard's source contracts and loopback API pass, but no interactive
browser backend is available in the current Codex session. The repository needs
a repeatable real-browser gate that can run independently of an operator's
desktop while preserving the distinction between automated accessibility
evidence and a manual screen-reader pass.

## Acceptance criteria

1. A production Control Room build boots under hosted Chromium from the
   committed lockfile and minimum declared Node.js version.
2. Keyboard evidence proves the skip link, command shortcut, initial dialog
   focus, focus containment, Escape close, and focus restoration.
3. Browser tests render loading, live, partial, empty, and error states from
   controlled API responses without prototype data.
4. A narrow/mobile viewport proves navigation can open and close by keyboard;
   reduced-motion preference is exercised.
5. Automated WCAG A/AA analysis reports no violations on the live surface and
   command dialog.
6. The browser job is source-only, read-only, SHA-pinned, bounded, and absent
   from consumer installations.

## Slice

| # | Change | Evidence | Status |
|---|---|---|---|
| 1 | Add Playwright/Axe browser harness and deterministic API fixtures | local type/lint/build contracts | done |
| 2 | Cover keyboard, modal, responsive, reduced-motion, and five UI states | hosted Chromium test report | done |
| 3 | Add a separate Ubuntu Chromium job to dashboard CI | workflow contract + hosted run | done |
| 4 | Record review, QA, and remaining manual screen-reader limitation | review/QA artifacts | done |

## Loop profile

Ratchet, budget 3. Each loop must move a named hosted browser failure to a
regression or return to this plan. No retry-until-green behavior is permitted.

## Security and rollback

- Browser responses are deterministic test fixtures; no credential, remote
  service, or repository mutation is used.
- Workflow permissions stay `contents: read`; action references stay pinned to
  full official commit SHAs.
- Playwright and Axe are development-only dependencies and remain outside
  Doctrine consumer installations.
- Rollback removes the browser job, configuration, tests, and two development
  dependencies; runtime behavior is unchanged unless a browser finding
  requires a separately reviewed fix.

## Explicit limit

Hosted Chromium plus Axe is real-browser automated evidence. It does not claim
to be a manual NVDA, JAWS, VoiceOver, or TalkBack session. Manual screen-reader
sign-off remains open until an appropriate interactive environment exists.

## Result

Implemented in `d682301`, repaired in `6f87761` and `55cee5d`, and verified by
[dashboard run 30185799191](https://github.com/aroora-ai-labs/doctrine/actions/runs/30185799191).
The browser job ran seven scenarios in hosted Chromium and passed in 18.0
seconds. The final source commit also passed both dashboard OS legs and all four
Doctrine Python/OS legs.

The three-iteration ratchet produced named regressions rather than unchanged
retries:

1. The first run exposed an unlabeled chart semantic, transient/real contrast
   defects, and two ambiguous locators.
2. The second run proved Axe clean and narrowed the only failure to one stale
   dialog-label assertion.
3. The final run passed all seven scenarios.

Review and QA evidence:

- `docs/reviews/doctrine-control-room-browser-qa.md`
- `docs/qa/doctrine-control-room-browser-qa.md`

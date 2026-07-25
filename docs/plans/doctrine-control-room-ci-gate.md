# Implementation Plan - Doctrine Control Room CI gate

**Parent brief:** `docs/briefs/doctrine-control-room-runtime-wiring.md`

**Architecture:** source-only workflow; ADR-008 and the runtime contract are
unchanged.

**Class:** M

## Acceptance criteria

1. Pull requests and pushes run the dashboard from its committed lockfile on
   the minimum declared Node.js version.
2. CI fails when dashboard lint, TypeScript checking, production build/tests,
   or the moderate dependency audit fails.
3. The dashboard exposes the same named commands locally; a contract test
   proves the source workflow invokes them in fail-fast order.
4. The installer continues shipping only the dashboard-agnostic Doctrine
   workflow to consumer repositories.
5. No workflow publishes, deploys, requests write permissions, or receives
   repository secrets.

## Slice

| # | Change | Evidence | Status |
|---|---|---|---|
| 1 | Add `typecheck` and `audit` dashboard scripts | local script execution | done |
| 2 | Add a pinned, source-only dashboard workflow | rendered contract test | done |
| 3 | Run clean install and all dashboard/Doctrine gates | command output + QA addendum | done |
| 4 | Review permissions, dependency posture, and consumer isolation | G4/G5 addendum | done |

## Loop profile

Ratchet, budget 3. The workflow is a known recipe: each iteration must move the
contract test from a missing gate to a complete gate. Repeated unchanged output
returns the task to this plan.

## Security and rollback

- Workflow permissions remain `contents: read`.
- Action references are pinned to full official commit SHAs.
- No deploy, artifact upload, write token, secret, or external environment is
  introduced.
- `dashboard.yml` is intentionally not copied by `doctrine_install.py`.
- Rollback is deletion of the source-only workflow and the two package scripts;
  runtime behavior is unaffected.

## Known limit

This gate prevents build and advisory drift. It does not satisfy real-browser
keyboard, screen-reader, or five-state interaction QA; that release blocker
remains open until a supported browser backend is available.

## Result

Local G3-G5 evidence is green. The first GitHub-hosted workflow execution
cannot exist until these commits are pushed; this task does not authorize that
external write, so the QA report labels hosted execution as pending rather than
fabricating a CI run.

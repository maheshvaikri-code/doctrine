# Implementation Plan - WorkHawk verification execution wiring

**Brief:** [WorkHawk execution wiring](../briefs/workhawk-execution-wiring.md)
**Design/ADRs:**
[ADR-010](../adr/010-workhawk-verification-execution-lifecycle.md),
[ADR-008](../adr/008-doctrine-control-room-local-bridge.md)
**Class:** L

## Slices

| # | Slice | Role | Files touched | Proven by | Status |
|---|---|---|---|---|---|
| 1 | Freeze scope, state ownership, failures, and lifecycle | Product Owner / Chief Architect | brief, ADR, plan | artifact review + Doctrine lint | done |
| 2 | Add the typed current-verification read operation | Frontend Engineer | API client, source contract | parser/endpoint contract + typecheck | done |
| 3 | Add start locking, current polling, terminal reconciliation, and dirty preflight | Frontend Engineer | Doctrine module | browser accepted/running/terminal/dirty/rejected/poll-error flows | done |
| 4 | Render the authoritative execution record and degraded synchronization state | Frontend / UX Engineer | Doctrine module, styles | semantic metadata and responsive browser assertions | done |
| 5 | Update operating docs and close local gates | Tech Writer / QA Engineer | README, changelog, tests, QA artifacts | lint, typecheck, build/tests, audit, Doctrine lint | done |
| 6 | Run fresh-hat review, security sweep, and hosted gates | Reviewer roles | review, QA, retro | zero open major findings + exact-commit CI | doing |

## Acceptance-criterion trace

| Criterion | Primary proof |
|---|---|
| AC1 one start | browser counts one POST and observes immediate disabled/starting state |
| AC2 current polling | browser request log proves only the current resource repeats while running |
| AC3 terminal reconciliation | browser observes terminal metadata and exactly one post-terminal snapshot refresh |
| AC4 dirty preflight | primary/command actions disabled, visible remediation, zero POST |
| AC5 rejected start | stable error announced and eligible control restored |
| AC6 degraded poll | last record retained, degraded sync visible, dashboard remains live |
| AC7 accessibility/responsive | desktop/dialog/narrow Axe, keyboard, live-region, reduced-motion, overflow assertions |
| AC8 boundary/dependencies | endpoint/source contract, unchanged OpenAPI/bridge, audit, lockfile review |

## Threat sketch

Assets touched: fixed verifier authority, repository eligibility, current job
identity/status, local CPU, and operator trust in gate evidence.

Entry points / untrusted inputs: loopback JSON responses, browser actions,
timing/concurrency between requests, and repository working-tree changes.

Worst plausible abuse: duplicate verification starts consume local resources,
a client invents completion, or a stale/failed poll is presented as current
evidence.

## Risks and rollback points

- Risk: an effect dependency starts overlapping polls -> mitigation: one
  abortable recursive timeout per running job -> rollback: restore bounded full
  snapshot polling.
- Risk: terminal reconciliation overwrites newer execution state -> mitigation:
  keep the bridge as sole state owner and merge only parsed authoritative
  records -> rollback: retain the terminal record without snapshot refresh.
- Risk: disabled controls hide the reason from keyboard/screen-reader users ->
  mitigation: visible preflight text and programmatic descriptions -> rollback:
  permit the action and rely on the bridge rejection.
- Risk: execution metadata overloads the gate panel -> mitigation: compact
  definition list with progressive disclosure at existing breakpoint ->
  rollback: keep lifecycle logic and remove the metadata panel.

## Loop profile

Default Class L profile, ten iterations per acceptance criterion. Each
iteration must advance one named criterion and produce a source, test, or
real-browser evidence delta.

## Deviation log

- 2026-07-26: Graphify output and command are unavailable, so architecture
  tracing uses the documented source-reading fallback. No coverage is claimed
  beyond the inspected WorkHawk client, Doctrine bridge, v1 contract, and
  browser tests.

## Status snapshot

Done: G0-G4 artifacts and gates, pre-change state checkpoint, client
operation, execution lifecycle, operator record, and 12-scenario Chromium
regression suite.
Next: exact-commit QA, security, project review, and checkpoint.
Blocked on: none. External deployment remains intentionally gated.

# Implementation Plan - Doctrine Control Room runtime wiring

**Brief:** `docs/briefs/doctrine-control-room-runtime-wiring.md`

**Design/ADRs:** `docs/adr/008-doctrine-control-room-local-bridge.md`

**Class:** L

## Slices

| # | Slice | Role | Files touched | Proven by (tests) | Status |
|---|---|---|---|---|---|
| 1 | Freeze the v1 snapshot and verification contract | Chief Architect | brief, ADR, plan, OpenAPI contract | `python -m json.tool docs/contracts/doctrine-control-room.openapi.json` | done - contract parses |
| 2 | Serve truthful repository snapshots over loopback | Backend Engineer | `tools/doctrine_dashboard.py`, bridge tests | snapshot, origin, empty/degraded-state tests | done - 9 bridge tests pass |
| 3 | Add bounded asynchronous verification | Backend Engineer | bridge tool and tests | accepted, concurrent rejection, completion/failure tests | done - job/concurrency/output-bound tests pass |
| 4 | Replace prototype state/actions with the API client | Frontend Engineer | dashboard client, component, styles, UI tests | build, lint, rendered contract tests | doing |
| 5 | Document operation and verify the complete surface | Tech Writer / QA | README, changelog, QA report | clean install, audits, all repository gates | todo |
| 6 | Fresh-hat code, security, and scope review | Review roles | review and retrospective artifacts | zero open blocker/major findings | todo |

## Threat sketch

Assets touched: repository metadata, verifier execution, local CPU, captured
gate output.

Entry points / untrusted inputs: HTTP origin/header/path/body and requests from
any local browser tab.

Worst plausible abuse: cross-site triggering of repeated verification, metadata
exfiltration, command/path injection, or unbounded output/resource consumption.

## Risks & rollback points

- Risk: local bridge becomes a remote shell -> mitigation: one fixed action,
  no command/path input, no shell -> rollback: remove the POST endpoint while
  retaining snapshots.
- Risk: UI mistakes stale cache for current evidence -> mitigation: every run is
  tied to a commit and stale status is explicit -> rollback: disable cache load.
- Risk: long verification blocks HTTP -> mitigation: one background worker and
  polling -> rollback: retain read-only snapshot mode.
- Risk: dashboard build cannot reach the bridge -> mitigation: fetch only in the
  browser after hydration -> rollback: retain the accessible connection state.

## Loop profile

Default profile, budget 10 iterations per acceptance criterion. Each iteration
must change one hypothesis and produce a test or observable contract delta.
Three edits to the same file without a test delta return the work to this plan.

## Deviation log

- 2026-07-25: none.

## Status snapshot

Done (with evidence): task checkpoint 23 records the start boundary; G0 and G1
artifacts drafted.

Next: wire the typed browser client and derive all five interface states from
the bridge contract.

Blocked on: none. External publishing remains gated.

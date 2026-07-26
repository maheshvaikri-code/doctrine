# Implementation Plan - WorkHawk application extraction

**Brief:** [WorkHawk extraction](../briefs/workhawk-extraction.md)
**Design/ADRs:** [ADR-009](../adr/009-workhawk-application-boundary.md),
[ADR-008](../adr/008-doctrine-control-room-local-bridge.md)
**Class:** L

## Slices

| # | Slice | Role | Files touched | Proven by | Status |
|---|---|---|---|---|---|
| 1 | Record product boundary, scope, threat model, and one-way dependency | Product Owner / Chief Architect | brief, ADR, plan | artifact review + doctrine lint | done |
| 2 | Move the tracked application to `workhawk/` without duplication | DevOps / Frontend Engineer | application tree, Sites metadata | Git path assertions + build | done |
| 3 | Rebrand the shell and add a truthful typed module registry | Frontend / Interop Engineer | metadata, shell, registry, styles | rendered contract + browser states | done |
| 4 | Rewire bridge language, CI, tests, and operating documentation | Interop / DevOps Engineer | bridge, OpenAPI, workflow, tests, READMEs | Python + Node contract tests | done |
| 5 | Run review, security, browser, OS, and repository gates | Reviewer roles | review and QA artifacts | lint, types, tests, audit, Chromium, Doctrine verify | done |
| 6 | Checkpoint release evidence without publishing and capture lessons | Release Manager / Project Reviewer | changelog, retro, state | clean pushed commit + hosted gates | done |
| 7 | Preserve and wire the human-supplied official WorkHawk raster | Frontend / QA Engineer | public asset, shell mark, tests, docs | render + production HTTP + hosted Chromium | done |
| 8 | Improve truthful metric, gate-score, and evidence-trend visualization | Frontend / QA Engineer | Doctrine module, styles, browser and render contracts | semantic meter/progress/chart assertions + hosted Chromium | doing |

## Acceptance-criterion trace

| Criterion | Primary proof |
|---|---|
| AC1 application boundary | rendered contract checks tracked `workhawk/` and absent tracked `dashboard/` |
| AC2 product/module identity | server-rendered metadata and shell assertions |
| AC3 live Doctrine flow | bridge tests, API parsing contract, production/browser verification action |
| AC4 truthful future modules | registry parser/contract plus visible unavailable-state assertions |
| AC5 five accessible states | hosted Chromium suite and Axe |
| AC6 source CI | workflow contract plus Windows/Ubuntu/Chromium hosted run |
| AC7 Windows assets | real production-server HTTP regression |
| AC8 consumer isolation | installer/workflow contract assertion |
| AC9 official brand asset | source-presence, server-render, production HTTP, and hosted browser assertions |
| AC10 evidence visualization | semantic meter/progress/chart browser assertions against the live fixture |

## Threat sketch

Assets touched: local repository evidence, verification authority, frontend
module identity, CI provenance.

Entry points / untrusted inputs: loopback HTTP headers and JSON, API responses,
environment-configured base URL, module registry declarations, Git metadata.

Worst plausible abuse: WorkHawk gains an arbitrary execution surface, accepts
unbounded or malformed module/API data, or presents a disconnected module as
trusted and actionable.

## Risks and rollback points

- Risk: path migration misses a workflow or test reference -> mitigation:
  repository-wide tracked-reference scan and contract test -> rollback:
  revert the extraction commit.
- Risk: rename changes accessible names and breaks keyboard/browser locators ->
  mitigation: update user-visible assertions deliberately and run all seven
  browser scenarios -> rollback: restore the prior copy and metadata.
- Risk: new registry implies integrations that do not exist -> mitigation:
  stable typed declarations, explicit unavailable state, no action URLs ->
  rollback: remove registry UI while retaining the application boundary.
- Risk: Sites project creation or deployment causes external state -> mitigation:
  preserve local hosting metadata only; do not create/deploy without human
  approval.

## Loop profile

Default, budget 10 per criterion. Each iteration must advance a named
acceptance criterion; repeated path or browser failures return to this plan.

## Deviation log

- The existing local port `3003` was occupied, which initially prevented the
  Playwright web server from starting. The E2E configuration now validates an
  optional `WORKHAWK_E2E_PORT` override while retaining `3003` as the CI and
  product default.
- The in-application browser controller exposed no installed browser backend,
  and the local Playwright Chromium binary was absent. Hosted CI remains the
  real-browser authority because its workflow installs Chromium explicitly.
- The moved Sites build plug-in matched the repository's broad `build/` ignore
  rule. It was force-added as the exact tracked migration target and a contract
  test now proves that a fresh checkout contains it.
- The first hosted Chromium run passed six scenarios but failed the live-state
  scenario because its non-exact WorkHawk locator matched the brand, fixture
  activity, and footer. The locator was narrowed and exact-commit run
  `30189259820` passed all seven scenarios.

## Status snapshot

Done: all seven slices. Exact commit `751e284` passed hosted WorkHawk Windows,
Ubuntu, six production tests per OS, and seven-scenario Chromium jobs plus
Doctrine's Windows/Ubuntu and Python 3.11/3.12 matrix. Review, QA, security, and
retrospective evidence are recorded. Blocked on: none. External publishing
remains intentionally out of scope.

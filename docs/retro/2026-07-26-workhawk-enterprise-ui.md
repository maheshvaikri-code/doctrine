# Retrospective - WorkHawk enterprise UI - 2026-07-26

## Facts

Shipped to `main`: a cohesive enterprise visual system, searchable command
palette, exact KPI status/progress, four-gate meter, evidence-derived SVG trend,
official brand mark, narrow-layout hardening, and desktop/dialog/mobile
accessibility assertions.

Application commits: `926757f`, `8b1e369`, `20c551d`, and `ae04e20`. Exact
application commit `ae04e20` passed Windows, Ubuntu, seven hosted Chromium
scenarios, and Doctrine's four OS/Python combinations. No dependency, API,
deployment, tag, package, or release changed.

## What worked

- Starting with explicit “evidence only” criteria kept richer visuals from
  turning into invented enterprise metrics.
- Native progress and meter semantics made the graphics independently
  inspectable instead of relying on color.
- One SVG function serves every range using the returned series, so visual and
  accessible values cannot drift into separate fixtures.
- Hosted Chromium rejected stale focus evidence immediately and validated the
  corrected searchable interaction.
- A separate enterprise-UI brief kept visual refinement distinct from the
  WorkHawk/Doctrine application-boundary ADR.

## What failed or hurt

- The first hosted visualization run retained the old command-focus assertion
  after the palette's focus target intentionally changed to search.
- The initial narrow scenario tested navigation and reduced motion but did not
  run Axe or assert horizontal width.
- The first chart assertion proved only a label prefix, not the exact total and
  series promised by the brief.
- Local Playwright lacked a browser executable and the interactive browser
  connector exposed no backend, leaving hosted Chromium as the authority.

## Root causes

### Hosted focus assertion lagged behind behavior

The launcher gained search -> the search field became the correct first focus
target -> the old scenario expected the first command -> source/build tests do
not execute focus -> hosted Chromium rejected the mismatch. Root cause:
feature/test synchronization gap. The correction tests search, wrap,
filtering, empty state, restoration, and Axe as one behavior.

### Acceptance proof was initially too broad

The brief named exact series, zero results, and no overflow -> first assertions
checked chart presence, one filter, and narrow navigation -> those are adjacent
signals but not the named outcomes -> reviewer trace exposed the gaps -> exact
assertions were added before sign-off. Root cause: acceptance-to-test
specificity gap.

## Doctrine and tooling amendments

| # | Amendment | Target | Class-S change filed? |
|---|---|---|---|
| 1 | Assert exact evidence-series accessible names, not chart presence alone. | WorkHawk browser QA | no; implemented |
| 2 | Test both matching and zero-result command searches in the focus-loop scenario. | WorkHawk browser QA | no; implemented |
| 3 | Include Axe and width overflow in the narrow viewport gate. | WorkHawk browser QA | no; implemented |
| 4 | Keep visual refinement in a dedicated brief when the application-boundary task is already complete. | project artifact practice | no doctrine-law change |

## Honest negative findings worth remembering

- “Enterprise UI” here means production-quality local interaction and evidence
  presentation, not authenticated multi-user enterprise operations.
- WorkHawk still has one live module: Doctrine. MAPLE, STIX, and Trust remain
  honest registry seams.
- The UI has no editor, PTY, capability broker, durable event backend, or
  public deployment.
- Automated browser/Axe coverage does not equal manual screen-reader,
  usability, or performance certification.

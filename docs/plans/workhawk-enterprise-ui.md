# Implementation Plan - WorkHawk enterprise UI

**Brief:** [WorkHawk enterprise UI](../briefs/workhawk-enterprise-ui.md)
**Class:** M

## Slices

| # | Slice | Role | Primary proof | Status |
|---|---|---|---|---|
| 1 | Record the evidence-only design boundary and acceptance criteria | Product Owner / UX Designer | brief and Doctrine lint | done |
| 2 | Refine visual tokens, surfaces, responsive KPI cards, and panel hierarchy | UX Designer / Frontend Engineer | production render at desktop and mobile | done |
| 3 | Implement searchable action palette and keyboard behavior | Frontend Engineer | filtered-result and focus-loop browser assertions | done |
| 4 | Implement native progress, gate meter, and SVG evidence chart | Frontend Engineer | semantic browser assertions against fixture values | done |
| 5 | Add desktop/mobile accessibility and source regression contracts | QA Engineer | Axe, rendered source tests, reduced-motion checks | doing |
| 6 | Run repository, security, and hosted gates; record evidence | Reviewer roles | local commands plus exact-commit CI | pending |

## Acceptance-criterion trace

| Criterion | Proof |
|---|---|
| AC1 action search | browser query filtering, empty-result, focus-loop, and restoration scenario |
| AC2 truthful KPIs | source contract plus progressbar values in the live browser fixture |
| AC3 gate meter | browser `meter` assertion with exact `aria-valuenow` |
| AC4 evidence chart | accessible chart-name assertion containing range, total, and series |
| AC5 responsive accessibility | desktop/dialog/mobile Axe scans, width assertion, reduced-motion scenario |
| AC6 dependency/source ownership | package/source contract and dependency audit |
| AC7 production assets | build and production HTTP regression suite |

## Risks and rollback points

- Search filtering could weaken the existing focus trap when the result list
  changes. Keep the search input and enabled buttons in one live focus-loop
  query and cover filtered results in Chromium.
- SVG animation could hide information from reduced-motion users. Keep the
  complete geometry in the rendered DOM, collapse duration through
  `useReducedMotion`, and place the exact series in the chart's accessible
  name.
- Smaller analytical labels can fail contrast at mobile scale. Run Axe at
  desktop and 390-pixel widths; treat a contrast finding as a release failure.
- Visual research could introduce a second dependency or copied registry
  source. Keep all components local and preserve Motion as the only animation
  package.

## Loop profile

Default Class M budget: ten iterations per criterion. A visual iteration must
advance a named criterion and be followed by a build, semantic assertion, or
real-browser observation.

## Status snapshot

Implementation and local real-browser review are in progress. External
deployment remains outside scope.

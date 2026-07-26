# Project Brief - WorkHawk enterprise UI

**Date:** 2026-07-26
**Class:** M - refines the WorkHawk visual system, component behavior,
accessibility contracts, and browser QA without changing the Doctrine API
**Requested by:** human

## Problem

WorkHawk has the correct application boundary and live Doctrine module, but
its analytical surfaces need a more legible enterprise hierarchy. The command
launcher looked like search without supporting search, repository trends were
decorative bars, and top-level metrics did not carry their health context.
The interface should feel production-grade while remaining evidence-driven,
accessible, locally owned, and calm under repeated operational use.

## Scope

- **In:** Apply a cohesive navy, blue, neutral, and restrained health-color
  system to the existing WorkHawk shell.
- **In:** Turn the command launcher into a keyboard-first searchable action
  palette with filtered and empty results, focus containment, and restoration.
- **In:** Add exact status and native progress semantics to repository KPI
  cards where the Doctrine snapshot supplies a meaningful denominator.
- **In:** Replace decorative commit bars with an owned, accessible SVG
  area/line chart generated from the selected Doctrine evidence series.
- **In:** Add an accessible verification meter calculated from the four
  required gates.
- **In:** Retain Motion as the single runtime and honor reduced-motion
  preferences.
- **In:** Preserve the exact human-supplied WorkHawk raster.
- **Non-goals:** Add Anime.js, copy Kokonut/Bklit/Motion+ registry source,
  fabricate portfolio data, change the Doctrine API, connect unavailable
  modules, publish WorkHawk, or build editor/terminal surfaces.

## Acceptance criteria

1. Given the command launcher, when an operator types a query, then actions
   filter by their labels and descriptions, a zero-result state is explicit,
   and keyboard focus remains inside the dialog until it closes.
2. Given a live snapshot, when the metric cards render, then every card pairs
   its exact value with a textual status and only activation/gates expose
   progress because those fields have truthful denominators.
3. Given verification evidence, when the gate panel renders, then its score is
   a native ARIA meter whose value equals passed gates divided by four.
4. Given a selected evidence range, when its chart renders, then the chart
   geometry and accessible name are derived from the exact returned series,
   including total and individual values.
5. Given desktop or a 390-pixel viewport, when WorkHawk is scanned for WCAG
   A/AA rules and exercised by keyboard, then the live surface and command
   dialog have zero automated violations, no horizontal overflow, and reduced
   motion remains effective.
6. Given dependency and source review, when the implementation is inspected,
   then Motion remains the sole animation runtime and no external premium
   component source has been copied.
7. Given a fresh production build, when the app and official logo are fetched,
   then all rendered assets return successful non-empty responses.

## Constraints

- No new runtime or development dependency.
- No lockfile graph change.
- All operational values must come from the existing Doctrine v1 snapshot.
- The application remains local-only and bound to the established loopback
  bridge trust boundary.
- The original logo remains unmodified at
  `workhawk/public/workhawk-logo.png`.

## Design direction

- Motion supplies the existing React animation primitives, focus-preserving
  presence transitions, and reduced-motion integration.
- Kokonut UI informs the compact searchable action pattern and tactile
  component spacing.
- Bklit informs dense KPI composition and analytical chart hierarchy.
- Anime.js is research input only; installing a second animation engine would
  duplicate the runtime already in the bundle.
- All shipped component source is repository-owned.

**Human confirmed:** yes - the request explicitly asks to use the strongest
ideas from the supplied references and produce an enterprise-level WorkHawk
interface.

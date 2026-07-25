# QA — Doctrine Control Room

**Date:** 2026-07-25
**Status:** Local prototype verified; browser visual QA unavailable

## Mechanical evidence

- `npm run build` — pass
- `npm run lint` — pass
- `npm test` — 2 tests passed, 0 failed
- `npm audit --omit=dev --audit-level=high` — 0 vulnerabilities
- Local HTTP smoke — status 200; product title and hero content present

The server-rendering test asserts product metadata, primary content, public-clean
execution terminology, and removal of starter-preview markers. The product
contract test asserts all five UI states, modal semantics, alert/live regions,
keyboard handling, focus treatment, reduced-motion support, and dependency scope.

## Manual coverage represented in code

- Responsive layouts at desktop, tablet, and compact breakpoints
- Skip link and visible focus treatment
- Semantic navigation, tables, progress elements, status and alert regions
- Command-palette focus trap, Escape handling, and focus restoration
- Reduced-motion styles and Motion runtime guard

## Degraded checks

The in-app browser was unavailable, so no screenshot comparison, real pointer
interaction, keyboard walk, or screen-reader pass was performed. Those checks
remain required before a production release.

The generated social-preview PNG failed saved-file inspection twice because its
typography disappeared after export. No `og:image` was shipped.

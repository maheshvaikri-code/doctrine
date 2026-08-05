# Retrospective - WorkHawk verification execution wiring - 2026-07-26

## Facts

Implemented on local `main`: typed current-verification reads, an immediate
start lock, ready/connected/clean preflight, one-resource recursive polling,
one terminal snapshot reconciliation, a semantic execution record, degraded
sync preservation, and modal isolation.

Implementation commit: `0a459c956e9dc0ae492d400e23b3a9356482b54c`.
Exact-commit evidence: lint and typecheck pass, six production tests pass,
audit reports zero vulnerabilities, 12 Chromium scenarios pass, 186 Doctrine
tests pass, Ruff passes, and the 28-checkpoint state chain verifies. No
dependency, lockfile, bridge, OpenAPI, deployment, tag, or published release
changed.

## What worked

- Treating the bridge as the sole state owner kept the UI from inventing gate
  progression or process output.
- Request counters in browser fixtures proved resource use and exact one-POST
  behavior, not merely the final screen.
- The dedicated current resource removed repeated full repository collection
  while a job runs.
- A visible preflight sentence lets disabled controls explain dirty, loading,
  and running states without requiring a failed request.
- Axe found both low-contrast metadata and incomplete modal isolation before
  sign-off.
- Exact-commit execution repeated both the WorkHawk and Doctrine gates after
  the feature commit was frozen.

## What failed or hurt

- The first implementation guarded the primary live action but overlooked that
  the global command palette exists during loading, error, and empty states.
- Initial modal behavior trapped keyboard focus but did not make the dashboard
  behind it inert to assistive technology.
- The first local browser attempt targeted port 3003, where an unrelated stale
  404 service prevented Playwright's managed server from becoming ready.
- The expected Playwright browser binary was absent, so the suite could not
  execute until the test browser was installed to the machine cache.
- Graphify was unavailable, requiring the documented source-reading fallback.

## Root causes

### Global launcher bypassed readiness

The primary action only renders with a live snapshot -> eligibility logic was
designed around that location -> the command palette is global and survives
loading/error/empty states -> its command inherited only dirty/running guards
-> G4 found a pre-snapshot POST path. Root cause: capability eligibility was
modeled per button instead of once for every invocation surface.

### Modal semantics lagged focus behavior

The focus loop worked -> `aria-modal` was assumed sufficient -> background
regions remained in the accessibility tree -> dialog-time Axe evaluated
obscured controls -> inert/ARIA isolation fixed the ownership boundary. Root
cause: modal verification emphasized keyboard containment without separately
testing accessibility-tree containment.

### Local browser environment was not preflighted

The default port was reused -> a stale service answered 404 -> the managed
server waited instead of starting -> a fresh port exposed the next missing
prerequisite, the Playwright browser binary. Root cause: environment readiness
was discovered by the expensive full suite instead of a cheap port/browser
preflight.

## Doctrine and tooling amendments

| # | Amendment | Target | Class-S change filed? |
|---|---|---|---|
| 1 | Derive one capability-eligibility value and apply it to every primary, palette, keyboard, and imperative invocation path. | WorkHawk UI review checklist | no; implemented and reviewed |
| 2 | For modal surfaces, test both focus containment and background inertness with Axe. | WorkHawk browser QA | no; implemented |
| 3 | Count network operations in execution-flow browser tests so polling and mutation claims are falsifiable. | WorkHawk browser QA | no; implemented |
| 4 | Preflight the chosen E2E port and Playwright browser cache before a full local run. | future WorkHawk test-runner improvement | no; follow-up candidate |

## Honest negative findings worth remembering

- WorkHawk still runs one fixed Doctrine operation; it is not a general shell,
  terminal, editor runtime, or capability broker.
- The execution record is the current job only. There is no durable history,
  cancellation, log stream, or signed export.
- MAPLE, STIX, and Trust remain honest unavailable seams.
- Local Chromium and automated Axe do not equal manual screen-reader,
  usability, performance, Windows desktop-shell, or multi-user certification.
- No hosted CI, external push, deployment, tag, or publication is claimed for
  this task.

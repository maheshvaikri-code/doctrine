# Project Brief - WorkHawk application extraction

**Date:** 2026-07-25
**Class:** L - creates a new top-level application boundary and changes the
repository's frontend, CI, documentation, and integration ownership
**Requested by:** human

## Problem

The existing Doctrine Control Room proves a high-quality operational UI and a
safe local Doctrine adapter, but its location and identity incorrectly imply
that the enterprise workbench belongs to Doctrine. Operators need a separately
owned WorkHawk application that can consume Doctrine now and later compose
MAPLE, STIX, Trust, editor, terminal, dashboard, and control-room capabilities
without making Doctrine depend on the frontend.

## Scope

- **In:** Move the existing tracked web application from `dashboard/` to the
  top-level `workhawk/` application boundary without retaining a duplicate.
- **In:** Present WorkHawk as the agentic engineering workbench and Doctrine as
  its currently connected governance module.
- **In:** Add a typed module registry with stable, brand-neutral module IDs and
  truthful connected/unavailable states.
- **In:** Preserve the versioned Doctrine v1 loopback contract, exact-origin
  policy, fixed verification operation, five UI states, production launcher,
  accessibility behavior, and Windows asset repair.
- **In:** Rewire source CI, browser QA, tests, operating documentation, package
  metadata, and Sites build metadata to the new application path.
- **In:** Keep Doctrine independently installable and headless; its consumer
  installer does not copy WorkHawk.
- **Non-goals:** Build a code editor, PTY terminal, MAPLE runtime connector,
  STIX policy connector, Trust connector, authentication, multi-repository
  service, remote execution, public deployment, or external release.
- **Deferred:** OpenHawk-hosted distribution, editor and terminal surfaces,
  capability broker, durable event ledger, authenticated enterprise access,
  and real MAPLE/STIX/Trust adapters.

## Acceptance criteria

1. Given a fresh checkout, when tracked files are inspected, then the
   application exists under `workhawk/`, no tracked `dashboard/` application
   remains, and the package identifies itself as WorkHawk.
2. Given WorkHawk is rendered, when an operator opens it, then the product
   metadata and shell identify WorkHawk while the active governance view
   identifies Doctrine as a connected module.
3. Given the Doctrine bridge is available, when WorkHawk loads and verification
   is requested, then the existing v1 snapshot and fixed verifier flow complete
   without a contract or security-boundary regression.
4. Given MAPLE, STIX, or Trust has no connector, when the module surface renders,
   then each is visibly unavailable and exposes no fabricated action or metric.
5. Given loading, empty, partial, bridge-error, and live data, when each state is
   rendered in hosted Chromium, then it remains keyboard operable and passes
   the existing automated WCAG A/AA checks.
6. Given Windows or Ubuntu CI, when WorkHawk gates run from the lockfile, then
   lint, typecheck, production build/tests, dependency audit, and Chromium QA
   pass from `workhawk/`.
7. Given a Windows production preview, when every rendered CSS and JavaScript
   URL is fetched, then every asset returns `200` with the expected content
   type and no host-absolute font URL.
8. Given a Doctrine consumer install, when its manifest and CI are inspected,
   then WorkHawk source and its source-only workflow are not copied into the
   consumer.
9. Given the human-supplied WorkHawk logo, when the application is built from a
   fresh checkout, then the exact raster is served by the production server and
   its hawk/W mark identifies the compact shell without regenerating the logo.
10. Given live Doctrine evidence, when an operator reads the overview, then
    health/status, gate completion, and evidence trend are expressed with
    accessible native semantics and values derived only from the current
    snapshot.

## Constraints

- Python 3.11+ and Node.js 22.13+ remain supported.
- No new dependency and no lockfile dependency upgrade in this extraction.
- The bridge remains bound to `127.0.0.1`; the default UI port remains `3003`.
- WorkHawk remains local-only in this task. Creating a hosted site, public
  domain, tag, package, or release requires separate human approval.
- Historical Doctrine Control Room evidence remains historically named; new
  records use WorkHawk terminology.

## Assumptions

- “Complete wiring” in this slice means complete migration and live Doctrine
  integration plus honest extension points for the other named modules. It
  does not mean simulating connectors whose repositories or contracts are not
  present here.
- `openhawk.workbench` is the stable internal application identity;
  `WorkHawk` is a replaceable frontend display brand.
- The current visual language is retained; this task changes ownership and
  information architecture rather than redesigning the workbench.

## Open questions

- None blocking for the extraction. Public branding and OpenHawk distribution
  are launch decisions, intentionally outside this task.

**Human confirmed:** yes - the instruction explicitly requested bundling the
existing UI as WorkHawk in a separate folder and completing its wiring.

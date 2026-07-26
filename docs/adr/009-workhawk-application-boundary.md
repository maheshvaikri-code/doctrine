# ADR-009: Extract WorkHawk as the frontend application boundary

**Date:** 2026-07-25
**Status:** accepted
**Deciders:** Chief Architect; CISO boundary review required at G5

## Context

The Doctrine Control Room began as an isolated proof that repository governance
could be rendered truthfully and operated through a bounded loopback bridge.
The intended product has since become broader: an agentic engineering workbench
that will compose Doctrine, MAPLE, STIX, Trust, editor, terminal, dashboard, and
human control surfaces. Keeping that application named and located as a
Doctrine dashboard would invert ownership and pressure Doctrine into becoming
an enterprise frontend.

## Decision

We will move the existing web application to `workhawk/` and identify it as
WorkHawk, internal ID `openhawk.workbench`. WorkHawk owns its product shell,
module registry, UI, and frontend CI. Doctrine remains a headless governance and
gating system that exposes its existing versioned loopback API; WorkHawk
consumes that API through a Doctrine adapter. Dependency direction is strictly
`WorkHawk -> Doctrine API`. No Doctrine core module imports WorkHawk.

The module registry uses stable IDs (`doctrine`, `maple`, `stix`, `trust`) and
declares capabilities and availability. Only Doctrine is connected in this
repository. Other modules remain visibly unavailable until real versioned
contracts and adapters exist.

The local Doctrine bridge remains in `tools/doctrine_dashboard.py` for package
compatibility in this change. Its human-facing description is generalized to a
Doctrine local operations bridge for WorkHawk and compatible clients. The v1
HTTP paths and security controls do not change.

## Data flow

```text
WorkHawk shell
  |
  | selects Doctrine module
  v
WorkHawk Doctrine adapter
  |
  | versioned loopback HTTP v1
  v
Doctrine local operations bridge
  |-- reads bounded repository/Git/state evidence
  `-- runs only tools/doctrine_verify.py
```

Failure is contained by the boundary: when the Doctrine bridge is unavailable,
the Doctrine module reports an actionable error while the WorkHawk shell and
module registry remain renderable. An unavailable future module exposes no
actions.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Extract one WorkHawk application and consume Doctrine by contract (chosen) | Correct ownership, one UI source, Doctrine stays headless, future modules have a clear seam | Cross-cutting path and naming migration | - |
| Copy the dashboard and keep both UIs | Lowest immediate migration risk | Two sources drift, duplicate security fixes, ambiguous product ownership | Violates single-source ownership |
| Grow Doctrine Control Room into the full workbench | No folder migration | Doctrine becomes coupled to editor/runtime/identity concerns outside its governance domain | Wrong dependency direction |
| Embed independent module UIs with iframes or micro-frontends now | Strong runtime isolation | Accessibility, identity, theming, navigation, and contract complexity before multiple real modules exist | Speculative infrastructure |
| Move the application directly into the external OpenHawk repository | Places the UI near its eventual platform | Splits the current tested vertical slice before a distribution and compatibility contract is agreed | Human requested a separate folder in this repository first |

## Capacity and compatibility

- One local operator, one repository, and one active verification job.
- Snapshot polling remains below two requests per second.
- The Doctrine HTTP API remains v1 and additive; this extraction is not an API
  major version.
- Source CI continues on Windows and Ubuntu with one hosted Chromium job.

## Security sketch

- **Assets:** local repository metadata, verification output, filesystem
  context, and the authority to run Doctrine's fixed verifier.
- **Entry points:** WorkHawk origin, bridge paths and headers, JSON mutation
  body, module metadata, and future module adapters.
- **Worst plausible abuse:** a frontend or future module bypasses the broker
  boundary to execute arbitrary commands or misrepresents disconnected data as
  trusted evidence.
- **Controls:** loopback bind, exact origin allowlist, fixed verifier path,
  bounded JSON/output/time, clean-tree attribution, typed frontend parsing,
  truthful unavailable states, and no arbitrary command/module endpoint.

## Consequences

- Positive: WorkHawk can evolve into the broader workbench without changing
  Doctrine's domain or forcing consumer repositories to ship the UI.
- Positive: Existing Doctrine behavior, browser QA, and Windows compatibility
  remain protected by renamed rather than recreated tests.
- Negative: This source repository temporarily hosts an application whose
  eventual distribution may belong to OpenHawk.
- Negative: The legacy Python module and command retain “dashboard” in their
  internal names until a separately planned compatibility migration.
- Invalidation triggers: a signed OpenHawk distribution contract, an
  authenticated multi-user backend, a real second module connector, or a need
  for module-contributed executable UI reopens the packaging decision.

This ADR supersedes ADR-007 for frontend ownership and naming. ADR-008 remains
authoritative for the local bridge security design.

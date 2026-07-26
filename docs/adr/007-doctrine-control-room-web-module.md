# ADR-007 — Doctrine Control Room web module

**Status:** Superseded by ADR-009 for frontend ownership and naming
**Date:** 2026-07-25

## Context

Doctrine has strong repository-local mechanics but no human portfolio surface.
An enterprise operator needs a concise view of gate posture, evidence integrity,
exceptions, agent execution, and release readiness without making that UI the
source of truth.

## Decision

Add an isolated `dashboard/` React module. The CLI, CI gates, and evidence
artifacts remain authoritative; the dashboard observes, explains, and initiates
prototype actions.

The visual system uses an obsidian navigation shell, warm analytical canvas,
cobalt evidence signals, and acid-lime live-state accents. It borrows principles,
not source code, from the supplied design references.

Portfolio-private systems are represented by public-clean capability aliases.
Every visible operational value is labeled prototype data.

## Dependency interview

### Motion 12.42.2

- **Need:** accessible React entry/state/layout animation and reduced-motion
  integration would exceed a small owned helper.
- **Health:** current maintained release; widely deployed.
- **Weight:** one animation runtime only; Anime.js was rejected as overlapping.
- **License:** MIT.
- **Security:** included in the zero-finding runtime audit.

### Lucide React 1.26.0

- **Need:** a consistent accessible icon vocabulary; hand-authored SVG assets
  would be larger, inconsistent, and harder to maintain.
- **Health:** actively maintained and broadly scrutinized.
- **Weight:** tree-shaken icon imports only.
- **License:** ISC.
- **Security:** included in the zero-finding runtime audit.

Patched `postcss` and `sharp` overrides are pinned because the latest stable
Next.js package currently resolves vulnerable transitive builds. Compatibility
is guarded by the production build and server-rendering tests.

## Consequences

- The dashboard can evolve without changing Doctrine’s Python distribution.
- Production data and mutation require a future typed evidence API, identity,
  authorization, and audit design.
- The module is not externally published by this change.

---
integration: openguide
upstream: <confirm — the user's OpenGuide repo>
license: <confirm>
pinned_version: <confirm>
discipline: behavior-engineering
status: proposed
drafted: 2026-07-20
---

# OpenGuide — Integration (proposed)

> **Proposed integration shim.** The *fit, routing, and boundary* are grounded in
> what Doctrine provides and what OpenGuide does; the **upstream URL, license,
> pinned version, and exact API/contract format are `<confirm>` placeholders** the
> human fills in before wiring live. Non-vendored. (The integrations index already
> names OpenGuide/GuidanceGrid as a taxonomy neighbor of ponytail — this promotes
> that reference to a real integration point.)

## What it is

OpenGuide is the portfolio's **behavioral control plane**: an Open Behavioral
Contract (OBC) spec plus the **GuidanceGrid** runtime, with **tiered enforcement
(T0–T3)** across open and closed models. It governs an agent's *trajectory and
behavior* — how it acts — as a runtime contract, not a prompt.

## Why it composes with Doctrine (the fit)

Doctrine's behavioral guidance is **prose**: role cards, skills, `skills/ponytail.md`
(brevity), and `skills/engagement-engineering.md` (how the agent engages) tell the
agent how to behave, and reviewers check after the fact. OpenGuide makes those
**runtime-enforced behavioral contracts**. The layers:

- **Doctrine authors the behavior** — a role *is* a persona; ponytail and
  engagement-engineering *are* behavioral disciplines.
- **OpenGuide enforces it** — role personas compile to **OBC contracts**;
  GuidanceGrid holds the agent's trajectory to them at runtime.
- Sits **beside ponytail** in Behavior Engineering: GuidanceGrid governs general
  behavioral conformance; ponytail governs code-brevity behavior specifically.

## Doctrine wiring (to build once confirmed)

- **Role personas → OBC contracts:** each `roles/*.md` persona (mission, authority,
  anti-patterns) maps to an OBC the runtime enforces — a reviewer role's "physically
  cannot edit code" becomes a behavioral contract, not just a tool restriction.
- **Engagement + brevity as contracts:** `skills/engagement-engineering.md` and
  `skills/ponytail.md` become T-tiered OBCs rather than prose the agent may drift from.
- **Tiers ↔ task classes / autonomy:** T0–T3 map to the S/M/L/HOTFIX classes and the
  autonomy-resolution ladder — heavier classes get stricter behavioral contracts.

## Boundary (binding)

**Doctrine authors behavior; OpenGuide enforces trajectory; the gates still
decide.** OpenGuide shapes *how* the agent works within a task — it does not decide
*what* ships (that is G0–G7) nor gate the concrete action (that is
`integrations/stix.md`). Three orthogonal planes: **process** (Doctrine gates),
**behavior** (OpenGuide), **action** (STIX).

## Taxonomy placement

**Behavior Engineering** — beside `skills/ponytail.md`. The runtime enforcer of the
behavioral disciplines Doctrine authors in prose.

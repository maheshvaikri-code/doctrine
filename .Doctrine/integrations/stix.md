---
integration: stix
upstream: <confirm — the user's STIX repo (local: D:\Research\STIX)>
license: <confirm>
pinned_version: <confirm>
discipline: action-enforcement
status: proposed
drafted: 2026-07-20
---

# STIX — Integration (proposed)

> **Proposed integration shim.** The *fit, routing, and boundary* below are
> grounded in what Doctrine provides and what STIX does. The **upstream URL,
> license, pinned version, and exact API are placeholders (`<confirm>`)** the
> human fills in before this is wired live — nothing here is verified against a
> running STIX yet. Non-vendored, like every integration.

## What it is

STIX is the portfolio's **agent-action enforcement** layer: it intercepts an
agent's *actual actions* (tool calls, commands, external effects) and returns
**ALLOW / DENY / QUARANTINE** with a **cryptographic proof** and a
**human-in-the-loop** path. Core enforces; Fabric governs the policy.

## Why it composes with Doctrine (the fit)

Doctrine's **§5** ("escalate before any irreversible or external action") and the
Non-Negotiables are **process** enforcement — the agent is *asked* to comply, and
compliance is verified after the fact by reviewers. STIX makes the same boundary
**physical**: the action is gated at the point of execution, not by the agent's
good behavior. The two are layers, not rivals:

- **Doctrine decides** *which* actions need a gate (§5: delete data, force-push,
  publish/release, spend, add a dependency, disable a check).
- **STIX enforces** that gate at the action boundary — a **DENY/QUARANTINE is the
  §5 escalation made unbypassable**, and the human remains root via HITL.
- The **cryptographic proof** each decision emits becomes audit evidence — it
  feeds `domains/auditing.md` (immutable evidence + chain-of-custody) and, if
  adopted, the Contegrity provenance plane (`integrations/contegrity.md`).

## Doctrine wiring (to build once confirmed)

- **Map §5 categories → STIX policies:** each §5 trigger and each Non-Negotiable
  that names a forbidden action (never commit secrets, never delete/skip a failing
  test, never move money without authz — see the domain packs) becomes a STIX
  policy rule.
- **Gold-build / release** (`standards/merge-and-promotion.md`): promotion actions
  become STIX-gated with a proof attached to the gold record.
- **Domain non-negotiables** that are *action* rules (finance: no money movement
  without idempotency+authz; logistics: hold-not-release for sanctioned parties;
  healthcare: no PHI to an un-BAA'd service) are natural STIX policies.

## Boundary (binding)

**Doctrine decides, STIX enforces, the human is root.** STIX does not replace the
gates or the reviewers — it makes the §5 floor unbypassable at runtime. The state
plane stays the durable decision truth; STIX proofs are the *action* truth.

## Taxonomy placement

**Action Enforcement** — the runtime layer beneath §5. Complements (does not
overlap) the *process* gates (G0–G7) and the *behavioral* plane
(`integrations/openguide.md`): process decides, behavior shapes trajectory, STIX
gates the concrete action.

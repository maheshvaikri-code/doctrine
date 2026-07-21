---
integration: contegrity
upstream: <confirm — the user's Contegrity / CGB repo (local: D:\Contegrity)>
license: <confirm>
pinned_version: <confirm>
discipline: integrity-provenance
status: proposed
drafted: 2026-07-20
---

# Contegrity / CGB — Integration (proposed)

> **Proposed integration shim.** The *fit, routing, and boundary* are grounded in
> what Doctrine provides and what Contegrity does; the **upstream URL, license,
> pinned version, and exact API are `<confirm>` placeholders** the human fills in
> before wiring live. Non-vendored.

## What it is

Contegrity is the portfolio's **integrity & provenance substrate** for enterprise
AI. **CGB** (its evidence-collection sidecar) **captures and replays agent
communications** — across MCP / HTTP / gRPC / Kafka — **non-invasively**, producing
tamper-evident records of what an agent actually did and said.

## Why it composes with Doctrine (the fit)

Doctrine already carries integrity primitives in-tree, and the newest domain pack is
about exactly this problem:

- the **state plane** (`state-plane/STATE.md`) is a **hash-chained**, tamper-evident
  record of session *decisions*;
- **gold-build** (`standards/merge-and-promotion.md`) is **content-pinned
  provenance** for what may deploy;
- **`domains/auditing.md`** requires **immutable evidence + chain-of-custody +
  reproducible findings** — which *is* Contegrity's model.

Contegrity/CGB supplies the layer beneath all three: it captures the agent's actual
**communications** as immutable evidence, where the state plane captures *decisions*
and gold-build captures *artifacts*.

## Doctrine wiring (to build once confirmed)

- **Evidence source for `domains/auditing.md`:** CGB's captured comms become the
  immutable, chain-of-custody evidence store the auditing pack's acceptance criteria
  require.
- **Provenance under gold-build:** attach CGB provenance to gold records so a
  promotion's evidence is the *actual* communications, not just a sign-off file.
- **Reconcile with the state plane:** the hash-chain records the durable *decision*
  truth; CGB records the *communications* truth. They cross-check each other — a
  decision with no supporting comms, or comms with no decision, is a finding.
- **Feeds `integrations/stix.md`:** STIX action-proofs + CGB comms-capture together
  give a complete, tamper-evident action+communication trail.

## Boundary (binding)

**The state plane is the durable decision truth; Contegrity is the
communications-evidence truth — they reconcile, neither replaces the other.**
Capture is non-invasive and machine-local by default; exporting captured evidence
externally is a §5 action (it may contain secrets/PII — scan first).

## Taxonomy placement

**Integrity / Provenance** — the evidence plane beneath the state plane, gold-build,
and `domains/auditing.md`. Complements STIX (action proofs) and OpenGuide (behavior):
Contegrity is the *record* the other two produce decisions and behavior into.

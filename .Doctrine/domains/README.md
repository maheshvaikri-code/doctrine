# Domain packs — vertical overlays on the engineering core

Doctrine's roles and skills are **horizontal**: they are *how* you build software,
reusable across every industry. A **domain pack** is a thin **vertical overlay**
for building software *in a regulated or specialized industry* — healthcare,
finance, aerospace, logistics. It carries what the vertical adds — its regulatory
regime, canonical entities, domain acceptance criteria, harm model, and gate
sign-offs — and **nothing the core already provides.**

## The composition model — a matrix, not a tree

You do **not** create a "healthcare backend engineer" or a "finance backend
engineer." There is one `roles/backend-engineer.md`; it **loads a domain pack**
when the work serves that domain. Coverage is `role × domain`, composed on demand:

```
build a HIPAA patient portal
  → Product Owner writes the brief
  → routing loads domains/healthcare.md   (the overlay)
  → the SAME backend/frontend/data engineers build against its
    FHIR entities + HIPAA acceptance criteria
  → G5 adds the domain sign-off (compliance-officer + clinical-safety) beside the security-reviewer
  → ship
```

Same gates, same roles, **+ overlay**. This keeps the always-loaded core lean
(progressive disclosure) while covering any number of verticals.

## What a pack is — and is not

- **Is:** the *stable structure* of operating in the domain — which regimes apply,
  what to verify, who signs, the canonical entities, the glossary.
- **Is not:** a copy of the regulations (they change — the model + current sources
  fill specifics; a pack that hardcodes volatile facts rots, the `STALE@` problem
  the state plane exists to fight), and not a parallel set of roles/skills.

## Authoring a pack

Copy `templates/domain-pack.md`, fill its eight sections, file as
`domains/<slug>.md`, and add a routing row to `.Doctrine.md` §6. Add a **new
specialist role** only where the function is genuinely distinct from an existing
role (most domains need zero or one). Packs are overlays, not disciplines, so they
carry **no Signature block** (that convention is for roles + skills).

## Packs

| Pack | Regime highlights | New roles | Status |
|------|-------------------|-----------|--------|
| `domains/healthcare.md` | HIPAA/HITECH · FHIR/HL7 · IEC 62304 clinical safety | +2 (clinical-safety, regulatory-affairs) | pilot (reference) |
| `domains/finance.md` | PCI-DSS · AML/KYC · SOX · ISO 20022/FIX · double-entry | 0 (reuses core governance) | shipped |
| `domains/quant.md` | MiFID II · MAR · model-risk · FIX · point-in-time/backtest | +1 (quant-researcher) | shipped |
| `domains/aerospace.md` | DO-178C · ECSS · ITAR/EAR · CCSDS · MC/DC + traceability | 0 (reuses qa/risk/compliance) | shipped |
| `domains/manufacturing.md` | ISO 9001/IATF · IEC 62443 (OT) · IEC 61508 (SIL) · ISA-95 · lot genealogy | 0 (reuses security/risk/qa) | shipped |
| `domains/logistics.md` | customs/export · sanctions · GS1/EPCIS · EDI · DSCSA · cold-chain | 0 (reuses compliance/regulatory) | shipped |
| `domains/ecommerce.md` | PCI · consumer-protection · tax nexus · WCAG · idempotent checkout | 0 (reuses security/compliance/frontend) | shipped |
| `domains/travel.md` | IATA/GDS/NDC · PCI · passport PII · ATOL · fare rules | 0 (reuses security/compliance/interop) | shipped |
| `domains/transportation.md` | FMCSA HOS/ELD · ISO 26262 (ASIL) · telematics privacy · GTFS | 0 (reuses risk/compliance/sre) | shipped |
| `domains/auditing.md` | SOC 2 · GAAS/SOX · evidence integrity · independence (SoD) | 0 (reuses security/compliance/risk) | shipped |

The roles column is the honesty ledger of overlay cost: **ten domains, three new
roles total** (healthcare +2, quant +1; the other eight reuse the core). A pack is
an overlay, not a payroll — a new role appears only where a genuinely distinct
function does (healthcare's clinical safety, quant's research rigor). New verticals
are stamped from `templates/domain-pack.md`; most add zero roles.

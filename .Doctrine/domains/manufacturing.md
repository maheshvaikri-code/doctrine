# Domain Pack — Manufacturing

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building manufacturing software (MES, quality, OT/shop-floor) changes three
> things: **the software touches physical machinery** — a bad command can injure a
> person or wreck a line, so functional safety and interlocks are non-negotiable;
> **IT and OT are different worlds** — the plant network must be segmented from the
> office, or ransomware halts production; and **traceability is legal** — lot/batch
> genealogy must reconstruct exactly what went into every unit for a recall. Load
> this pack for MES/SCADA/quality/IIoT work. **Zero new roles** — it composes onto
> the core.

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **ISO 9001** | Quality management system | any production quality process |
| **IATF 16949** | Automotive QMS + traceability | automotive supply |
| **ISO 13485 / FDA 21 CFR 820** | Medical-device manufacturing (QSR) | making medical devices (composes with `domains/healthcare.md`) |
| **IEC 62443** | Industrial control-system (OT) security | any OT/plant-network system |
| **IEC 61508 / 61511 (SIL)** | Functional safety of control systems | software can command hazardous motion/energy |
| **ISA-95 / IEC 62264** | MES ↔ ERP integration levels + data model | integrating shop floor to business systems |

The pack names *which regime applies and what it demands*; specifics come from the
standard + primary sources at design time.

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md`, `skills/interoperability.md`, and
`skills/resilience.md` (real-time / OT reliability).

- **Standards:** **OPC-UA** (secure industrial interop), **MTConnect** (machine
  data), **MQTT/Sparkplug B** (IIoT), **ISA-95 / B2MML** (MES-ERP), **OPC-UA over
  the Purdue model** levels. Timestamps from the machine clock, sourced explicitly.
- **Canonical entities** (ISA-95): `Equipment`, `Material` (+ `Lot`/`Batch`),
  `Personnel`, `ProcessSegment`, `WorkOrder`, `BOM`, `Genealogy` (lot ↔ lot links),
  `QualityResult`, `OEE`.
- **Traceability invariant:** every finished unit's **genealogy** resolves both ways
  — forward (where did this lot go) and backward (what lots/machines/operators made
  this unit) — for recall and root-cause.

## 3. Domain acceptance criteria (added to every task's own)

1. Given a finished unit, when queried, then its **lot/batch genealogy** is complete
   and bidirectional (backward to inputs, forward to shipments).
2. Given the plant network, when architected, then **OT is segmented from IT**
   (Purdue-model zones + conduits, IEC 62443); no direct office-to-controller path.
3. Given software that can command hazardous motion/energy, when it runs, then
   **safety interlocks are independent of it** (a SIL-rated safety system, not the
   app logic) — software never the sole guard against physical harm.
4. Given a change to a running line, when deployed, then it is validated in a
   non-production cell/twin first; **no untested change reaches live control**.
5. Given OT data, when integrated to IT, then it flows through ISA-95 levels (no
   raw controller exposure to business systems).

## 4. Threat / harm model

- **Assets:** operators' physical safety, production continuity, the OT network,
  product quality + traceability, machine setpoints/recipes.
- **Untrusted inputs:** sensor/PLC data, operator HMI input, IIoT device telemetry,
  IT-side commands crossing into OT, remote-maintenance access.
- **Worst plausible harm:** (a) a bad motion/energy command → **operator injury or
  equipment destruction**; (b) OT ransomware/worm (Stuxnet-class) → line halt or
  sabotage; (c) a broken safety interlock or bypassed guard → death; (d) lost
  genealogy → an un-scopable recall (ship everything back). Harm is bodily +
  production loss + recall liability.

## 5. Gate overlay

- **G0 (Intake):** name the regime(s) and safety integrity level (SIL) if hazardous
  control is involved; add the §3 criteria.
- **G1 (Architecture):** OT/IT segmentation (Purdue), independent safety systems,
  ISA-95 integration, lot genealogy, and change-in-a-twin-first are **design
  constraints**.
- **G5 (Verification):** the **manufacturing domain sign-off** —
  `roles/security-reviewer.md` (IEC 62443 OT security, segmentation, remote access)
  **plus** `roles/risk-officer.md` (functional-safety / SIL + hazard sign-off)
  **plus** `roles/qa-engineer.md` (quality + traceability verification). Any may veto.
- **G6 (Release):** change validated off-line; rollback to last-known-good recipe
  tested; safety sign-off recorded.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/security-reviewer.md` | existing | OT/ICS security (IEC 62443), segmentation, remote access |
| `roles/risk-officer.md` | existing | functional safety (SIL) + hazard analysis |
| `roles/qa-engineer.md` | existing | quality-system + lot-traceability verification |
| `roles/data-architect.md` | existing | ISA-95 entity modeling + genealogy |
| `roles/sre.md` | existing | real-time / OT reliability + availability |

## 7. Glossary

- **OT / IT** — Operational Technology (shop floor / control) vs Information Technology.
- **Purdue model** — the reference layering (levels 0–5) that segments OT from IT.
- **MES** — Manufacturing Execution System.
- **SIL** — Safety Integrity Level (IEC 61508); the required risk-reduction of a safety function.
- **Genealogy / lot traceability** — the bidirectional record of what made each unit.
- **OEE** — Overall Equipment Effectiveness.
- **OPC-UA** — the secure industrial interoperability standard.

## 8. Non-negotiables (domain)

1. **Never let application software be the sole guard against physical harm** — a
   SIL-rated safety system, independent of the app, holds the interlock.
2. **Never bridge OT and IT without segmentation** (Purdue zones + conduits); no
   direct office-network path to a controller.
3. **Never push an untested change to a live control system** — validate in a
   cell/digital twin first; keep a tested rollback to last-known-good.
4. **Never break lot genealogy** — traceability must reconstruct any recall scope,
   both directions.
5. **Remote/maintenance access to OT is least-privilege, logged, and time-boxed** —
   never a standing open path.

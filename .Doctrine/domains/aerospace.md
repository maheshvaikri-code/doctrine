# Domain Pack — Aerospace / Space

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building flight or space software changes three things: **the safety class dictates
> the process** (DO-178C DAL A code demands MC/DC coverage and bidirectional
> requirements traceability, not "good tests"); **the code often cannot fail-and-retry**
> (a real-time deadline missed, or heap exhausted, can lose the vehicle); and **the
> bits are export-controlled** (ITAR/EAR — sending them to the wrong person is a
> federal crime). Load this pack for flight software, ground/mission control, or
> spacecraft data systems. **Zero new roles** — it composes onto the existing core.

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **DO-178C** (+ DO-330/331/333 supplements) | Airborne software lifecycle by **DAL A–E** | certified airborne software |
| **DO-254** | Airborne electronic hardware | custom flight hardware/FPGA |
| **ECSS-E-ST-40 / Q-ST-80** (ESA) | European space software engineering + product assurance | European space missions |
| **NASA-STD-8739.8 / NPR 7150.2** | NASA software assurance + safety-critical classes | NASA missions |
| **ITAR / EAR** | Export control of defense/dual-use technical data | the tech is on the USML/CCL — controls who may access it |
| **AS9100** | Aerospace quality management | supplier/manufacturer QMS |

The pack names *which regime and safety class apply and what they demand*; the
detailed objectives come from the standard + primary sources at design time.

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md`, `skills/interoperability.md`, and
`skills/resilience.md` (real-time / fault tolerance).

- **Standards:** **CCSDS** (space telemetry/telecommand packets), **MIL-STD-1553**
  and **SpaceWire** (avionics buses), **ARINC 429 / 653** (avionics data / time-space
  partitioning), **PUS** (ECSS packet utilization). Time in a stated epoch (GPS/TAI/UTC)
  with leap-second handling made explicit.
- **Canonical entities:** `Requirement` (with a **bidirectional trace** to code +
  test), `SafetyCase` / hazard analysis, `TelemetryPoint`, `Command`, `Mode`
  (state machine), `Partition` (ARINC 653 time/space isolation), `ConfigItem`.
- **Traceability invariant:** every requirement traces down to code + a test, and
  every line of DAL-A/B code traces up to a requirement — no orphan code, no
  untested requirement.

## 3. Domain acceptance criteria (added to every task's own)

1. Given DAL-A (or DAL-B) software, when verified, then structural coverage meets the
   class (**MC/DC** for A, decision coverage for B) and **bidirectional requirements
   traceability** is complete — no orphan code, no unverified requirement.
2. Given a flight-critical path, when it runs, then it is **deterministic** — bounded
   worst-case execution time (WCET), no unbounded loops, and **no dynamic memory
   allocation after initialization** (or a justified, analyzed exception).
3. Given a fault, when it occurs, then the system enters a **defined safe mode** —
   fail-operational or fail-safe per the hazard analysis, never undefined behavior.
4. Given any technical data, when stored/shared, then **ITAR/EAR classification** is
   applied and access is restricted to authorized persons/systems (segregated
   environment) — a cross-border/uncleared flow is a §5 escalation.
5. Given a change, when made, then **configuration management** records it and its
   effect on the safety case and certification evidence.

## 4. Threat / harm model

- **Assets:** the vehicle/mission and any crew; the safety case; export-controlled
  technical data; the certification evidence trail.
- **Untrusted inputs:** sensor/telemetry data (noise, dropouts, spoofing),
  ground commands, timing sources, radiation-induced bit flips (SEU).
- **Worst plausible harm:** (a) a missed real-time deadline or heap exhaustion →
  loss of control → **loss of vehicle/mission/crew**; (b) an unhandled fault with no
  safe mode → uncontrolled behavior; (c) a bit-flip corrupting an unprotected value →
  wrong actuation (radiation is an input, not an edge case); (d) ITAR data reaching a
  foreign person → **federal criminal liability**. Harm is loss of life/mission +
  criminal export liability.

## 5. Gate overlay

- **G0 (Intake):** declare the **safety class (DAL / NASA class)** and whether ITAR/EAR
  applies — both reshape the whole process; add the §3 criteria.
- **G1 (Architecture):** determinism, partitioning (ARINC 653), safe modes, WCET
  budgets, and requirements traceability are **design constraints**; the safety case
  is authored here, not retrofitted; the dev environment is export-controlled.
- **G5 (Verification):** the **aerospace domain sign-off** — `roles/qa-engineer.md`
  runs the DO-178C structural-coverage + traceability verification; `roles/risk-officer.md`
  owns the safety-case / hazard sign-off; `roles/compliance-officer.md` +
  `roles/regulatory-affairs.md` verify ITAR/EAR handling + certification liaison. Any
  may veto ship. (For DAL-A programs at scale, a dedicated safety engineer is the
  next specialist role to add — deferred until the workload earns it.)
- **G6 (Release):** certification evidence package assembled; config baseline frozen;
  export-control review recorded.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/qa-engineer.md` | existing | DO-178C structural coverage (MC/DC) + traceability verification |
| `roles/risk-officer.md` | existing | the safety case / hazard analysis sign-off |
| `roles/compliance-officer.md` | existing | ITAR/EAR export-control review |
| `roles/regulatory-affairs.md` | existing | certification liaison (DER/authority), submissions |
| `roles/sre.md` | existing | ground/mission-control resilience + real-time ops |

## 7. Glossary

- **DAL** — Design Assurance Level (DO-178C A–E); A = catastrophic-if-it-fails.
- **MC/DC** — Modified Condition/Decision Coverage: the structural-coverage bar for DAL-A.
- **Traceability** — bidirectional links: requirement ↔ code ↔ test.
- **WCET** — Worst-Case Execution Time; must be bounded for real-time paths.
- **Safe mode** — a defined degraded state entered on fault (fail-safe/operational).
- **ITAR / EAR** — US export-control regimes for defense / dual-use technical data.
- **SEU** — Single-Event Upset: a radiation-induced bit flip.
- **ARINC 653** — time-and-space partitioning standard for avionics.

## 8. Non-negotiables (domain)

1. **Never ship DAL-A/B software without the required structural coverage (MC/DC for
   A) and complete bidirectional traceability.** Coverage is the certification, not a nicety.
2. **Never rely on undefined behavior on a fault** — every flight-critical failure
   mode has a defined safe mode from the hazard analysis.
3. **Never use unbounded loops or post-init dynamic allocation in flight-critical
   paths** without a documented, analyzed justification.
4. **Never let ITAR/EAR-controlled technical data reach an unauthorized person or an
   uncontrolled system** — classification and access control first; a cross-border
   flow is a §5 escalation, always.
5. **Configuration management is mandatory** — an uncontrolled change to certified
   software invalidates the safety case.

# Domain Pack — Transportation

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building transportation/fleet/mobility software changes three things: **fatigue and
> control are safety law** — hours-of-service and driver-assist logic can kill if
> wrong, so ELD accuracy and functional safety are non-negotiable; **the vehicle is a
> surveillance device** — telematics tracks a person, so location/driver-data privacy
> is load-bearing; and **real-time reliability is a safety property**, not a nicety.
> Load this pack for fleet, telematics, routing, ELD, or driver-assist work. **Zero
> new roles** (autonomy/ADAS safety-critical work also composes `domains/aerospace.md`).

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **FMCSA HOS + ELD mandate** (US) | Driver hours-of-service, electronic logging | commercial trucking/driving |
| **ISO 26262 (ASIL)** | Automotive functional safety | driver-assist / ADAS / autonomy (see `domains/aerospace.md` for safety-critical rigor) |
| **DOT / vehicle safety** | Vehicle compliance, inspections, recalls | regulated vehicles |
| **Telematics data privacy** (GDPR/CCPA) | Location + driver-behavior data | tracking drivers/vehicles |
| **GTFS / transit standards** | Public-transit schedule + real-time feeds | transit apps |

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md`, `skills/interoperability.md`, and
`skills/resilience.md`.

- **Standards:** **ELD** logs, **AEMP / ISO 15143-3** (fleet telematics), **GTFS /
  GTFS-realtime** (transit), **NMEA/GPS**, **J1939/OBD-II** (vehicle bus), map/routing
  APIs. Timestamps UTC with the vehicle's time source stated.
- **Canonical entities:** `Vehicle`, `Driver` (+ license/qualification), `Trip`,
  `Route`, `TelematicsEvent` (location/speed/harsh events), `HOSLog` (duty status),
  `Geofence`, `MaintenanceRecord`.
- **HOS invariant:** duty-status logs are **tamper-evident and complete** — edits are
  audited, never silently overwritten (an ELD is a legal record).

## 3. Domain acceptance criteria (added to every task's own)

1. Given driver duty status, when logged, then the **ELD/HOS record is accurate,
   complete, and tamper-evident** — edits are attributed and audited.
2. Given a driver-assist / ADAS / autonomy function, when it can affect vehicle
   control, then it meets its **ISO 26262 ASIL** target with a safe fallback — the
   software is never the sole guard against a crash (compose `domains/aerospace.md`).
3. Given telematics/location data, when collected, then it is **minimized, consented,
   and access-controlled** — driver tracking is not silent surveillance.
4. Given real-time safety-relevant data (position, alerts), when delivered, then
   latency + availability meet the safety budget; a stale reading is flagged, not
   trusted.
5. Given geofencing/routing, when it drives a safety or compliance action, then its
   accuracy is validated (no acting on a bad fix).

## 4. Threat / harm model

- **Assets:** road users' physical safety, drivers' privacy, the legal HOS record,
  vehicle-control integrity.
- **Untrusted inputs:** GPS/telematics (spoofable, gaps), sensor data, driver input,
  map/routing data, remote commands.
- **Worst plausible harm:** (a) HOS bug hides fatigue → a drowsy driver crashes;
  (b) an ADAS/autonomy fault with no safe fallback → **collision, loss of life**;
  (c) telematics breach → stalking/surveillance harm; (d) a spoofed/stale GPS fix
  driving an automated action → wrong maneuver. Harm is bodily + privacy + legal.

## 5. Gate overlay

- **G0 (Intake):** add the §3 criteria; flag safety-critical control (→ ISO 26262
  ASIL, compose the aerospace pack's rigor) vs telematics/logistics-only.
- **G1 (Architecture):** tamper-evident HOS logging, functional-safety architecture
  with safe fallbacks, driver-data minimization, and real-time reliability budgets
  are **design constraints**.
- **G5 (Verification):** the **transportation domain sign-off** — `roles/risk-officer.md`
  (functional safety / ASIL + hazard sign-off) **plus** `roles/compliance-officer.md`
  (HOS/ELD legal record + telematics privacy) **plus** `roles/qa-engineer.md` +
  `roles/sre.md` (real-time reliability). Any may veto. (Dedicated safety engineer is
  the deferred specialist for ASIL-D autonomy, as in aerospace.)
- **G6 (Release):** ELD compliance verified; safe-fallback behavior tested; privacy
  disclosures in place.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/risk-officer.md` | existing | functional safety (ISO 26262 ASIL) + hazard sign-off |
| `roles/compliance-officer.md` | existing | HOS/ELD legal record, telematics privacy |
| `roles/sre.md` | existing | real-time reliability + availability budgets |
| `roles/qa-engineer.md` | existing | safety + compliance verification |
| `roles/data-architect.md` | existing | telematics / HOS / vehicle modeling |

## 7. Glossary

- **HOS** — Hours of Service (driver working-time limits).
- **ELD** — Electronic Logging Device (the legal duty-status record).
- **ASIL** — Automotive Safety Integrity Level (ISO 26262, A–D; D = most stringent).
- **ADAS** — Advanced Driver-Assistance Systems.
- **Telematics** — vehicle location/behavior data collection.
- **Geofence** — a virtual boundary triggering an action.
- **GTFS** — the standard public-transit schedule/real-time feed format.

## 8. Non-negotiables (domain)

1. **Never let HOS/ELD records be silently editable** — they are legal records;
   edits are attributed, audited, tamper-evident.
2. **Never let software be the sole guard against a crash** — safety-critical control
   meets its ASIL target with an independent safe fallback (compose aerospace rigor).
3. **Never treat driver telematics as free data** — minimize, consent, access-control;
   location is sensitive PII.
4. **Never act on a stale or unverified position fix** for a safety/compliance action.
5. **Never ship an ADAS/autonomy change without its functional-safety sign-off.**

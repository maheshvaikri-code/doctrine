# Domain Pack — Travel / Tourism

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building travel software changes three things: **inventory is perishable and
> distributed** — a seat/room is sold once across many channels, so availability and
> booking idempotency are load-bearing; **the booking record is regulated identity
> data** — PNRs hold passports and special-category PII under strict rules; and
> **money protection is legal** — package holidays require financial bonding (ATOL),
> and cancellation/refund terms are enforceable. Load this pack for booking, GDS/NDC,
> or itinerary work. **Zero new roles** (payment path borrows `domains/finance.md`).

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **IATA / GDS + NDC** | Airline distribution, fare/booking messaging | selling flights |
| **PCI-DSS** | Card data at booking | taking payment (see `domains/finance.md`) |
| **GDPR (passport = special category)** | Traveler PII, API/PNR-sharing to authorities | EU travelers; border-authority data sharing |
| **Package Travel Directive / ATOL** | Refunds, financial protection, bonding | selling package holidays |
| **APIS / border control** | Advance passenger info to governments | international travel |

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md` and `skills/interoperability.md`.

- **Standards:** **GDS** (Amadeus/Sabre/Travelport), **IATA NDC** (XML offers/orders),
  **OpenTravel (OTA)**, **HL7-style?** no — hospitality uses **HTNG**; car/rail have
  their own. PNR record locators; IATA airport/airline codes.
- **Canonical entities:** `Offer`/`Fare`, `Availability` (perishable, time-boxed),
  `Booking`/`PNR`, `Traveler` (+ passport/APIS data), `Segment` (flight/hotel/car),
  `Ancillary`, `FareRule` (change/cancel/refund conditions).
- **Availability invariant:** a bookable unit reflects **real-time** inventory from
  the source of truth; a hold expires; two channels never confirm the same seat.

## 3. Domain acceptance criteria (added to every task's own)

1. Given a booking request, when retried, then **one** PNR/reservation results (no
   duplicate booking, no double charge).
2. Given availability shown, when a booking is attempted, then it is confirmed
   against **live** inventory (or gracefully fails) — no overbooking beyond policy.
3. Given fare rules, when a change/cancel/refund is processed, then the **rule is
   applied correctly** (penalties, non-refundable segments) and the total is accurate.
4. Given passport/APIS data, when handled, then it is encrypted, minimized, and only
   shared with authorities as legally required — never logged or sent to an LLM.
5. Given a package holiday, when sold, then financial-protection (ATOL-style)
   obligations are met and disclosed.

## 4. Threat / harm model

- **Assets:** travelers' money + passport/PII, the booking record, perishable
  inventory, refund/protection obligations.
- **Untrusted inputs:** GDS/NDC responses, payment webhooks, traveler-entered
  passport/contact data, date/route input.
- **Worst plausible harm:** (a) a double-booking or lost PNR → stranded traveler;
  (b) mis-applied fare rules → wrong refund/penalty (financial + legal); (c) passport
  data breach → high-harm PII exposure; (d) selling unprotected packages → ATOL
  breach + unprotected customers if the operator fails. Financial + traveler safety.

## 5. Gate overlay

- **G0 (Intake):** add the §3 criteria; flag whether packages (bonding), flights
  (APIS), or international (border data) are involved.
- **G1 (Architecture):** live availability + booking idempotency + fare-rule engine +
  passport-data minimization are **design constraints**.
- **G5 (Verification):** the **travel domain sign-off** — `roles/security-reviewer.md`
  (PCI + passport-data handling, GDS/PSP boundaries) **plus** `roles/compliance-officer.md`
  (special-category PII, package/ATOL, APIS sharing). Any may veto.
- **G6 (Release):** refund/cancellation path tested against fare rules; financial-
  protection disclosures in place.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/security-reviewer.md` | existing | PCI + passport-data handling, GDS/PSP boundaries |
| `roles/compliance-officer.md` | existing | special-category PII, package/ATOL, APIS sharing |
| `roles/interop-engineer.md` | existing | GDS / NDC / OTA integration |
| `roles/data-architect.md` | existing | PNR / availability / fare modeling |

## 7. Glossary

- **PNR** — Passenger Name Record (the booking record + traveler data).
- **GDS** — Global Distribution System (Amadeus/Sabre/Travelport).
- **NDC** — IATA New Distribution Capability (modern XML offer/order API).
- **APIS** — Advance Passenger Information System (border-authority data).
- **ATOL** — UK financial protection for package holidays (bonding).
- **Fare rule** — the conditions governing changes/cancellations/refunds.

## 8. Non-negotiables (domain)

1. **Never confirm a booking against stale inventory** — check live availability; a
   hold expires; never double-sell a unit.
2. **Never charge or book non-idempotently** — one request, one PNR, one charge.
3. **Never mishandle passport/APIS data** — encrypt, minimize, share only as legally
   required; never log it or send it to an LLM.
4. **Never mis-apply fare/refund rules** — the rule engine is the source of truth for
   penalties and refundability.
5. **Never sell an unprotected package** where financial protection is required.

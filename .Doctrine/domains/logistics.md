# Domain Pack — Logistics / Supply Chain

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building logistics/supply-chain software changes three things: **crossing a border
> is a legal act** — a wrong HS code, valuation, or an export-controlled item to a
> sanctioned party is a customs/criminal violation, not a bad shipment; **the data
> model is other people's standards** — GS1 identifiers and EDI messages, not yours
> to invent; and **chain-of-custody is the product** — for pharma/food a broken
> cold-chain or a serialization gap means counterfeit or spoiled goods reaching a
> patient. Load this pack for shipping, WMS, track-and-trace, or customs work.
> **Zero new roles** — it composes onto the core.

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **Customs / trade compliance** (HS codes, valuation, Incoterms) | Cross-border movement + duties | shipping internationally |
| **Export control / sanctions** (ITAR/EAR, OFAC, dual-use) | Who may receive what, where | controlled goods or restricted parties (composes with `domains/aerospace.md`) |
| **C-TPAT / AEO** | Supply-chain security programs | trusted-trader status |
| **DSCSA / EU FMD** | Pharma serialization + track-and-trace | distributing medicines |
| **GDP / FSMA cold-chain** | Good Distribution Practice; food safety | temperature-controlled pharma/food |
| **Dangerous goods** (IATA DGR / IMDG / ADR) | Classification + handling of hazmat | shipping hazardous materials |

The pack names *which regime applies and what it demands*; classifications and
thresholds come from the model + primary sources at design time.

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md` and `skills/interoperability.md`.

- **Standards:** **GS1** identifiers — **GTIN** (product), **SSCC** (logistics unit),
  **GLN** (location), **SGTIN** (serialized item); **EPCIS** (the who/what/where/when/
  why track-and-trace event model); **EDI** — **X12** (US: 850 PO, 856 ASN, 214
  status) and **EDIFACT** (intl); carrier APIs.
- **Canonical entities:** `Party` (+ sanctions status), `Location` (GLN), `Product`
  (GTIN), `Shipment`/`Consignment`, `HandlingUnit` (SSCC), `CustomsDeclaration`
  (HS code + valuation + Incoterm), `TrackingEvent` (EPCIS), `ColdChainReading`.
- **Chain-of-custody invariant:** every custody transfer emits an EPCIS event; the
  full commissioning→dispensing history of a serialized unit is reconstructable.

## 3. Domain acceptance criteria (added to every task's own)

1. Given any cross-border shipment, when created, then its **customs data is complete
   and correct** (HS code, declared value, country of origin, Incoterm) and the
   parties are **screened against sanctions/denied-party lists**.
2. Given a controlled item or a restricted destination/party, when detected, then the
   shipment is **held for review** — never auto-released (a §5 escalation).
3. Given a serialized (pharma) unit, when it moves, then an **EPCIS custody event** is
   recorded; its history is queryable end-to-end (no serialization gaps).
4. Given a cold-chain shipment, when in transit, then temperature is monitored and an
   **excursion invalidates the unit** (not silently accepted).
5. Given dangerous goods, when shipped, then they are **classified and documented**
   per IATA/IMDG/ADR before dispatch.

## 4. Threat / harm model

- **Assets:** goods + their custody integrity, customs/legal standing, PII of
  recipients, sanctions compliance, cold-chain integrity.
- **Untrusted inputs:** EDI/API messages from partners (malformed, spoofable),
  scanned barcodes, carrier status feeds, address/party data.
- **Worst plausible harm:** (a) an export-controlled item or a sanctioned party
  slips through → **criminal/OFAC liability, seizure**; (b) a serialization gap →
  counterfeit medicine reaches a patient; (c) an unflagged cold-chain excursion →
  spoiled/ineffective product dispensed; (d) mis-declared customs value → fraud/
  penalties. Harm is legal/criminal + patient/consumer safety.

## 5. Gate overlay

- **G0 (Intake):** name the regime(s); flag whether goods are controlled/serialized/
  temperature-sensitive/hazmat; add the §3 criteria.
- **G1 (Architecture):** GS1/EPCIS entities + EDI interop + sanctions screening +
  cold-chain monitoring + a **hold-not-release** default for flagged shipments are
  **design constraints**.
- **G5 (Verification):** the **logistics domain sign-off** —
  `roles/compliance-officer.md` (customs/trade, sanctions screening, data privacy)
  **plus** `roles/regulatory-affairs.md` (export-control classification, DSCSA)
  **plus** `roles/security-reviewer.md` for partner EDI/API boundaries. Any may veto.
- **G6 (Release):** denied-party screening live; EPCIS events flowing; cold-chain
  alerting proven; DG documentation generated.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/compliance-officer.md` | existing | customs/trade, sanctions/denied-party screening, PII |
| `roles/regulatory-affairs.md` | existing | export-control classification, DSCSA/FMD serialization |
| `roles/security-reviewer.md` | existing | partner EDI/API trust boundaries |
| `roles/data-architect.md` | existing | GS1/EPCIS/EDI entity modeling |
| `roles/interop-engineer.md` | existing | EDI (X12/EDIFACT) + carrier-API integration |

## 7. Glossary

- **HS code** — Harmonized System tariff classification; drives duties + controls.
- **Incoterm** — standardized delivery-responsibility terms (EXW, FOB, DDP…).
- **GS1 / GTIN / SSCC / GLN** — global standards for product / logistics-unit / location IDs.
- **EPCIS** — the event standard for what/where/when/why in track-and-trace.
- **EDI** — Electronic Data Interchange (X12 / EDIFACT partner messaging).
- **Denied-party / sanctions screening** — checking parties against OFAC/EU/UN lists.
- **Cold chain** — unbroken temperature control; an excursion can invalidate product.
- **DSCSA** — US pharma serialization + track-and-trace law.

## 8. Non-negotiables (domain)

1. **Never auto-release a shipment flagged for export control or a sanctioned/denied
   party** — hold for human review; a bypass is a §5 escalation, always.
2. **Never file customs data you cannot substantiate** (HS code, value, origin) —
   mis-declaration is fraud.
3. **Never break serialization/chain-of-custody** for regulated goods — every custody
   transfer is an EPCIS event; no gaps.
4. **Never silently accept a cold-chain excursion** — an out-of-range reading
   invalidates the unit until dispositioned.
5. **Never invent identifiers where GS1 exists** — GTIN/SSCC/GLN, not a home-grown scheme.

# Domain Pack — HealthCare

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building software that touches patient data, clinical decisions, or medical
> devices changes three things: **privacy law is criminal, not civil** (PHI
> mishandling is a reportable breach); **the data model is a published standard**
> (FHIR/HL7), not yours to invent; and **a defect can harm a patient**, so
> clinical risk gets its own sign-off. Load this pack *in addition to* the normal
> role/skill routing whenever work touches PHI, clinical workflow, or a device.

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **HIPAA / HITECH** (US) | Privacy + Security of PHI; breach notification | any storage/transit/processing of identifiable patient data |
| **GDPR (health = special category)** (EU/UK) | Lawful basis, data-subject rights, DPIA | EU/UK patients; explicit consent + DPIA required |
| **IEC 62304** | Medical-device software lifecycle + safety class (A/B/C) | the software *is* or drives a medical device (SaMD) |
| **DCB0129 / DCB0160** (UK NHS) | Clinical risk management (manufacturer / deployer) | deploying into NHS; a Clinical Safety Case + hazard log are mandatory |
| **FDA 21 CFR Part 11** | Electronic records + signatures | regulated records requiring audit trail / e-sig |
| **SOC 2 / HITRUST** | Security controls attestation | enterprise/provider customers require it |

The pack names *which regime applies and what it demands*; current specifics come
from the model + primary sources at design time — never hardcode volatile clauses.

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md` (one definition per entity) and
`skills/interoperability.md`. **The data model is standardized — adopt it, don't
reinvent it.**

- **Standard:** **FHIR R4/R5** (RESTful resources) for exchange; **HL7 v2** for
  legacy hospital interfaces; **SMART on FHIR** + **OAuth2/OIDC** for app auth;
  **DICOM** for imaging; **SNOMED CT / LOINC / ICD-10 / RxNorm** as the terminology
  spines (diagnoses, labs, drugs).
- **Canonical entities** (map yours onto these, don't fork them): `Patient`,
  `Practitioner`, `Encounter`, `Observation` (vitals/labs), `Condition`,
  `MedicationRequest`, `AllergyIntolerance`, `Consent`, `DocumentReference`.
- **Identity:** never invent a patient identifier scheme where a national/MRN one
  exists; model it as a FHIR `Identifier` with a system URI.

## 3. Domain acceptance criteria (added to every task's own)

1. Given any PHI at rest, when stored, then it is encrypted (AES-256) and the field
   is classified in the data inventory; given PHI in transit, then TLS 1.2+ only.
2. Given any access to a patient record, when it occurs, then an **immutable audit
   log** entry (who, what, when, patient, purpose) is written — audit is a feature,
   not a nice-to-have.
3. Given a data-subject/patient request (access, export, delete-where-lawful), when
   made, then the system can fulfill it within the statutory window.
4. Given PHI, when it appears in logs, error messages, analytics, or an LLM prompt,
   then it is redacted/tokenized first — **PHI never leaks to a third-party model or
   log sink.**
5. Given a clinical-decision or dosing feature, when shipped, then it carries a
   hazard-log entry and a clinical-safety sign-off (see §5).

## 4. Threat / harm model

- **Assets:** PHI (identity + health = maximally sensitive), clinical decisions,
  audit integrity, consent state, device behavior.
- **Untrusted inputs:** patient/clinician free text, HL7/FHIR feeds from external
  systems, device telemetry, uploaded documents/images.
- **Worst plausible harm:** (a) a PHI breach → reportable, fines, patient harm from
  exposure; (b) a wrong dose / missed alert / mis-mapped code → **physical patient
  harm or death**; (c) unauthorized record access (celebrity/ex-partner snooping) →
  the audit log is the control; (d) PHI silently sent to an LLM/analytics vendor.
  Harm here is bodily, not just financial — the threat sketch must say so.

## 5. Gate overlay

- **G0 (Intake):** name the regime(s); add the §3 acceptance criteria; flag if the
  build is SaMD (→ IEC 62304 safety class).
- **G1 (Architecture):** data-residency + encryption + audit-trail + consent model
  are design constraints, not afterthoughts; adopt FHIR entities; a BAA is required
  before any third-party processes PHI (a §5 escalation).
- **G5 (Verification):** the **healthcare domain sign-off** — the
  `roles/security-reviewer.md` PHI-handling review **plus** the
  `roles/compliance-officer.md` HIPAA/GDPR review, **and**, for any
  clinical/device feature, the `roles/clinical-safety-officer.md` safety sign-off
  against the hazard log. Any one may veto ship.
- **G6 (Release):** breach-notification runbook current; retention/disposal policy
  applied; SaMD labeling + (where applicable) regulatory submission via
  `roles/regulatory-affairs.md`.

## 6. Specialist roles

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/compliance-officer.md` | existing | always (HIPAA/GDPR audit) |
| `roles/security-reviewer.md` | existing | always (PHI is the crown jewel) |
| `roles/clinical-safety-officer.md` | **new** | any clinical-decision, dosing, alerting, or SaMD feature — holds a **patient-safety veto** |
| `roles/regulatory-affairs.md` | **new** | SaMD classification, submissions, audit liaison (reused across regulated domains) |
| `roles/data-architect.md` | existing | modeling patient data onto FHIR |

## 7. Glossary

- **PHI** — Protected Health Information: identifiable health data.
- **BAA** — Business Associate Agreement: contract required before a vendor may
  process PHI on your behalf.
- **SaMD** — Software as a Medical Device.
- **FHIR** — Fast Healthcare Interoperability Resources (HL7's modern API standard).
- **Hazard log** — the living register of clinical hazards, causes, and mitigations.
- **Minimum necessary** — HIPAA rule: access only the PHI required for the task.
- **De-identification** — Safe Harbor (18 identifiers removed) or Expert
  Determination, so data is no longer PHI.

## 8. Non-negotiables (domain)

1. **Never send PHI to a third-party service (including an LLM) without a signed BAA
   and de-identification/redaction** — this is a §5 escalation, always.
2. **Never ship a clinical/dosing/alerting feature without a clinical-safety
   sign-off and a hazard-log entry.** Convenience never overrides patient safety.
3. **Never disable or bypass the access audit log** — it is the control against
   unauthorized record access.
4. **Never invent a patient identity or clinical terminology scheme** where a
   standard (MRN, SNOMED, LOINC, ICD-10) exists.
5. **Minimum necessary, always** — collect and expose the least PHI the task needs.

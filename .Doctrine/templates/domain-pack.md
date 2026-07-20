# Domain Pack — <domain name>

<!-- G1 artifact. A domain OVERLAY, not a discipline: it composes with the
     engineering core (roles + skills), it does not replace it. Authored/loaded
     at G1 (design constraints) and enforced by a G5 domain sign-off.
     File as domains/<slug>.md. Keep it to STABLE structure — the regime that
     applies, what to verify, who signs — not volatile facts that go stale. -->

> One or two sentences: what building software *in this domain* changes, and
> when to load this pack. Load it in ADDITION to the normal role/skill routing —
> a domain backend engineer is a `roles/backend-engineer.md` **plus** this pack.

## 1. Regulatory / standards regime

The rules that bind here — what each governs, not a copy of the law (laws change;
the model + current sources fill specifics). One row per regime.

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| <e.g. HIPAA> | <PHI privacy/security> | <you touch patient data> |

## 2. Canonical entities & interoperability

The domain's data model + the wire standards. Routes into
`skills/data-architecture.md` (one definition per entity) and
`skills/interoperability.md` (protocols/serialization).

- **Entities:** the canonical objects and their one-true definitions.
- **Standards:** the interchange formats / protocols (e.g. FHIR, ISO 20022, GS1).

## 3. Domain acceptance criteria

What "correct" means *here*, as testable rules the normal G0 brief inherits. These
are ADDED to a task's own acceptance criteria, never instead of them.

1. Given …, when …, then … (observable, domain-specific)

## 4. Threat / harm model

Domain-specific abuse and *harm* (not just security): who is hurt, how, worst
plausible case. Feeds the Class-L threat sketch and the G5 sign-off.

- **Assets:** … · **Untrusted inputs:** … · **Worst plausible harm:** …

## 5. Gate overlay (what each gate adds in this domain)

- **G0 (Intake):** domain acceptance criteria + regime identified.
- **G1 (Architecture):** design constraints this regime imposes (data residency,
  audit trail, safety class, …).
- **G5 (Verification):** the **domain sign-off** — WHO must sign and against what
  (extends the security-reviewer/compliance-officer veto; names any specialist).
- **G6 (Release):** domain release gates (labeling, submissions, retention).

## 6. Specialist roles

Which roles this domain pulls in — existing first, new only where genuinely
distinct. State the trigger.

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/compliance-officer.md` | existing | always in this domain |

## 7. Glossary

Domain terms an engineer must not guess at. Term — one-line definition.

## 8. Non-negotiables (domain)

The hard rules that override convenience here. Numbered, absolute.

1. **Never …**

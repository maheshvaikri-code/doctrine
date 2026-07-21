# Domain Pack — Auditing / Assurance

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building audit / GRC / assurance software changes three things: **evidence is only
> worth its integrity** — a working paper that could have been altered proves nothing,
> so tamper-evidence and chain-of-custody are the product; **independence is
> structural** — the party that performs the work cannot attest to it, which is the
> doctrine's own fresh-context-verifier principle made into a legal requirement; and
> **an opinion must be reproducible** — the same evidence and procedure must yield the
> same finding. Load this pack for audit-management, evidence-collection, controls, or
> GRC work. **Zero new roles.**

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **SOC 2 / SSAE 18 / ISAE 3402** | Service-organization control reporting | attesting service controls |
| **PCAOB / GAAS** | Financial-audit standards, working papers | financial-statement audit |
| **SOX ICFR** | Internal control over financial reporting | public-company controls |
| **ISO 19011** | Auditing management-system guidelines | management-system audits |
| **Independence / ethics rules** (AICPA/IESBA) | Auditor independence, separation of duties | any attestation engagement |

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md` and `skills/interoperability.md`. The
evidence-integrity substrate overlaps the user's Contegrity provenance model.

- **Standards:** immutable/append-only evidence stores (hash-chained or WORM),
  **OSCAL** (open security-controls assessment language), control frameworks
  (SOC 2 TSC, NIST 800-53, ISO 27001 Annex A, COSO), GRC-platform APIs.
- **Canonical entities:** `Control`, `Assertion`, `Evidence` (immutable, hashed,
  timestamped, chain-of-custody), `WorkingPaper`, `TestOfControl`, `Finding`,
  `Sample`, `Materiality`, `Engagement` (+ independence attributes).
- **Evidence invariant:** every piece of evidence is **content-addressed and
  tamper-evident** — you can prove it has not changed since collection, and trace who
  collected it, when, and from where.

## 3. Domain acceptance criteria (added to every task's own)

1. Given collected evidence, when stored, then it is **immutable and tamper-evident**
   (hash/WORM), timestamped, with chain-of-custody — later alteration is detectable.
2. Given a control, when tested, then the test **traces to the evidence** that
   supports the conclusion, and the conclusion is **reproducible** from that evidence.
3. Given an engagement, when staffed/executed, then **independence / separation of
   duties** is enforced — the preparer of a control cannot sign its test (the
   fresh-context-verifier rule, mechanized).
4. Given sampling, when performed, then the method is recorded and defensible
   (population, method, size) — not cherry-picked.
5. Given a finding, when raised, then its severity, evidence, and remediation owner
   are recorded; the audit trail of the audit itself is complete.

## 4. Threat / harm model

- **Assets:** evidence integrity, the audit opinion's defensibility, independence,
  the confidentiality of audited data.
- **Untrusted inputs:** evidence uploaded by the audited party, system exports,
  auditor edits, sampling parameters.
- **Worst plausible harm:** (a) tampered/backdated evidence accepted → a false
  clean opinion (fraud enablement); (b) an independence violation → the whole opinion
  is void; (c) an irreproducible finding → indefensible under challenge; (d) a
  missed material item due to bad sampling → material misstatement uncaught. Harm is
  legal/professional liability + enabled fraud.

## 5. Gate overlay

- **G0 (Intake):** add the §3 criteria; identify the framework (SOC 2 / SOX / ISO)
  and independence constraints.
- **G1 (Architecture):** immutable evidence store + chain-of-custody + separation-of-
  duties enforcement + reproducible test procedures are **design constraints**.
- **G5 (Verification):** the **audit domain sign-off** — `roles/security-reviewer.md`
  (evidence-store immutability, access control, tamper-evidence) **plus**
  `roles/compliance-officer.md` (framework mapping, independence, retention) **plus**
  `roles/risk-officer.md` (materiality + sampling defensibility). Any may veto.
- **G6 (Release):** evidence integrity provable end-to-end; independence controls
  live; audit-of-the-audit trail complete.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/security-reviewer.md` | existing | evidence immutability, tamper-evidence, access control |
| `roles/compliance-officer.md` | existing | framework mapping, independence, retention |
| `roles/risk-officer.md` | existing | materiality + sampling defensibility |
| `roles/data-architect.md` | existing | control/evidence/finding modeling |

## 7. Glossary

- **Working paper** — the documented evidence + reasoning behind an audit conclusion.
- **Chain-of-custody** — the provable, unbroken record of who held evidence, when.
- **Independence** — the auditor cannot attest to work they performed (separation of duties).
- **Materiality** — the threshold above which a misstatement matters.
- **Test of control** — a procedure evidencing that a control operates.
- **OSCAL** — a machine-readable standard for controls/assessment.
- **WORM** — Write Once, Read Many (immutable storage).

## 8. Non-negotiables (domain)

1. **Never store audit evidence mutably** — hash/WORM, timestamped, chain-of-custody;
   any later change must be detectable.
2. **Never let the performer attest to their own work** — independence / separation of
   duties is enforced structurally, not by policy alone.
3. **Never present an irreproducible finding** — the same evidence + procedure yields
   the same conclusion.
4. **Never cherry-pick a sample** — method and population are recorded and defensible.
5. **Audit the audit** — the engagement's own trail (who did what, when) is complete.

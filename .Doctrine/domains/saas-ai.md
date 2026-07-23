# Domain Pack — Enterprise SaaS AI

<!-- G1 artifact. A deployment-pattern security-review archetype: overlays
     skills/ai-security.md with what is DISTINCT about multi-tenant SaaS AI features. -->

> Security-review archetype for **AI features inside multi-tenant enterprise SaaS** —
> copilots, RAG over customer data, AI actions in a shared product. Load with
> `skills/ai-security.md`. What is distinct: **tenant isolation** is the crown-jewel
> control (no customer's data or model context bleeds into another's), the LLM vendor
> is a **subprocessor** under the customer's DPA, and enterprises demand
> **no-training-on-our-data**, RBAC, residency, and auditability.

## 1. Regime (adds to `skills/ai-security.md`)

**SOC 2 / ISO 27001** (customers will audit), **GDPR/DPA** with the LLM as a named
**subprocessor**, data-residency commitments, sector packs where the tenant is
regulated (compose `domains/finance.md`, `healthcare.md`); EU AI Act tier per feature.

## 2. Canonical entities & interoperability

- **Entities:** `Tenant`, `Workspace`, `User` (+ role), `AIFeature`, `EmbeddingIndex`
  (per-tenant), `Subprocessor` (the model vendor), `AuditEvent`.
- **Interop:** the LLM vendor API (a subprocessor boundary), the vector store (must be
  tenant-partitioned), SSO/SCIM, the customer's BYO-key/BYO-model options.

## 3. Domain acceptance criteria (added to the task's own)

1. Given RAG / embeddings / context, when built or queried, then it is
   **tenant-partitioned** — retrieval, embeddings, and prompt context **cannot cross
   tenants** (the #1 SaaS-AI failure); tested with a cross-tenant probe.
2. Given customer data sent to the model, when processed, then it is **not used to
   train** the vendor's model (contractual + API flag verified), and the vendor is a
   **named subprocessor** in the DPA with residency honored.
3. Given AI features, when exposed, then **RBAC** applies — a user only gets AI over
   data they may already see; the AI cannot become a privilege-escalation path.
4. Given AI actions/answers, when produced, then they are **audit-logged per tenant**
   (who asked, what data, what the model did) for the customer's own audit.
5. Given cost/abuse, when a tenant uses the feature, then **per-tenant rate/token/cost
   limits** prevent one tenant degrading or expensing others.

## 4. Threat / harm model

- **Assets:** every tenant's data + the isolation guarantee, the no-train commitment,
  audit integrity, availability across tenants.
- **Untrusted inputs:** tenant users' prompts, uploaded documents (indirect injection
  into RAG), cross-tenant confusion in shared indexes.
- **Worst plausible harm:** (a) **cross-tenant leakage** — one customer's data surfaces
  in another's AI answer (contract-ending breach); (b) customer data trained into a
  shared model; (c) a user reaching data they shouldn't via the AI (broken RBAC); (d)
  a noisy/abusive tenant exhausting shared model capacity or cost. Trust-ending +
  contractual + privacy.

## 5. Gate overlay

- **G0:** tenancy model + subprocessor/DPA + residency + no-train commitments recorded.
- **G1:** per-tenant partitioning of retrieval/embeddings/context, RBAC on AI features,
  audit logging, and per-tenant limits are **design constraints**; the model vendor is
  a subprocessor (a §5 data-flow to approve).
- **G5:** the **SaaS-AI sign-off** — `roles/security-reviewer.md` (tenant isolation
  probe, RBAC, injection via uploads) **plus** `roles/compliance-officer.md` (DPA,
  subprocessor, residency, no-train). Any may veto.
- **G6:** cross-tenant isolation test in CI; audit export per tenant; incident path.

## 6. Specialist roles (all existing — no new roles)

| Role | Pulled in when… |
|------|-----------------|
| `roles/security-reviewer.md` (+ `skills/ai-security.md`) | tenant isolation, RBAC, RAG injection |
| `roles/compliance-officer.md` | DPA/subprocessor, residency, no-train |
| `roles/data-architect.md` | per-tenant partitioning of indexes/context |
| `roles/ml-engineer.md` | RAG/embedding + model wiring |

## 7. Glossary

- **Tenant isolation** — a hard guarantee that one customer's data/context never
  reaches another's; the crown-jewel SaaS control.
- **Subprocessor** — a third party (the LLM vendor) processing customer data on your behalf.
- **No-train** — the contractual + technical guarantee customer data isn't used to train the model.
- **Cross-tenant leakage** — data from tenant A surfacing to tenant B (often via a shared index).
- **BYO-key / BYO-model** — the customer supplies their own model credentials/endpoint.

## 8. Non-negotiables (domain)

1. **Never let retrieval, embeddings, or prompt context cross tenants** — partition and
   test with a cross-tenant probe.
2. **Never let customer data train the vendor's model** — verify the flag + the DPA.
3. **Never let the AI become a privilege-escalation path** — RBAC: AI over data the user already has.
4. **Never add the model vendor as a data flow without the DPA/subprocessor + residency** (§5).
5. **Never ship without per-tenant limits + per-tenant AI audit logs.**

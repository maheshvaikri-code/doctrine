# Domain Pack — Finance / Fintech

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building software that moves money, holds funds, extends credit, or handles card
> data changes three things: **money movement must be idempotent and auditable**
> (a retry must never double-charge; every cent is traceable); **the ledger is an
> invariant, not a table** (double-entry must always balance); and **card/PII data
> drags in strict scope regimes** (PCI-DSS, AML/KYC). Load this pack in addition to
> the normal routing whenever work touches payments, ledgers, trading, or lending.
> **Zero new roles** — this vertical composes onto existing governance roles.

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **PCI-DSS** | Cardholder data (PAN) storage/transit/processing | you touch card numbers — minimize scope, tokenize |
| **AML / KYC** (BSA, FATF, sanctions) | Customer identity, transaction monitoring, screening | onboarding customers or moving funds |
| **SOX** (public co.) | Financial-reporting controls + change management | the system feeds financial statements |
| **PSD2 / Open Banking** (EU/UK) | Strong Customer Authentication, consent, API access | EU payments / account access |
| **Basel III / capital** (banks) | Capital, liquidity, model risk | a regulated bank/lender |
| **MiFID II / market rules** (trading) | Best execution, market-abuse surveillance, reporting | trading/brokerage |
| **SOC 2 / ISO 27001** | Security controls attestation | enterprise/fintech customers require it |

The pack names *which regime applies and what it demands*; current thresholds and
clauses come from the model + primary sources at design time — never hardcode them.

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md` (one definition per entity) and
`skills/interoperability.md`. **The ledger and the wire formats are standardized.**

- **Standards:** **ISO 20022** (modern payments/reporting messaging), **ISO 8583**
  (card auth), **FIX** (trading orders/execution), **Open Banking / FDX** APIs,
  **SWIFT MT** (legacy interbank). Money amounts: **minor units as integers**
  (never floats) with an explicit ISO 4217 currency.
- **Canonical entities:** `Account`, `LedgerEntry` (double-entry: every movement is
  a balanced debit+credit), `Transaction`, `Payment`, `Instrument`, `Order`,
  `Position`, `Party` (KYC subject), `Balance` (derived, never stored authoritative).
- **Money invariant:** the ledger is the source of truth; balances are *projections*
  of entries, and the sum of every transaction's entries is always zero.

## 3. Domain acceptance criteria (added to every task's own)

1. Given a money-movement request, when retried with the same idempotency key, then
   it executes **at most once** (no double-spend / double-charge).
2. Given any posted ledger entry, when written, then it is **append-only and
   immutable**, and its transaction's debits equal its credits.
3. Given any balance shown or acted on, when computed, then it derives from ledger
   entries — never a mutable stored counter treated as truth.
4. Given card data (PAN), when handled, then it stays inside PCI scope
   (tokenized/vaulted); it never lands in logs, analytics, or an LLM prompt.
5. Given customer onboarding or a funds transfer, when it occurs, then AML/KYC
   screening (identity, sanctions, thresholds) runs and its result is recorded.
6. Given end-of-period, when it closes, then automated **reconciliation** proves the
   internal ledger matches the external processor/bank — breaks are alerted, not
   swallowed.

## 4. Threat / harm model

- **Assets:** funds, the ledger's integrity, card/PII data, credit decisions,
  market positions, audit trail.
- **Untrusted inputs:** payment webhooks (spoofable — verify signatures), user
  amounts/currencies, market-data feeds, batch files from processors.
- **Worst plausible harm:** (a) double-spend / lost-update on a retry or race →
  real money lost or created; (b) a webhook replayed or forged → fraudulent credit;
  (c) PAN breach → PCI penalties + fraud; (d) missed AML screening → sanctions
  violation (criminal); (e) a broken ledger invariant discovered at audit →
  restatement. Harm is financial and often criminal, not just downtime.

## 5. Gate overlay

- **G0 (Intake):** name the regime(s); add the §3 acceptance criteria; flag PCI
  scope and whether funds are actually held (money-transmitter licensing).
- **G1 (Architecture):** idempotency keys + the double-entry ledger + reconciliation
  are **design constraints, not features**; card data is tokenized at the boundary;
  webhook signature verification is mandatory; money is integer minor units.
- **G5 (Verification):** the **finance domain sign-off** —
  `roles/security-reviewer.md` (PCI scope, PAN handling, webhook auth) **plus**
  `roles/compliance-officer.md` (AML/KYC, sanctions, data) **plus**, for
  trading/lending, `roles/risk-officer.md` (model/market/credit risk). Any one may
  veto ship.
- **G6 (Release):** reconciliation job proven; incident/chargeback runbook current;
  regulatory reporting wired via `roles/regulatory-affairs.md` where licensed.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/security-reviewer.md` | existing | always (PCI + funds are the crown jewels) |
| `roles/compliance-officer.md` | existing | always (AML/KYC, sanctions, data) |
| `roles/risk-officer.md` | existing | trading, lending, or any model-driven decision |
| `roles/regulatory-affairs.md` | existing | licensing, regulatory reporting, audits |
| `roles/data-architect.md` | existing | modeling the ledger / ISO 20022 entities |

## 7. Glossary

- **PAN** — Primary Account Number (the card number); PCI's protected datum.
- **Double-entry** — every transaction posts balanced debits and credits.
- **Idempotency key** — a client token making a retried write execute at most once.
- **AML / KYC** — Anti-Money-Laundering / Know-Your-Customer screening.
- **Reconciliation** — proving the internal ledger matches an external source of truth.
- **SoD** — Separation of Duties (SOX): the initiator of a change cannot also approve it.
- **Settlement** — the actual movement of funds, distinct from authorization.
- **ISO 20022 / FIX** — payment-messaging / trading-order standards.

## 8. Non-negotiables (domain)

1. **Never move money without an idempotency key, an authorization check, and an
   immutable audit entry.** A retry must never double-spend.
2. **Never break double-entry** — no unbalanced posting, no editing a posted entry;
   corrections are new reversing entries.
3. **Never represent money as a float** — integer minor units + explicit currency.
4. **Never store or log a PAN outside PCI scope** — tokenize at the boundary; never
   send card/account data to an LLM or analytics sink.
5. **Never skip AML/KYC screening** on onboarding or transfer — a bypass is a §5
   escalation, not a shortcut.
6. **Reconciliation is mandatory** — an unreconciled ledger is treated as broken.

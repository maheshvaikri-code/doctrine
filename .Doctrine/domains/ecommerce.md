# Domain Pack — Ecommerce

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building ecommerce changes three things: **checkout is money movement** — a retry
> must never double-charge and inventory must never oversell, so idempotency and
> stock invariants are load-bearing (borrow `domains/finance.md` for the payment
> path); **the storefront is a legal surface** — displayed prices, taxes, and return
> terms must be accurate and the flow free of dark patterns; and **the buyer is a
> data subject** — consent-gated tracking, not silent surveillance. Load this pack
> for storefront/cart/checkout/fulfillment work. **Zero new roles.**

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **PCI-DSS** | Card data at checkout | you take card payments (see `domains/finance.md`) |
| **GDPR / CCPA** | Consumer PII + tracking consent | EU/CA shoppers; any analytics/ads pixel |
| **Consumer-protection law** (FTC, EU CRD) | Price/advertising accuracy, returns, no dark patterns | any consumer sale |
| **Sales tax / VAT (nexus)** | Correct tax by jurisdiction | selling across tax jurisdictions |
| **WCAG / ADA** | Accessible storefront + checkout | any public storefront (see `skills/accessibility.md`) |

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md`, `skills/interoperability.md`, and
`skills/accessibility.md`.

- **Standards:** payment gateway/PSP APIs (tokenized — PAN never touches your
  server), **GS1 GTIN** for catalog, tax-engine APIs (Avalara/TaxJar-style), address
  validation, **schema.org/Product** for SEO.
- **Canonical entities:** `Product`/`SKU`, `Inventory` (reservable), `Cart`, `Order`,
  `Payment`, `Shipment` (see `domains/logistics.md`), `Customer`, `Promotion`,
  `TaxLine`. Money is integer minor units + currency (finance pack invariant).
- **Inventory invariant:** stock is **reserved at add-to-cart/checkout**, not merely
  read — concurrent buyers cannot both purchase the last unit.

## 3. Domain acceptance criteria (added to every task's own)

1. Given a checkout, when retried with the same idempotency key, then the customer is
   **charged at most once** and **one** order is created.
2. Given limited stock, when two buyers race for the last unit, then **at most one
   succeeds** (reservation, not read-then-write) — no oversell.
3. Given a displayed price/tax/shipping/total, when shown, then it matches what is
   charged, and returns/cancellation terms are stated before purchase.
4. Given card data, when handled, then it is tokenized at the PSP boundary — PAN
   never reaches your server, logs, or an LLM (PCI scope minimized).
5. Given tracking/analytics, when loaded, then it is **consent-gated**; the checkout
   is WCAG-accessible and free of dark patterns (no pre-checked add-ons, forced
   continuity).

## 4. Threat / harm model

- **Assets:** buyers' money + card/PII, inventory accuracy, price integrity, the
  order record.
- **Untrusted inputs:** cart contents, coupon/promo codes, prices/quantities from the
  client (never trust client-sent prices), payment webhooks, address input.
- **Worst plausible harm:** (a) double-charge on a retry/race → refunds + trust loss;
  (b) oversell → unfulfillable orders; (c) a client-set price / coupon-stacking
  exploit → revenue loss; (d) card/PII breach → PCI penalties; (e) a price glitch
  auto-honored at scale → mass loss. Financial + consumer-trust harm.

## 5. Gate overlay

- **G0 (Intake):** add the §3 criteria; flag payment method + tax jurisdictions.
- **G1 (Architecture):** idempotent checkout + inventory reservation + server-side
  pricing + tokenized payments + consent management are **design constraints**;
  never trust client-supplied prices/totals.
- **G5 (Verification):** the **ecommerce domain sign-off** — `roles/security-reviewer.md`
  (PCI scope, payment/webhook auth, price-tampering) **plus** `roles/compliance-officer.md`
  (privacy/consent, consumer-protection, tax) **plus** `roles/frontend-engineer.md`
  with `skills/accessibility.md` for checkout a11y. Any may veto.
- **G6 (Release):** payment reconciliation wired (finance pack); refund/chargeback
  path tested; accessibility audit recorded.

## 6. Specialist roles (all existing — the overlay adds none)

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/security-reviewer.md` | existing | PCI scope, payment/webhook auth, price/coupon tampering |
| `roles/compliance-officer.md` | existing | privacy/consent, consumer-protection, tax nexus |
| `roles/frontend-engineer.md` | existing | accessible, dark-pattern-free checkout |
| `roles/data-architect.md` | existing | catalog/inventory/order modeling |

## 7. Glossary

- **PSP** — Payment Service Provider (Stripe/Adyen/…); tokenizes the card.
- **Idempotency key** — makes a retried checkout charge at most once.
- **Oversell** — selling more units than exist (a read-then-write race).
- **Dark pattern** — a UI that tricks users (pre-checked add-ons, forced continuity).
- **Nexus** — the tax-jurisdiction link that creates a collection obligation.
- **Chargeback** — a customer-disputed payment reversal.

## 8. Non-negotiables (domain)

1. **Never trust client-supplied prices, totals, or discounts** — the server is the
   source of truth for money.
2. **Never charge without an idempotency key** or **oversell** — reserve stock, don't
   read-then-write.
3. **Never let a PAN reach your server/logs/LLM** — tokenize at the PSP boundary.
4. **Never misstate price, tax, or return terms**, and never ship a dark pattern —
   the storefront is a regulated consumer surface.
5. **Never load tracking without consent** where consent is required.

# Domain Pack — Quant / Trading

<!-- G1 artifact. A domain overlay: composes with the engineering core, does not
     replace it. Loaded at G1, enforced by a G5 domain sign-off. -->

> Building quantitative trading/research systems changes three things: **a backtest
> that peeks at the future is worse than no backtest** (look-ahead bias manufactures
> fake alpha and real losses); **models are regulated artifacts** (model-risk
> governance, not just accuracy); and **orders touch a live market** where a bug is
> a market-abuse event, not a stack trace. Load this pack in addition to the normal
> routing for signal research, backtesting, execution, or portfolio systems. Adds
> one specialist: `roles/quant-researcher.md`.

## 1. Regulatory / standards regime

| Regime | Governs | Triggers when… |
|--------|---------|----------------|
| **MiFID II** (EU) | Best execution, transaction reporting, algo-trading controls | executing in EU venues |
| **MAR / market-abuse** | Manipulation, spoofing, insider dealing, surveillance | any live order flow |
| **SEC / FINRA, Reg SCI** (US) | Market access controls, system resilience, reporting | US markets/brokerage |
| **Model risk (SR 11-7 / SS1/23)** | Model development, validation, monitoring, governance | a model drives capital/risk/trading decisions |
| **SEC 15c3-5 (market-access)** | Pre-trade risk controls before an order reaches the market | direct market access |

The pack names *which regime applies and what it demands*; thresholds/specifics come
from the model + primary sources at design time — never hardcode them.

## 2. Canonical entities & interoperability

Routes into `skills/data-architecture.md`, `skills/data-engineering.md`
(market-data pipelines), and `skills/interoperability.md`.

- **Standards:** **FIX** (orders/executions), exchange native feeds (**ITCH/OUCH**),
  **FpML** (derivatives), market-data timestamps in **UTC with nanosecond precision**.
- **Canonical entities:** `Instrument`, `MarketData` (tick/OHLCV, **point-in-time**),
  `Signal`, `Order`, `Execution`/`Fill`, `Position`, `Portfolio`, `Backtest`,
  `Model` (versioned, with training window + validation record).
- **Point-in-time invariant:** every research query returns data **as it was known at
  that timestamp** — no restated/survivorship-biased data leaking backward. Money is
  integer minor units (see `domains/finance.md`); returns/PnL are reproducible.

## 3. Domain acceptance criteria (added to every task's own)

1. Given a backtest, when run, then it uses **point-in-time data only** — no
   look-ahead, no survivorship bias — and is **bit-reproducible** from a pinned data
   + code + seed snapshot.
2. Given a signal/model, when proposed, then it ships with an **out-of-sample /
   walk-forward** evaluation, not just in-sample fit, and a model-risk record.
3. Given any live order path, when it exists, then **pre-trade risk controls**
   (max order size, price collars, kill switch, fat-finger limits) gate it before it
   reaches the market.
4. Given order flow, when generated, then it is **market-abuse-safe** (no
   layering/spoofing patterns) and surveillance-loggable.
5. Given execution, when measured, then **best-execution / TCA** evidence is recorded.

## 4. Threat / harm model

- **Assets:** capital, the market's integrity, alpha/IP (models), positions, the
  audit + surveillance trail.
- **Untrusted inputs:** market-data feeds (gaps, bad ticks, outages), model outputs,
  user-set limits, external reference data.
- **Worst plausible harm:** (a) look-ahead bias → a strategy that backtests
  beautifully and loses real money live; (b) a runaway/looping algo → a market-abuse
  event or a flash crash (Knight Capital: ~$440M in 45 min); (c) a missing kill
  switch → unbounded loss; (d) a mis-validated model driving position sizing →
  correlated blow-up. Harm is capital loss + criminal market-abuse liability.

## 5. Gate overlay

- **G0 (Intake):** add the §3 acceptance criteria; declare whether the system places
  live orders (→ market-access controls) or is research-only.
- **G1 (Architecture):** point-in-time data store + reproducible-research harness +
  pre-trade risk gate + kill switch are **design constraints**; models are versioned
  artifacts with a validation lifecycle.
- **G5 (Verification):** the **quant domain sign-off** — `roles/quant-researcher.md`
  (backtest integrity: no look-ahead, out-of-sample evidence) **plus**
  `roles/risk-officer.md` (model risk + limits) **plus** `roles/compliance-officer.md`
  for live order flow (market-abuse surveillance, best-ex, reporting). Any may veto.
- **G6 (Release):** kill switch tested; limits configured; reporting/surveillance wired.

## 6. Specialist roles

| Role | Existing / new | Pulled in when… |
|------|----------------|-----------------|
| `roles/quant-researcher.md` | **new** | signal/model research, backtesting — owns backtest integrity + model validation |
| `roles/risk-officer.md` | existing | model/market/limit risk on any live or capital-driving system |
| `roles/compliance-officer.md` | existing | live order flow (MAR surveillance, best-ex, reporting) |
| `roles/data-engineer.md` | existing | point-in-time market-data pipelines |

## 7. Glossary

- **Look-ahead bias** — using information in a backtest that was not knowable at the
  simulated time; manufactures fake performance.
- **Point-in-time (PIT)** — data as it was actually known at a past timestamp
  (vs later-restated), the antidote to look-ahead.
- **Out-of-sample / walk-forward** — validating a model on data it was not fit on.
- **TCA** — Transaction Cost Analysis (best-execution evidence).
- **Kill switch** — a control that halts all order flow instantly.
- **Slippage** — the gap between expected and realized execution price.
- **FIX** — the standard trading order/execution protocol.

## 8. Non-negotiables (domain)

1. **Never present a backtest without point-in-time data and out-of-sample
   evidence** — look-ahead bias is falsification, not optimism.
2. **Never connect an algo to a live market without pre-trade risk controls and a
   tested kill switch.** No exceptions under deadline.
3. **Never generate order patterns that constitute market abuse** (spoofing,
   layering, wash trades) — even in test against a live venue.
4. **Never treat a model as validated on in-sample fit alone** — model risk is
   governed, versioned, and monitored for drift.
5. **Reproducibility is mandatory** — research pins data + code + seed; an
   irreproducible result does not exist.

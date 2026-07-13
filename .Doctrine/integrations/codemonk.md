---
integration: codemonk
upstream: https://github.com/aroora-ai-labs/codemonk
license: MIT
pinned_version: 0.10.0
discipline: metrics-engineering
verified: 2026-07-12
---

# CodeMonk — Integration

The doctrine's metrology subsystem: zero-dependency change metrics, token
metering, and a graded scorecard for AI-agent coding. ~4,400 LOC, 85
tests, a golden-vector metric spec (CODEMONK-METRICS-v1, 25 hand-computed
vectors) — the same determinism discipline as the rest of this ecosystem.
Not vendored: pinned upstream, thin shim (`skills/metrics.md`).

## What it measures

**CESR** (merged AND survived — no revert/excess churn/incident, staged
decomposition) · **Agent Engagement Level** · **HITL coverage/intensity**
· **HITL Reduction Rate gated on CESR holding** (flags review erosion) ·
**ROI** (net hours after rework/review/incidents) · **Token Churn Ratio**
(spend on retried/superseded/failed attempts) · **cost per landed change**
(joined to outcomes via `item_id`).

## Install & health check

```bash
pip install codemonk            # or pipx; pin ==0.10.0
python -m codemonk demo         # full scorecard on synthetic data
python -m codemonk analyze --repo .   # real metrics from git history
```

Verified on this repo (2026-07-12): 31 agent changes detected via the
Co-Authored-By trailers, CESR 100% (zero reverts — accurate), HITL 0%
from git alone — see the wiring note below for why that number needs
enrichment before it means anything.

## Doctrine wiring

- **item_id discipline:** use the state-plane `task_refs` / brief slug as
  CodeMonk's `item_id` everywhere (commits, token logs, work items) so
  cost joins to landed outcomes.
- **HITL truth:** git carries no review data, so HITL reads 0. The
  doctrine's review reality lives in `docs/reviews/` and `docs/qa/` —
  feed it via the enrichment overlay (`--dump-enrich` shape); a review
  round-trip (VETO → fix → SIGN-OFF) is high-intensity HITL and should
  count as such.
- **Token capture:** `codemonk wrap --otel claude` (verified upstream on
  a real Claude Code run) or point the harness's OTel export at
  `codemonk collect`. Status attrs (`codemonk.status`) make TCR precise.
- **G7 is the consumer:** `codemonk scorecard` output is filed with the
  retrospective (`docs/metrics/`); trends via snapshot + `trend`.
  CESR drops feed the retro's 5-whys.
- **Provenance:** this repo's commit style (Claude co-author trailers)
  is what the agent/human attribution reads — keep the trailer rule.
- **Honesty law applies to numbers:** estimated cost stays labeled
  estimated (CodeMonk's own footer does this — keep it when quoting).

## Boundaries

Metrics never gate an individual merge (that is the council's job — see
`standards/merge-and-promotion.md`); they trend the process for G7.
Baseline fidelity notes: HITL/TCR track their inputs; git-only runs are
heuristics; live GitLab path unverified upstream at 0.10.0.

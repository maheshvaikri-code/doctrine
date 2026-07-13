# Metrics snapshot — 2026-07-13 (post history-rewrite, provenance via enrichment)

Commit trailers were stripped from history (operator decision); agent
attribution now travels in the enrichment overlay (--mark-authorship
agent_assisted, a blanket operator claim true for this repo's whole
history). HITL fidelity label unchanged: verifier fan-out coverage.

# CodeMonk &mdash; Change Metrics & ROI

_44 agent / 0 human changes, window=14d, population=`agent`_

## Headline

| Metric | Value | Note |
|---|---|---|
| **CESR** (agent) | 100.0% | vs human n/a |
| **Agent Engagement Level** | 100.0% | L4 dominant (0.0% autonomous) |
| **HITL coverage** | 22.7% | intensity 0.0% |
| **HITL Reduction Rate** | 80.5% | healthy |
| **ROI** | 317.44x | net 529.07h |

## CESR detail

- Merged: 44, successful elevations: 44
- Staged: merge 100.0% -> survive 100.0% -> incident-free 100.0%
- Churn threshold (tau): 0.25

## HITL trend (reduction)

| Period | HITL | CESR(agent) | n |
|---|---|---|---|
| 2026-07-12..2026-07-12 | 32.1% | 100.0% | 28 |
| 2026-07-12..2026-07-13 | 6.2% | 100.0% | 16 |

## ROI breakdown (hours)

- Gross saved: 530.73
- Rework: -0.0 | Review: -1.67 | Incidents: -0.0
- **Net: 529.07h** (whiplash gap hidden by velocity: 1.67h)

---
_Cost assumptions: author 2.0 min/line, rework 3.0 min/line, review 10.0 min/change, revert 30.0 min, incident 120.0 min. Tune in config; the dollar figure is an estimate, not a measurement._

---
description: Run every doctrine gate (corpus lint, ruff, tests, state chain)
---

Run the full doctrine gate suite and paste REAL output for each step:

1. `python tools/doctrine_lint.py` — corpus self-consistency.
2. `python -m ruff check tools tests` (skip with a note if ruff is not
   installed).
3. `python -m unittest discover -s tests` — the enforcement suite.
4. `python tools/doctrine_state.py verify` — checkpoint chain integrity.

Report PASS/FAIL per gate. A failure routes to the gate that owns the
defect (closed loop) — never weaken a gate to go green. $ARGUMENTS

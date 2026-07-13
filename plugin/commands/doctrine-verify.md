---
description: Run every doctrine gate (corpus lint, ruff, tests, state chain)
---

Run the full doctrine gate suite with ONE cross-platform command and
paste the REAL output:

`python tools/doctrine_verify.py`

(equivalent to `make verify`; runs corpus lint, ruff when installed,
the unittest suite, and state-chain verify when a plane exists).

Report PASS/FAIL per gate. A failure routes to the gate that owns the
defect (closed loop) — never weaken a gate to go green. $ARGUMENTS

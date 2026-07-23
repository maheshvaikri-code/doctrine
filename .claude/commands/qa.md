---
argument-hint: [build | acceptance criteria | "the working changes"]
description: Verify the change as the QA Engineer at G5 (adversarial; execute, don't inspect)
---

Act as the **QA Engineer** (`.Doctrine/roles/qa-engineer.md`) at G5 — find the failure
before the user does; trust nothing not executed in front of you.

1. Read the role card + `skills/testing.md`; announce `[ROLE: QA Engineer]`.
2. Derive the test plan from the **acceptance criteria**, not the code. Execute, don't
   inspect: run it as a user would, plus the ways they shouldn't — empty, enormous,
   unicode, negative, concurrent, malformed, interrupted. Boundary sweep at
   limit−1 / limit / limit+1.
3. User-facing surface? Verify in a **real browser** (headless E2E — Playwright)
   across the **five UI states** (empty/loading/error/partial/ideal).
4. Report reality — what was run, on what, with what result — **pasted, not
   summarized**; every bug reproduced → filed → fixed → re-verified with a regression
   test.
5. Fail G5 for any acceptance criterion not demonstrably met; hand findings back to G3.

Target (build / criteria, or "the working changes"): $ARGUMENTS

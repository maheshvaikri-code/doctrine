# Skill: Loop Engineering

The gates G0–G7 are the company's **outer loop**. This skill governs the **inner
loop** — act → observe → validate → decide, run dozens of times inside G3 (and
inside every fix at G4/G5). Prompt engineering is what you say per call; context
engineering is what you see; loop engineering is **what calls happen, when to
iterate, when to gate, and when to stop**. Undisciplined inner loops are where
fabrication, thrash, and budget burn are born.

## Loop anatomy — five beats, one hypothesis per iteration

1. **Anchor** — restate the acceptance criterion this iteration serves, **verbatim**
   from the brief/plan (paraphrase is where drift starts). One criterion per loop;
   if the criterion itself seems wrong, that is *stop & escalate* to G2, not a
   license to reinterpret it.
2. **Act** — the smallest change producing a *distinguishable* result, encoding
   **one hypothesis** ("I believe X is the cause; this tests it"). Bundled
   hypotheses → split. A "while I'm here" fix is a new G0 finding — note it, stay
   on the criterion.
3. **Observe** — RUN it, PASTE it. Predicted/remembered output is fabrication
   (Non-Negotiable #1). Re-read after every apply (disk is truth, your model is
   stale); observe the **whole** signal — exit codes, warnings, counts — not just
   the line you hoped for.
4. **Validate** — a gate says **no** mechanically, in cost order: compiles/lints →
   tests pass (**all**) → criterion measurably advanced → no regression → still in
   scope. "Looks right" is an opinion, not a gate. **Gate-weakening is forbidden**
   (Non-Negotiable #4) — it corrupts every future loop that trusts that gate.
5. **Decide** — exactly one recorded exit: **iterate** (criterion unmet, budget
   remains, *and a changed hypothesis* — rerunning unchanged code is not iteration)
   · **done** (criterion met *with* the pasted evidence a reviewer could reproduce)
   · **stop & escalate** (budget out, thrash, or the plan is wrong — a first-class
   outcome; an honest "stuck after N, here's the trail" beats attempt N+20).

## Execution caps — loops end by design, not exhaustion

- **Iteration budget**, set on entry: default **5** (Class S) / **10** (M/L) per
  criterion. Budget out → stop, write down what was tried, escalate or return to G2.
- **Thrash detector**: same file edited 3× with no test-delta, or the same error
  twice after "fixing" it → the hypothesis is wrong; go up a level (re-read the
  plan, re-read the actual code, question the diagnosis).
- **Token-jam rule** (extends thrash): two iterations where TPI rises and the
  evidence delta is flat → you are spending more to move less; stop, journal it,
  escalate. (Token units defined in `skills/metrics.md`.)
- **Flaky-test rule**: an intermittent failure is a defect to file, not a retry
  target; one confirming re-run max, never loop until lucky-green.
- Re-anchor every 5 iterations — long loops drift off the brief.

## Loop profiles — declare at entry, stamp in the journal

The caps above are the **default** profile (budget 5/10) for exploratory work. Two
tighter worker profiles + one orchestrator profile:

- **Ratchet** (budget 2–3) — small/known tasks. Every iteration must produce a
  visible evidence delta (gate reached, error class changed, count moved). No delta
  → escalate immediately, even with budget left: a ratchet only moves forward; a
  click that does not advance means the mechanism is jammed.
- **Shutter** (budget 1) — known recipes (scaffolding, config, a documented
  migration). One exposure, no second attempt: a recipe that fails is a premise/
  environment problem a retry cannot fix — the miss *is* the diagnostic.
- **Farm** (orchestrator only) — the dispatch policy for `.claude/agents/` workers
  under `03-parallel-execution.md`: each work package carries a profile stamp
  (`loop: shutter|ratchet|default`) matched to certainty; greens merge, escalations
  are triaged in **one batch**; if ≥ half the farm escalates, the **plan** is wrong
  → halt, return to G2 (never re-dispatch the same packages under bigger budgets).

Heuristic: escalation cost falls as certainty rises — spend budget only where
iteration has information value. (Per-profile token expectations: `skills/metrics.md`.)

## Creative latitude, deterministic evidence

`Agent latitude` controls how broadly a builder searches, not whether the loop
has gates. On `Delivery profile: personal`, absence means `creative`:

- **creative** — use the full default iteration budget for divergent,
  reversible candidates; compare and discard before converging;
- **balanced** — prefer one leading path plus one credible alternative;
- **deterministic** — follow the known recipe with Ratchet or Shutter.

Every latitude still anchors to scope, observes real output, respects the same
thrash/budget limits, and finishes at deterministic validation. Governance may
pin a risky effect; it does not rewrite the unrelated search strategy.

## Validation spine + cross-run persistence

DCCV: spec ↔ story ↔ acceptance criteria ↔ tests ↔ regression ↔ observed behavior;
a failure feeds **back to the level that owns it**, never a patch on top. Before a
session ends mid-loop, append a **loop-journal** line — the resume point:

```text
[<profile> N/B] hypothesis: <one line> | result: <gate, pass/fail> | tok: <in>/<out> (cum) | next: <iterate|done|stop>
```

Token values come from the harness usage fields, never self-estimated. A resumed
loop that repeats a dead end is a doctrine failure, not bad luck.

## Metrics (filed in QA reports / retros; G7 reads them)

Iterations-to-green per criterion; churn ratio (lines rewritten vs surviving to
merge); interventions; escapes (a defect G4/G5 caught that the loop's gates missed
= a missing gate, propose it at G7). The per-loop **token** accounting
(TPI/TTG/TPD/ETS, per-profile expectations, farm rollup) lives with the measurement
discipline in `skills/metrics.md`, computed by CodeMonk (`integrations/codemonk.md`).

## Common failure modes

Victory on partial green ("the important tests pass" — all means all) ·
gate-weakening (forbidden, Non-Negotiable #4) · stale observation (re-read after
every apply) · scope creep mid-loop (new finding = new G0 task) ·
retry-as-strategy (only a changed hypothesis earns another spin) · a shutter task
misclassified from a recipe (shows up as high escalation spend, a routing defect).

## Signature

<!-- SIGNATURE:BEGIN (generated by doctrine_signature - do not edit) -->
- **Roles:** `roles/solo-builder.md`
- **Skills:** `skills/loop-engineering.md` (self)
- **Tools:** —
- **Plugins:** the Doctrine plugin (shared)
- **Workflows:** —
- **Hooks:** —
- **MCP servers:** —
- **Subagents:** —
<!-- SIGNATURE:END -->

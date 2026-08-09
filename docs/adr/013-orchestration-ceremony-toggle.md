# ADR-013: `orchestration-ceremony` toggle — paperwork is togglable, the panel and safety rails are not

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-08-08 · **Status:** accepted (revised same-day — see "Correction" below)
**Deciders:** Chief Architect (direction from the framework owner: swarm dispatch, verifier
councils, and disciplined looping are Doctrine's job, not only Write/Edit/Bash gating —
and like every other restriction in this repo, they should be toggle-controlled, with
nothing enforced when the toggle is off)

## Context

`03-parallel-execution.md` (fan-out width, file-scope discipline, the G4/G5 verifier
panel) and `skills/loop-engineering.md` (iteration budgets, thrash detector, loop-journal)
are both squarely in Doctrine's scope — they already existed as first-class playbooks
before this ADR. What they lacked was a toggle: every rule in both files is prose the
agent follows because the doctrine says to, with no code path enforcing any of it (unlike
`PreToolUse`'s Write/Edit/Bash decisions, which `FEATURES.md`'s `autonomous-verification`
already toggles). Asked directly, the instruction was that gating "must be based on
feature toggle and no restrictions enforced if the toggle is off" — the same philosophy
`autonomous-verification` and the solobuilder Bash exception already embody, extended to
this territory.

Two of those rules are not interchangeable in kind. `03-parallel-execution.md` §1's width
cap and no-shared-files rule exist so two concurrent workers cannot corrupt the same file.
`skills/loop-engineering.md`'s thrash detector and token-jam rule exist so a loop cannot
burn unbounded time and tokens chasing a hypothesis that already failed. Neither is about
who reads the output afterward — turning them off does not remove paperwork, it removes
the thing that stops real damage.

## Correction (same day, before this shipped past local commits)

The first implementation bucketed the **G4/G5 verifier panel dispatch itself** as ceremony
— `off` made self-review a legitimate substitute for dispatching `code-reviewer` /
`security-reviewer` / `qa-engineer`, reasoning it was "the same relaxation `Delivery
profile: solobuilder` already gets." Told directly this was wrong, and it was: dispatching
a fresh-context subagent is a tool call the Orchestrator makes without asking anyone —
autonomous by definition, costing no human friction. Relaxing it bought no autonomy back
and only cost the one thing `02-role-protocol.md`'s "Switching hats is not separation of
duties" section exists to prevent — an author judging its own work under a different hat.
Recorded here rather than quietly rewritten, per this repo's own practice: a wrong first
answer, caught and corrected, is a more honest record than one where the mistake never
happened to be visible (charter: negative findings are wins, not embarrassments).

The actual ceremony — the thing that costs real overhead and produces no safety of its
own — is the **paperwork**: a written work-package brief before dispatch, a loop-journal
line, a formal artifact filed to `docs/reviews/` or `docs/qa/`. None of that is the review;
it's the record of the review. That is what this toggle relaxes.

## Decision

`FEATURES.md` gets a new toggle, `orchestration-ceremony`, defaulting **on** (unlike
`autonomous-verification`, this narrows required *paperwork*, not granted *permission* —
nothing here reaches the `PreToolUse` guard, so it belongs with the backward-compatible
defaults, not the opt-in-only exception).

**`off` removes:** work-package brief documents before a fan-out, loop-journal lines, and
formal `docs/reviews/` / `docs/qa/` artifact filing. The panel's findings are still
obtained and acted on — they're just not written to a permanent file.

**`off` does not touch:** the G4/G5 fresh-context verifier panel dispatch itself — self-
review remains gated to exactly the two doors `02-role-protocol.md` has always named
(subagents technically unavailable; declared `Delivery profile: solobuilder`), both still
requiring the artifact to open with that disclosure. Also unchanged:
`03-parallel-execution.md` §1's fan-out limits (width ≤ 4, no two packages on the same
file, contracts frozen first), `skills/loop-engineering.md`'s execution caps (iteration
budget, thrash detector, token-jam rule, flaky-test rule), Non-Negotiables §7, the §5
escalation list, and the Merge Council (`standards/merge-and-promotion.md`) where that
standard applies.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| A (chosen): paperwork-only toggle, panel dispatch + safety rails fixed | dispatching a subagent costs no autonomy to keep, so nothing is bought by relaxing it; only genuine overhead (briefs, journal, formal filing) is removed | doesn't grant the literal "no restrictions enforced" reading | the literal reading was offered explicitly, tried, and corrected — see Correction above |
| B (tried, corrected — this ADR's own first-shipped design): ceremony includes the panel itself, self-review allowed | matched the instruction's literal wording most closely | turns an autonomous, zero-friction tool call into an optional step, buying nothing while reintroducing "author reviews own work" | corrected same-day on direct instruction: dispatching doesn't "dishonor autonomy" — skipping it isn't required to have any |
| C: one toggle, everything off including the collision guard and loop caps | matches the instruction's literal wording even more completely than B | removes the only thing standing between two parallel workers and a corrupted shared file, or between a stuck loop and unbounded token burn | rejected from the start (present in this ADR's very first version) and still rejected here, unchanged: the instruction's intent, confirmed directly, was never the collision/burn protections |
| D: split into two toggles (dispatch-paperwork ceremony vs. loop-paperwork ceremony) | finer-grained control | no live need for independently loosening one without the other yet; a second toggle is a second thing to keep in sync (echoes ADR-002/ADR-012's drift lesson) | deferred — split later if a real need for independent control shows up |

## Consequences

- **Positive:** the toggle now does exactly what it claims — removes overhead, not
  oversight. The two files that carry the rules name, in their own text, exactly what's
  optional (briefs, journal, formal filing) versus fixed (the panel, the collision guard,
  the execution caps) — no separate document to fall out of sync with them.
- **Negative / debt accepted:** like every rule in `03-parallel-execution.md` and
  `skills/loop-engineering.md`, this toggle is consulted by the agent reading prose, not
  enforced by any hook — an agent (or a session) that simply doesn't read `FEATURES.md`
  gets no signal either way, same as every toggle before it that isn't guard-enforced.
- **Invalidation triggers:** a real need emerges to loosen dispatch-paperwork
  independently of loop-paperwork (→ Option C, split the toggle) or to code-enforce any
  part of `03-parallel-execution.md`/`skills/loop-engineering.md` (→ that new gate gets
  its own toggle-and-floor design, not folded into this one).

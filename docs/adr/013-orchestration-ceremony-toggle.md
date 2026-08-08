# ADR-013: `orchestration-ceremony` toggle — paperwork is togglable, the safety rules are not

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-08-08 · **Status:** accepted
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
the thing that stops real damage. The mandatory G4/G5 verifier panel, work-package brief
docs, and loop-journal entries are a different kind of rule: they produce artifacts, and
skipping them is exactly what `Delivery profile: solobuilder` already does today ("fewer
artifacts, self-review instead of a dispatched panel") without incident.

Presented with this split, explicitly, the decision was: **ceremony only, safety rails
stay** — matching how solobuilder itself already relaxes gating without touching §7.

## Decision

`FEATURES.md` gets a new toggle, `orchestration-ceremony`, defaulting **on** (unlike
`autonomous-verification`, this narrows required *paperwork*, not granted *permission* —
nothing here reaches the `PreToolUse` guard, so it belongs with the backward-compatible
defaults, not the opt-in-only exception).

**`off` removes:** the mandatory G4/G5 fresh-context verifier panel (self-review allowed
instead, on any profile, not only solobuilder), work-package brief documents, loop-journal
lines, and formal `docs/reviews/` / `docs/qa/` artifact filing.

**`off` does not touch:** `03-parallel-execution.md` §1's fan-out limits (width ≤ 4, no
two packages on the same file, contracts frozen first) and `skills/loop-engineering.md`'s
execution caps (iteration budget, thrash detector, token-jam rule, flaky-test rule) — both
files now say so explicitly, cross-referencing `FEATURES.md`. Non-Negotiables §7 and the §5
escalation list are unaffected, as they are by every toggle in this file — concretely, the
`02-role-protocol.md` disclosure duty ("the artifact must open with that disclosure, naming
it an author's self-review… undisclosed self-review presented as a passed gate is a
fabricated verdict under §7 #1") travels with this relaxation exactly as it already does for
the solobuilder and subagents-unavailable doors. `orchestration-ceremony: off` is a third
door to the same rule, not an exemption from it: the toggle grants skipping the panel, never
grants presenting the result as one. `02-role-protocol.md` names all three doors explicitly.
The Merge Council (`standards/merge-and-promotion.md`) is a separate, stricter mechanism
this toggle does not reach.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| A (chosen): ceremony-only toggle, safety rails fixed | matches solobuilder's existing, already-proven relaxation shape; nothing here can corrupt a file or burn unbounded budget | doesn't grant the literal "no restrictions enforced" reading | the literal reading was offered explicitly and not the one chosen — see Context |
| B: one toggle, everything off including safety rails | matches the instruction's literal wording | removes the only thing standing between two parallel workers and a corrupted shared file, or between a stuck loop and unbounded token burn | rejected — the instruction's intent, confirmed directly, was ceremony, not the collision/burn protections |
| C: split into two toggles (dispatch ceremony vs. loop ceremony) | finer-grained control | no live need for independently loosening one without the other yet; a second toggle is a second thing to keep in sync (echoes ADR-002/ADR-012's drift lesson) | deferred — split later if a real need for independent control shows up |

## Consequences

- **Positive:** the relaxation solobuilder already gets ("fewer artifacts, self-review
  instead of a dispatched panel") is now available to any repo or profile via one
  documented switch, consistent with the rest of `FEATURES.md`'s toggle philosophy. The
  two files that actually carry the rules now name, in their own text, exactly what a
  reader can and cannot skip — no separate document to fall out of sync with them (the
  ADR-012 lesson: don't let a decision live only in a place nobody re-reads).
- **Negative / debt accepted:** like every rule in `03-parallel-execution.md` and
  `skills/loop-engineering.md`, this toggle is consulted by the agent reading prose, not
  enforced by any hook — an agent (or a session) that simply doesn't read `FEATURES.md`
  gets no signal either way, same as every toggle before it that isn't guard-enforced.
- **Invalidation triggers:** a real need emerges to loosen dispatch discipline
  independently of loop discipline (→ Option C, split the toggle) or to code-enforce any
  part of `03-parallel-execution.md`/`skills/loop-engineering.md` (→ that new gate gets
  its own toggle-and-floor design, not folded into this one).

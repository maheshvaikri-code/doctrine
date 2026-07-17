# ADR-004: An activation layer so repos reliably wake Doctrine up

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR.
     Builds on: the Engagement Protocol (v0.6.10) + the SessionStart state hook. -->

**Date:** 2026-07-16 · **Status:** accepted (L0+L1 built; L2/L3 roadmap)

## Context

Doctrine is **advisory**: `.Doctrine.md` is loaded into the agent's context and
the Engagement Protocol (v0.6.10) relies on the agent *choosing* to open with
`[DOCTRINE ENGAGED]`, classify the task, and Read the routed roles/skills.
Observed in the field: repos that *have* Doctrine installed frequently do not
*trigger* it — the block is skipped, the routing table is never consulted, and
the right role/skill is not loaded for the specific task. Three failure modes:
(1) **never loaded** — no `@.Doctrine.md` in CLAUDE.md, no `AGENTS.md`, no state
plane; (2) **loaded but not obeyed** — present in context, treated as wallpaper,
especially deep in long sessions or on tasks that don't "feel" doctrine-y;
(3) **half-engaged** — block emitted as theater, the routed skill never Read.

This is the v0.6.10→v0.6.18 retrospective's finding at ecosystem scale (a rule
that is a *value*, not a *gate*, depends on goodwill and is skipped) and the
governance-stack thesis restated (advisory discipline needs a runtime). The one
existing mechanical hook — `SessionStart` state hydration — fires **once**; there
is nothing that re-arms the protocol per task.

## Decision

Add an **activation layer** — mechanical wiring that raises engagement from
*hoped-for* to *reliably prompted*, in layers, cheapest first:

- **L0 — the doctor (`tools/doctrine_awaken.py`).** Audits a repo's activation
  wiring (presence · CLAUDE.md/AGENTS.md load · SessionStart+UserPromptSubmit
  hooks · state plane) and reports every gap with a remediation. Exit non-zero on
  a **critical** gap, so "installed but won't wake up" is diagnosable in one
  command and can gate an install.
- **L1 — per-turn engagement (`tools/doctrine_engage.py` + a `UserPromptSubmit`
  hook).** Re-arms the Engagement Protocol on **every** user message by printing a
  compact reminder that Claude Code injects into context. SessionStart *loads*;
  UserPromptSubmit *re-arms*. This is the highest-leverage fix — it turns "loaded
  once, forgotten by turn 40" into "prompted every turn."

Five invariants are binding:

1. **Awakening is injected, not assumed.** Engagement re-arms per turn via hook,
   not once at session start.
2. **Consumer-safe by construction.** `doctrine_engage` is a silent no-op outside
   a doctrine repo (no `.Doctrine.md` found → prints nothing, exit 0); the plugin
   hook keeps the `os.path.exists` guard; `doctrine_awaken` inspects wiring only —
   no version carriers, no host tests. (Applies the retro's consumer-safety lesson
   at build time, not after a field escape.)
3. **ASCII-only runtime output.** Windows cp1252 pipes crash on stray Unicode.
4. **Right-sized.** The reminder is compact (it ships every turn); hard
   block-enforcement (L3) is opt-in, never the default.
5. **Honest agent-dependent ceiling.** Full per-turn re-arm is a Claude Code hook;
   other agents rely on the `AGENTS.md` always-load floor. The doctor reports which
   layer a given repo actually has, rather than pretending uniform enforcement.

## Layers (built vs roadmap)

| Layer | Mechanism | Status |
|-------|-----------|--------|
| L0 | `doctrine_awaken` activation doctor | **built** |
| L1 | `UserPromptSubmit` engagement hook (`doctrine_engage`) | **built** |
| L2 | `.claude/rules/` path-scoped routing pack (touch auth → security skill, …) | roadmap |
| L3 | `PreToolUse` gates for the §7 non-negotiables (opt-in hard blocks) | roadmap |

## Alternatives considered

| Option | Why not |
|--------|---------|
| A (chosen): inject-per-turn hook + doctor, layered | mechanically re-arms without hard-blocking everything; degrades gracefully across agents |
| B: keep the always-loaded `.Doctrine.md` only (status quo) | *is* the problem — advisory load, probabilistic obedience |
| C: hard `PreToolUse` gates everywhere from day one | too heavy, agent-specific, and annoying; over-ceremony for Class S work — L3 is opt-in for a reason |

## Consequences

- **Positive:** repos re-arm engagement every turn; "installed but not triggering"
  becomes a one-command diagnosis; the installer can end on a provable-AWAKE check.
- **Negative / debt:** L2/L3 are not built (path-rules + hard gates are roadmap);
  the per-turn reminder adds a small context cost each turn (kept compact to bound
  it); non-Claude agents get only the load floor, not the re-arm.
- **Invalidation triggers:** if per-turn injection proves noisy → throttle it; if a
  host agent lacks `UserPromptSubmit` → the doctor reports the degraded floor rather
  than failing silently.

# Skill: Tooling & Tool Selection

> The discipline of **recommending and choosing the best tool or project for a
> need** — a role, a skill, a workflow gate, a plugin, an MCP server, a subagent.
> The rule is **portfolio-first, then vetted external, and never a hardcoded
> "best" that rots.** Recommendations here are *starting points*: verify a tool is
> current and fit-for-context before you commit to it.

## Scope

When any task needs a capability the core doesn't already provide — measurement,
a workforce runtime, action/behavior enforcement, retrieval, a local model, an
MCP server, a demo substrate. Pairs with `standards/dependency-policy.md` (the
adoption gate) and `skills/mcp-tooling.md` (governed MCP servers).

## Principles

- **Portfolio-first.** Reach for a product from our own catalog when one fits the
  need — we know it, we can extend it, and it composes with the rest of the stack.
- **Vetted before adopted.** Any new external dependency passes
  `standards/dependency-policy.md`; adopting/provisioning a paid or external tool
  is a §5 escalation. A recommendation is not an adoption.
- **Prefer proven and boring.** The cheapest tool that fully meets the requirement
  wins (the `skills/ponytail.md` ladder applies to tools too).
- **Recommendations rot — encode the rule, not a frozen list.** "Best tool for X"
  changes fast; this skill names the *stable* portfolio map and the *procedure*,
  and defers per-domain external specifics to the routed discipline skill + a
  current check. Don't hardcode a best-tool-per-role matrix that goes stale.
- **The tool serves the mechanism.** Pick for the concrete need (role/skill/
  workflow/plugin/subagent), and record the choice (an ADR for a Class-L adoption).

## Portfolio catalog — reach for these first

The live integrations Doctrine ships, mapped to the mechanism each serves. Beyond
these, other capabilities — runtime **action** enforcement (make §5 physical),
runtime **behavior** enforcement, **provenance/integrity** (tamper-evident evidence),
**retrieval/KG**, **intent resolution**, **local-LLM serving** — are *bring-your-own*
extension points: pick a tool that fits, vet it via `standards/dependency-policy.md`,
and wire it as a new `integrations/*.md` shim (provisioning/paying is a §5 decision).

| Integration | Serves (mechanism) | Status | Ref |
|-------------|--------------------|--------|-----|
| **CodeMonk** | metrics/metrology — CESR, token cost, HITL (skill: metrics; gate: G7) | wired | `integrations/codemonk.md` |
| **MAPLE** | multi-agent **workforce runtime** — persistent fleet, typed messages (subagents; parallel G3) | wired (opt-in) | `integrations/maple.md` |
| **floci / FDE** | demo/prototype provisioning (role: fde; P1–P6) | wired | `integrations/floci.md` |
| **ponytail** | code-brevity behavior — the 7-rung least-code ladder | wired | `integrations/ponytail.md` |
| **graphify** | deterministic code-structure retrieval — graph before grep | wired | `integrations/graphify.md` |

## Best-fit by mechanism (portfolio-first; external = the routed skill + a current check)

| Need in a… | Wired-first | Then / external anchor |
|------------|-------------|------------------------|
| **role** | the mechanism the role owns (metrics→CodeMonk, workforce→MAPLE, demo→floci) | the role card's own `Loads`; vet new tools via dependency-policy |
| **skill** | a wired integration that serves the discipline (metrics, structure→graphify, brevity→ponytail) | the discipline skill already recommends in-domain — follow it, verify current |
| **workflow (gate)** | G7 metrics→CodeMonk; parallel G3→MAPLE | the gate's owning role card |
| **plugin** | the Doctrine plugin (shared) | tool-native plugins only if they pass dependency-policy |
| **MCP server** | — | `skills/mcp-tooling.md` (governed open-source servers; writes/spends = §5) |
| **subagent** | MAPLE for a persistent fleet | `.claude/agents/` for one-shot fresh-context verifiers/workers |
| **action / behavior / provenance** | — (bring-your-own extension point) | pick a fit, vet via dependency-policy, wire as an `integrations/*.md` shim |
| **retrieval / structure** | `integrations/graphify.md` (code structure) | `skills/ponytail.md` rung 2; a vetted retrieval/KG tool for semantic recall |

## Selection procedure

1. Name the concrete need and the mechanism it serves.
2. **Portfolio-first:** a catalog product fits? Prefer it. Confirm its status
   (wired/proposed/candidate) and interface.
3. Else consider external — the routed discipline skill's recommendation, checked
   for currency; MCP servers via `skills/mcp-tooling.md`.
4. **Vet** anything new against `standards/dependency-policy.md`; provisioning/
   paying is §5.
5. **Record** the choice (an ADR for Class-L adoption; the brief otherwise).

## Do

- Prefer a portfolio tool that fits over a new external dependency.
- Label a recommendation as a recommendation; verify currency before adopting.
- Compose planes: process (gates) · metrics (CodeMonk) are orthogonal to any
  action / behavior / provenance plane you wire — they compose, not compete.

## Don't

- Don't hardcode a "best tool" as permanent truth — it rots; encode the rule.
- Don't adopt (or provision/pay for) a tool on a recommendation alone — that is a
  dependency-policy pass and a §5 decision.
- Don't reach external when a portfolio product already fits the need.

## Common failure modes

Recommending a shiny tool nobody vets; a stale "best of" list treated as current;
adopting past the dependency gate under deadline; reaching external when we own a
fit; confusing "proposed shim" with "wired and verified".

## Signature

<!-- SIGNATURE:BEGIN (generated by doctrine_signature - do not edit) -->
- **Roles:** — (cross-cutting; applied by every role)
- **Skills:** `skills/tooling.md` (self)
- **Tools:** —
- **Plugins:** the Doctrine plugin (shared)
- **Workflows:** —
- **Hooks:** —
- **MCP servers:** —
- **Subagents:** —
<!-- SIGNATURE:END -->

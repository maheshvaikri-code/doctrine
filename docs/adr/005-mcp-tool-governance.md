# ADR-005: Governed use of external MCP servers (open-source-first)

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR.
     Companion: skills/mcp-tooling.md. Relates to standards/dependency-policy.md + §5. -->

**Date:** 2026-07-16 · **Status:** accepted

## Context

Feature development increasingly happens through **external MCP servers** — an agent
reaches GitHub (repo/PR/actions), Docker (containers), cloud providers (provision/
deploy), Sentry (error monitoring), and other domain tools over MCP. Doctrine already
*ships* an MCP server (`doctrineos`) and its adapters wire it into agents (§05-packaging),
but the corpus had **no discipline for the reverse — consuming other MCP servers**.
`skills/mcp-tooling.md` was absent; grep for `Sentry` returned zero hits.

Two facts make this a doctrine concern, not mere tool-wiring:

1. **An MCP tool call can take a real, consequential action** — merge a PR, deploy to
   prod, delete a container, *spend money* provisioning a resource, send a message.
   Those are exactly the §5 escalation triggers (irreversible / external / paid) and
   the non-negotiables (never commit secrets).
2. **Adopting an MCP server is adopting a dependency** — it should clear the same bar
   as any dependency (`standards/dependency-policy.md`), and open-source is preferred
   for auditability and self-hosting.

## Decision

Add `skills/mcp-tooling.md` to govern MCP *consumption* for **any** feature development
(not DevOps-only). Four invariants are binding:

1. **Open-source-first.** Prefer an open-source MCP for a need (auditable, self-hostable,
   vettable). An MCP server is a dependency and clears the dependency-policy bar; a
   closed/hosted data-touching MCP is a §5 external-dependency decision.
2. **Intended, available, else fall back.** Match the MCP to the task's intent; use it
   only if a suitable server is wired; otherwise fall back to the CLI/SDK the work-skill
   assumes. **Never block a task because an MCP is absent** — the tool is a convenience,
   not a prerequisite.
3. **MCP actions are governed actions.** Read-only / least-privilege by default; every
   write / deploy / spend / delete / send is a §5 escalation; secrets live in the MCP
   server's auth config, never the repo; the action stays attributable + tested. The
   gate is on the **action**, not the tool.
4. **No skill-per-server.** One principle-first skill; the catalog is illustrative and
   grows by MCP-registry entry, not by new files that rot with each provider's API.

## Alternatives considered

| Option | Why not |
|--------|---------|
| A (chosen): one governed, open-source-first, principle-first `mcp-tooling` skill | durable; puts the governance where the risk is (the action) without a rotting per-server catalog |
| B: a skill per MCP server (`github-mcp.md`, `docker-mcp.md`, …) | rots as each provider's API changes; multiplies files; still misses the shared governance |
| C: no doctrine coverage — let agents use MCP ad hoc | the status quo gap; consequential actions (deploy/spend/delete) go ungated, secrets leak, closed MCPs adopted unvetted |

## Consequences

- **Positive:** consequential MCP tool-use is *gated, not laundered*; open-source-first
  keeps the tool layer auditable and self-hostable; the discipline is available to every
  role and any feature, via the routing table, without new per-tool files.
- **Negative / debt:** MCP maturity varies by provider — some concerns fall back to the
  CLI (honest, documented in the skill); enforcement is **advisory** until a mechanical
  gate lands (a `PreToolUse` hook or external pre-execution authorization on MCP
  actions — the natural L3 successor, cf. ADR-004).
- **Invalidation triggers:** if an MCP becomes the *only* viable path for a consequential
  action, the §5 gate still applies (the gate is on the action); if a mechanical MCP-action
  gate is built, this skill becomes its policy layer rather than the sole control.

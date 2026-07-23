# Domain Pack — Agentic AI

<!-- G1 artifact. A deployment-pattern security-review archetype: overlays the
     shared control backbone skills/ai-security.md with what is DISTINCT about
     autonomous, tool-using agents. Loaded at G1, enforced by a G5 sign-off. -->

> Security-review archetype for **autonomous, tool-using agents** — systems that
> plan, call tools, keep memory, and *act* with limited human oversight. Load with
> `skills/ai-security.md` (the shared backbone). What is distinct here: the model
> doesn't just answer, it **takes actions**, so **excessive agency** and
> **indirect prompt injection through what the agent reads** are the dominant risks.
> Doctrine's own §5, budget gate, loop caps, and STIX/Contegrity map directly onto
> these controls.

## 1. Regime (adds to `skills/ai-security.md`)

OWASP LLM Top 10 (esp. **Excessive Agency**, **Prompt Injection**), MITRE ATLAS,
NIST AI RMF; EU AI Act tier by *what the agent can do*. Emerging agentic-threat
guidance (multi-agent, autonomy).

## 2. Canonical entities & interoperability

- **Entities:** `Agent`, `Tool` (+ its permission scope), `Plan`/`Task`, `Memory`
  (short + long term), `Action`, `Trace` (immutable action log), `Guardrail`.
- **Interop:** tool/function-calling schemas, MCP servers (`skills/mcp-tooling.md`),
  the agent runtime. Tool calls are the trust boundary between "the model decided"
  and "the world changed."

## 3. Domain acceptance criteria (added to the task's own)

1. Given any tool, when granted, then the agent holds the **least privilege** the
   task needs — scoped, not standing broad access; high-impact tools are allow-listed.
2. Given a **high-impact or irreversible action** (spend, delete, deploy, external
   send), when the agent attempts it, then it is **gated** — a §5 escalation /
   human-in-the-loop, enforced at the action boundary (STIX where wired), not by the
   agent's good behavior.
3. Given content the agent **reads** (tool output, retrieved docs, other agents),
   when it enters context, then it is treated as **untrusted** — indirect prompt
   injection is assumed; instructions in data are not obeyed.
4. Given the agent loop, when it runs, then **cost/iteration bounds + a kill switch**
   apply (the loop caps + budget gate), so a runaway or looping agent cannot burn
   budget or spam actions.
5. Given any agent action, when taken, then it is **logged for non-repudiation**
   (who/what/when/why), tamper-evident (Contegrity where wired).

## 4. Threat / harm model

- **Assets:** everything the agent's tools can touch — funds, data, infra, external
  systems; the agent's memory + plan integrity.
- **Untrusted inputs:** user goals, **tool outputs**, retrieved documents, other
  agents' messages, its own memory (poisonable).
- **Worst plausible harm:** (a) **excessive agency** — a broadly-permissioned agent
  tricked (via indirect injection) into a destructive/exfiltrating action; (b)
  **memory poisoning** — planted content steers all future decisions; (c) a runaway
  loop spending money or hammering an API; (d) multi-agent collusion/confused-deputy
  crossing a trust boundary. Harm is real-world action, not a bad answer.

## 5. Gate overlay

- **G0:** classify the agent's blast radius (what its tools can do) + EU-AI-Act tier.
- **G1:** least-agency tool scoping, action-gating for high-impact ops, untrusted-read
  handling, loop/cost bounds, and an action-provenance log are **design constraints**.
- **G5:** the **agentic sign-off** — `roles/security-reviewer.md` (least agency,
  injection red-team, action gating) **plus** `roles/risk-officer.md` (autonomy/blast
  radius). Any may veto. Red-team indirect injection through tool output, with evidence.
- **G6:** kill switch tested; action log + alerting live.

## 6. Specialist roles (all existing — no new roles)

| Role | Pulled in when… |
|------|-----------------|
| `roles/security-reviewer.md` (+ `skills/ai-security.md`) | always — least agency, injection, action gating |
| `roles/risk-officer.md` | autonomy / blast-radius risk |
| `roles/ml-engineer.md` | the agent's model/prompt/tool wiring |

## 7. Glossary

- **Excessive agency** — more tool/permission/autonomy than the task requires.
- **Indirect prompt injection** — instructions hidden in content the agent *reads*.
- **Memory poisoning** — planting content that corrupts future agent decisions.
- **Confused deputy** — the agent misused as a proxy for an action the caller couldn't do.
- **Human-in-the-loop (HITL)** — a required human approval before a gated action.

## 8. Non-negotiables (domain)

1. **Never grant standing broad tool/permission scope** — least agency, scoped per task.
2. **Never let the agent take a high-impact/irreversible action without a gate** (§5 /
   HITL, enforced at the action boundary).
3. **Never trust what the agent reads** — tool output and retrieved content are
   untrusted; instructions in data are not commands.
4. **Never run an agent unbounded** — cost/loop limits + a tested kill switch, always.
5. **Never ship without an injection red-team** — a guardrail you didn't attack is decoration.

# DoctrineOS — the Activation Model

**Phase 0 deliverable.** The trigger specification: which resource loads, on what signal, at what threshold.
**Date:** 2026-08-25 · **Status:** G1 design, for approval

---

## Why this is the product

Packs answer *what is installed*. They say nothing about *what loads, when* — and that second question is the whole thing, because **context is the agent's scarce resource** (agent fact 1).

v1 got this half-right and half-wrong:

- **Right:** progressive disclosure was stated as the design principle, and `.Doctrine.md` §6 is a routing table — a genuine attempt at conditional loading.
- **Wrong:** the routing table is **prose the model consults**. Whether a skill loads depends on the model reading a 77-row table and deciding. That is not a trigger; it is a suggestion. It costs tokens on every task whether or not anything fires, and it fires inconsistently because it is a judgement call every single time.

**The fix is to make activation computed, not decided.** A deterministic engine evaluates the signals and emits exactly the resource set this task needs. The model receives an answer, not a table.

That single change is also what makes DoctrineOS **agent-portable**: the engine runs in the binary, so the same activation logic serves Claude Code, Codex, Cursor, and Aider. Only the *delivery* differs, not the decision.

---

## The signal taxonomy

Six signal classes, ordered by how reliable they are. Reliability determines what a signal is permitted to trigger.

| # | Signal | Example | Reliability | Cost to evaluate |
|---|---|---|---|---|
| **S1** | **Repo facts** | `pyproject.toml` exists → Python profile; `.github/workflows/` → CI is Actions; `migrations/` exists → this repo has a schema | **Deterministic** | Once per session, filesystem |
| **S2** | **Path touched** | write to `migrations/**` · `**/auth/**` · `.github/workflows/**` · `*.tf` · `Dockerfile` | **Deterministic** | Per tool call, free |
| **S3** | **Tool + payload** | `Bash` running `git push --force` · Write containing an API key · Edit adding `@skip` | **Deterministic** | Per tool call, free |
| **S4** | **Declared class / profile** | Class L · `Merge profile: enterprise` · `Delivery profile: solobuilder` | **Declared** — trustworthy but human-set | Once per task |
| **S5** | **Gate transition** | entering review · attempting to end a turn · tagging a release | **Deterministic** | Per event |
| **S6** | **Intent (task text)** | "deploy this" · "why is X failing" · "design the schema" | **Weak** — inference | Per task, cheap |

**The threshold rule, and it is the core of the design:**

> **A signal may only auto-fire a resource whose cost is proportional to that signal's reliability.**

| Signal reliability | May auto-fire | May NOT auto-fire |
|---|---|---|
| **Deterministic** (S1–S3, S5) | anything, including a refusal or a dispatch | — |
| **Declared** (S4) | reads, dispatches, template instantiation | refusals |
| **Weak** (S6) | **reads only** — a skill file into context | dispatch, refusal, domain composition |

This is why v1's ritual felt like a tax: it fired on **S6-and-weaker** (the existence of a task) but charged **S4-level** cost (a full engagement block, class declaration, role announcement) on every turn. Wrong signal, wrong price.

---

## The activation contract

Every resource — skill, lens, template, pack, hook — declares how it wants to be reached. Machine-readable, versioned, and shipped with the resource.

```toml
# packs/core/skills/database.md  ->  frontmatter or sidecar
[activate]
on          = ["path:migrations/**", "path:**/schema.*", "intent:migration|schema"]
provides    = "skill"          # skill | lens | template | subagent | overlay
cost        = "read"           # read | dispatch | compose | refuse
reliability = "deterministic"  # highest reliability among its `on` signals
```

The engine's contract is one function:

```
resolve(task_context) -> { read: [...], adopt: [...], dispatch: [...], refuse: [...] }
```

`task_context` = repo facts (S1) + touched paths (S2) + tool payload (S3) + declared class (S4) + gate (S5) + task text (S6).

**Determinism is a hard requirement.** Same context in, same set out — so it is testable, diffable, and explicable. `doctrineos why <resource>` must be able to answer *"because you touched `migrations/0007.sql`, and `database` activates on `path:migrations/**`."* A trigger that cannot explain itself is a trigger nobody will trust.

---

## The six activation tiers

### Tier 0 — Always (session start)
**Fires:** SessionStart. **Budget: hard cap, ~2k tokens.**

- The kernel law — the short version, not 77 rows
- **Hydrated state** (agent fact 2 — this is the one thing an agent cannot reconstruct)
- Installed-pack manifest (names only, not contents)

`obra/superpowers` won at 277k stars on *"pulls in one doc of fewer than 2k tokens"*. That is the bar, and it is the entire per-session tax.

### Tier 1 — Repo shape (S1, once per session, cached)
Language profile, CI system, cloud target, whether a schema/IaC/frontend exists. Cheap, stable, and it prunes the candidate set for every later tier.

### Tier 2 — Path (S2, per tool call) — *the workhorse*

| Path touched | Activates |
|---|---|
| `migrations/**`, `**/schema.*` | database lens + `skills/database.md` |
| `**/auth/**`, `**/*credential*`, `.env*` | security lens + `skills/security.md` |
| `.github/workflows/**`, `.gitlab-ci.yml` | `skills/cicd.md` |
| `*.tf`, `Dockerfile`, `k8s/**` | `skills/iac.md` |
| `**/*.test.*`, `tests/**` | `skills/testing.md` |
| `docs/adr/**` | ADR template |
| `packs/domains/healthcare/**` present + `**/patient*` | healthcare overlay |

Deterministic, free to evaluate, and it generalises Roo Code's proven `fileRegex` mechanism from *restriction* to *activation*. **The same map does double duty:** a lens's paths define both what it loads *and* what it may write. One declaration, two enforcements.

### Tier 3 — Risk (S3, per tool call) — *the guard*
Secret pattern → **refuse**. Protected path → **refuse**. §5 verb (force-push, publish, spend, destroy) → **escalate**. Test-weakening edit → **escalate**.

Deterministic signals, highest stakes, so they are permitted to refuse. This is v1's guard, kept, narrowed to where it is sound.

### Tier 4 — Gate (S5, per transition)
Entering review → **dispatch verifiers** (default posture, not ceremony — agent fact 4: parallelism is nearly free). Attempting to end a turn on a declared M/L task → **Stop gate** checks evidence exists. Release tag → gold gate.

### Tier 5 — Intent (S6, per task) — *reads only*
"why is this failing" → `debugging`. "design/architecture" → `architecture` + ADR template. "deploy/release" → *suggests* the release path but **cannot itself escalate** — the actual refusal comes from Tier 3 when a §5 verb is really invoked.

Weak signal, so bounded to the cheapest, most reversible action: putting a file in context.

### Tier 6 — Explicit (always available)
`/role <x>`, `/soc-triage`, `doctrineos add <pack>`, `doctrine: <task>`. The human overrides everything. Never automatic, always reachable.

---

## Cross-agent delivery — one engine, four transports

The engine is host-agnostic. Only delivery differs, and that is the portability claim made concrete.

| Host | Tier 0 | Tiers 2–3 | Tier 4 | Tier 5 |
|---|---|---|---|---|
| **Claude Code** | `SessionStart` hook | `PreToolUse` hook | `Stop` hook | `UserPromptSubmit` hook |
| **Codex / Cursor / Aider** | `AGENTS.md` points at the CLI | `doctrineos check --tool …` (agent-invoked, or a git pre-commit backstop) | pre-commit / CI | CLI |
| **Any MCP host** | `doctrineos.context()` tool | `doctrineos.check()` | `doctrineos.gate()` | `doctrineos.context()` |
| **CI (any)** | — | `doctrineos verify` | required check | — |

**The honest asymmetry, stated up front:** only Claude Code can *refuse before execution*, because only it exposes a blocking pre-execution hook. Everywhere else, Tier 3 degrades from **refuse** to **detect at commit/CI**. That is a real capability difference and the README must say so plainly rather than implying uniform enforcement. What *is* uniform across all four: Tiers 0–2 and 4–5, and every artifact at layer 4.

---

## What this fixes, concretely

| v1 problem | Activation model fix |
|---|---|
| 77-row routing table read every task | Tier 0 caps at ~2k tokens; routing is computed, not read |
| Ritual charged on every task | Tier price matches signal reliability; Class S pays nothing |
| Three marketing skills existed but were routed from nowhere | A resource without an `[activate]` block is **unreachable and fails the build** |
| Model decides whether to load a skill — inconsistently | Engine computes it — deterministically, and can explain why |
| 69 skills on the first screen | Only the kernel's activations exist until a pack is added |
| Domain overlays never fire | They now fire on real signals (S1 + S2), not on remembering they exist |

---

## Open questions for Phase 0 approval

1. **Frontmatter or sidecar?** An `[activate]` block inside each `.md` keeps resource and contract together (one file to move); a sidecar `.toml` keeps the Markdown clean for humans. **Recommendation: frontmatter** — a contract that can drift from its resource will.
2. **Is S6 intent-matching worth it at all?** It is the only weak signal in the system. **Recommendation: ship Tier 5 last**, and only if Tiers 1–4 leave a real gap. Keyword matching that fires wrongly is worse than not firing.
3. **How does a lens's write-scope interact with the vendor's permission layer?** A lens refusing an out-of-scope write is Tier 3. The vendor's `permissions.deny` outranks it. **Recommendation:** lens scope is an *additional* constraint, never a grant — it can only narrow, never widen.
4. **Pack granularity** — 8 packs is a guess. Install telemetry answers it later; hold the split loosely.

---

## Phase 0 asks for exactly three decisions

1. **Approve the activation model** — six tiers, the threshold rule, the `[activate]` contract.
2. **Approve the Go spike** — with the reversal clause: if it does not measurably beat Python on this machine, the runtime decision flips on evidence.
3. **Approve the Bucket-3 correction list** — the six defects fixed rather than carried forward (`maple` stamp, two inert toggles, ritual pricing, company metaphor, guard layer positioning, mid-workflow gap).

Nothing is built until these three are settled.

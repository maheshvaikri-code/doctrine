# DoctrineOS — thesis, stack, and rebuild plan

**Status:** G0/G1 proposal. Nothing is built yet. **Date:** 2026-08-25
**Supersedes in spirit:** `.Doctrine.md`'s founding line — *"This repository is operated as a complete software company staffed by AI."*

---

## Part 0 — The thesis: of the agents, by the agents, for the agents

Doctrine v1 was built on a metaphor: **a software company, staffed by AI.** Roles, hats, gates, ceremonies, sign-offs, a charter. It is a human organisational chart projected onto a language model.

That metaphor produced real value — the gates, the evidence discipline, the anti-fabrication law all came from it. But it also produced 41 role cards, a mandatory engagement ritual on every task, and a per-task token tax. And the market has already returned a verdict on the metaphor: **BMAD-METHOD, at 52,230 stars, deleted its QA agent and its Scrum Master agent** and folded them into the developer. AWS shipped **Quick Spec** with *"no approval gates between phases."* Both are the same signal — the human org chart does not fit the thing it is being draped over.

**The reframe:** stop modelling a company. Model the agent's *actual constraints and actual affordances*. There are five that differ materially from a human engineer, and every one of them has a design consequence.

### The five agent facts

| # | Fact about agents (not humans) | Design consequence |
|---|---|---|
| **1** | **Context is the scarce resource** — not time, not headcount. Every token spent on ritual is a token not spent on the problem. | Progressive disclosure is the *architecture*, not a nicety. Nothing loads until the task needs it. The engagement ritual is a tax and must justify itself per token. |
| **2** | **Memory resets; it does not accumulate.** A human carries yesterday forward. An agent starts at zero, every time. | External, hash-chained, auto-hydrated state is **first-class product**, not an add-on. This is the one thing v1 got structurally right. |
| **3** | **Every action is a typed tool call** — interceptable at a boundary that does not exist for humans. A human acts through fingers; an agent acts through a JSON payload you can read before it executes. | Enforcement belongs at the call boundary, and decisions must be **machine-readable**. This affordance is unique to agents and is the reason a repo-native guard is even possible. |
| **4** | **Parallelism is nearly free.** Four fresh reviewers cost seconds, not four salaries. And an agent can *genuinely* forget writing the code — something no human reviewer can do. | Fresh-context verification is the **default**, not ceremony. Separation of duties is *easier* for agents than for humans. v1 treats this as a gate; it should be the resting state. |
| **5** | **The failure mode is confabulation, not laziness.** Under pressure an agent invents a plausible answer rather than reporting "blocked". | "Done" must be **mechanically checkable**, never narrated. Evidence beats assertion at every gate. This is the deepest thing v1 understood. |

**The one-line thesis:** *DoctrineOS is not a company an agent works inside. It is the memory, the evidence, and the refusal an agent does not have on its own.*

Three nouns — **memory, evidence, refusal** — map exactly onto facts 2, 5, and 3. That is the product. Everything else in v1 is either an implementation of one of them or is ceremony that should be optional.

### What this thesis deletes

- **The company metaphor.** No charter-as-values-statement, no org chart, no "hats."
- **Roles as identities.** A role is not a person to become; it is a **lens**: a set of checks + a tool grant + a file scope. Roo Code proved the mechanism with `fileRegex` — the *runtime* throws when a lens writes outside its scope. A lens is a function; a persona is a costume. BMAD deleted costumes; functions survive.
- **Mandatory ceremony.** The `[DOCTRINE ENGAGED]` block on every task is a per-turn token cost paid before any work. It should fire when a task is *risky*, not when a task *exists*.

### What this thesis keeps and promotes

- **Hash-chained state** (fact 2) — promoted from feature to foundation.
- **Evidence-gated completion** (fact 5) — promoted from prose to a runtime check.
- **Point-of-action refusal** (fact 3) — kept, but *narrowed* to where it is sound (writes), and honest about where the vendor's permission layer outranks it.
- **Dispatched fresh-context verification** (fact 4) — promoted from a G4/G5 gate to the default posture, plus the thing nobody has built: **proof it happened**.

---

## Part 1 — The four-layer model (where DoctrineOS lives)

| Layer | Owner | Answers | DoctrineOS |
|---|---|---|---|
| 1 Containment | a sandbox / VM / container | *What can the process physically touch?* | **Not ours.** Select one; never claim to be one. |
| 2 Permission | the agent vendor (`permissions.deny`, managed settings) | *May this agent do X, anywhere?* | **Not ours, and not a gap.** Defer to it; a deny rule outranks any hook. |
| **3 Process** | **DoctrineOS** | *Has this passed the gates, by whom, with what evidence?* | **Owns it.** |
| **4 Provenance** | **DoctrineOS** | *Can I prove afterwards what was decided and reviewed?* | **Owns it.** No competitor sells this. |

v1's guard operates at layer 2 — where it is weakest, duplicates the vendor, and is **switchable off by `allowManagedHooksOnly`**. Layers 3–4 cannot be switched off, because the artifacts are committed files.

---

## Part 2 — The stack

### Requirements, derived not assumed

1. **Hot path must be invisible.** A hook runs per prompt and per write. Measured on this machine: bare Python **1,875 ms**; `node -e ''` **391 ms**. Even allowing that this box taxes all spawns (~15× slow), Python is ~5× worse than Node here, and both are far from free.
2. **Must run where agents run** — macOS, Linux, Windows, and in CI.
3. **Zero install friction** — an install step is an adoption cliff.
4. **Auditable.** A governance tool that says "denied" must be inspectable. This is a real constraint, not a preference.
5. **No runtime dependency** if achievable — a Node shop should not need Python to run gates that have nothing to do with their stack. v1 charges exactly that tax.

### Recommendation: **Go for the binary, Markdown for the corpus, nothing else**

| Option | Startup | Deps | Verdict |
|---|---|---|---|
| Python (v1) | ~1.9 s here | needs Python | **Reject.** Couples every consumer to a runtime unrelated to their stack. |
| Node | ~391 ms here | needs Node | **Reject as primary.** Guaranteed under Claude Code, *not* under Codex/Cursor/Aider/CI. Trades one runtime assumption for another. |
| **Go static binary** | **~2 ms** | **none** | **Recommend.** |
| Rust static binary | ~1 ms | none | Defensible; marginal gain over Go, slower iteration for a solo maintainer. |

**Why Go, on merits:**
- **Single static binary, zero runtime.** Kills requirement 5 outright — the Node shop, the Rust shop, and the CI container all just run a file.
- **Cross-compilation is trivial** (`GOOS`/`GOARCH`): six targets from one CI job. Rust needs more toolchain care; Python needs none but ships no binary.
- **~2 ms startup** makes the hot-path tax vanish — this is the single measurable defect in v1's daily experience.
- **Stdlib covers the whole surface**: `encoding/json`, `crypto/sha256`, `os/exec` (git), `path/filepath`, `net/http` (MCP over stdio needs none of it). The zero-dependency ethos survives intact.
- **Auditability is preserved** by shipping source + reproducible builds + `go install` as a first-class path. The binary is a convenience; the source is the truth. (This is the honest answer to requirement 4 — a compiled governance tool must be buildable from source by the person it governs.)

**Distribution, all three at once, no runtime required for any:**
```
GitHub Releases  ->  6 static binaries, checksummed
go install       ->  for Go shops
npx doctrineos   ->  thin JS wrapper that downloads the right binary
                     (rides Claude Code's bundled Node; no Node code runs the gates)
```

**The corpus does not move.** It is Markdown — 66% of the value, portable as-is, and the layer every agent already reads.

---

## Part 3 — Port / redo / drop ledger

Nothing is carried across on sentiment. Each line has a reason.

### PORT — proven, and the moat

| From v1 | Why it survives |
|---|---|
| **Gold records + hash chain** (`doctrine_gold`) | The one mechanism the entire competitive survey found **no equivalent for**. Content-pinned verdicts, "no verdict, no gold". This is the moat. |
| **State plane** (`prev_sha256` chain, distillates, hydration) | Directly implements agent fact 2. Nobody else ships hash-chained session state. |
| **Secret patterns + protected-path rules** | Battle-tested through four adversarial review rounds. Port the *rule sets*, not the shell parser. |
| **The corpus's best skills** | `loop-engineering`, `engagement-engineering`, `sandboxing`, `ai-slop`, `debugging`, `testing`, `security` — these are genuinely agent-native. Port with editing. |
| **ADR/plan/review/QA templates** | The artifacts are the product at layer 4. |
| **`AGENTS.md` adapter model** | Rides a Linux Foundation spec across 20+ tools. Free distribution. |

### REDO — right idea, wrong implementation

| From v1 | What changes |
|---|---|
| **Runtime** (6,469 lines Python) | → Go. See Part 2. |
| **41 roles** | → **~8 lenses**, each = checks + tool grant + **file scope enforced at the call boundary** (Roo `fileRegex` pattern). A lens that writes outside scope is refused, not reminded. |
| **The engagement ritual** | → fires on **risk**, not on existence. Class S/M ordinary work gets no preamble. |
| **7 gates G0–G7** | → **3 gates**: `intent` (what and why), `build`, `evidence` (reviewed + checkable). L-class work can still expand to the full seven; the default is three. |
| **Guard** | → Write/Edit only, honest about layer 2, **plus** a `Stop`-event Definition-of-Done gate — the band v1 leaves to narration. |
| **FEATURES.md** | → every toggle must be **read by code or deleted**. v1 ships two that nothing reads. |
| **Installer** | → one binary, one command, no `--tool` matrix at first run. |

### DROP — costs more than it returns

| From v1 | Why |
|---|---|
| **The "software company" framing** | The metaphor that produced the surface-area problem. BMAD's receipt. |
| **Startup/founder-ops roles** (7 cards) | Marketing, sales, legal, investor-relations are not agent-native software development. They belong in a separate pack, not the core. |
| **Governance heads** (4 cards) | Same — an enterprise overlay, not the core product. |
| **Domain overlays in core** (16) | Genuinely valuable, wrong default. Ship as an installable pack. |
| **`Workforce runtime: maple` stamp** | Contradicts the corpus's own corrected position; ADR-012 class defect. Do not port. |
| **Fleet view, dashboard, metrics bridge** | Real work, but not the first-run product. Later, or separate. |

**Net first-run surface:** ~8 lenses, 3 gates, ~20 core skills, one binary, one command. Everything else installable. `obra/superpowers` won at 277,129 stars on *"one doc under 2k tokens"* — that is the bar for the first screen.

---

## Part 4 — The three things that make it best-in-class

Not marketing. Each is a mechanism nobody currently ships, verified by this week's survey.

**1. Enforced reviewer identity — the empty slot.**
No open-source project mechanically enforces *the builder cannot approve its own build*. `flow-next` (687★) enforces *dispatch* but not *identity*. GitHub blocks PR self-approval but keys on *account*, defeated by one bot token. Everyone else checks *whether* a review exists, never *who wrote it*.
**Build:** every verdict carries a reviewer stamp (agent type + dispatch id). The evidence gate **refuses when the stamp is absent or equals the builder's.** Verified this session: dispatched subagents *do* trigger the guard, so the mechanism is real.

**2. Definition-of-Done as a runtime check.**
v1 enforces at write-time and release-time and **nothing in between**. This session proved the cost: seven files left untracked would have shipped a corpus claiming 69 skills to a consumer receiving 62 — caught only by a dispatched reviewer.
**Build:** a `Stop`-event gate that refuses to end a turn when the declared class's evidence is missing. Must fail *open* on its own errors.

**3. Portable provenance.**
Managed settings are Claude-only; Team Rules are Cursor-only. A CISO in a mixed shop configures three consoles and gets three unrelated audit trails — and every one of them is a *SaaS account* log (Cursor's is 19 event types covering auth, membership, API keys). None records that the security reviewer signed off on the auth change.
**Build:** keep the hash chain, make the records the thing you point at.

---

## Part 5 — Sequence

**Phase 0 — decide (you).** Approve or amend this thesis, the Go choice, and the drop list. Nothing is built until then.

**Phase 1 — the spike (small, throwaway-able).** One Go binary that does exactly three things: `guard` (PreToolUse deny), `stop` (DoD gate), `verify`. Prove the ~2 ms startup on this machine and that the hooks fire from Claude Code. **If the spike doesn't beat Python measurably here, the Go decision reverses on evidence.**

**Phase 2 — port the moat.** Gold records + state plane into Go, with the v1 Python suite kept as a differential oracle: both implementations run the same fixtures and must agree byte-for-byte. That is how a rewrite avoids silently losing four rounds of adversarial hardening.

**Phase 3 — the corpus edit.** 69 skills → ~20 core + packs. 41 roles → ~8 lenses. Three gates. This is editorial work and the highest-risk-of-regret step; it is deliberately after the runtime is proven.

**Phase 4 — the first screen.** README, one-command install, and the refusal demo as a checked-in `vhs` tape regenerated in CI.

**Phase 5 — cut over.** New repo, rename, claim `doctrineos` on PyPI and npm, repoint. Only when Phases 1–4 are green.

---

## Part 6 — What could make this wrong

Stated up front because the plan is worth less without it.

- **The corpus edit is irreversible in practice.** Deleting 21 roles and 49 skills is easy; discovering in three months that the domain packs were the differentiator is expensive. **Mitigation:** v1 stays intact and tagged. Nothing is deleted — it is *moved out of the default*.
- **Go's auditability cost is real.** A compiled governance tool is less inspectable than a Python script by the agent it governs. **Mitigation:** reproducible builds, source-first, `go install` supported. If this is judged unacceptable, the fallback is Python with a Defender exclusion, and the honest test for that is one exclusion on `C:\Program Files\Python312` before any rewrite starts.
- **A vendor may ship layers 3–4 natively.** Qodo's *Skill Review Standards* — governance of the agent's own config files — is the leading indicator. If that lands, differentiation collapses to portability alone.
- **The "agent-native" thesis is a bet, not a finding.** BMAD's persona deletion is evidence *against the org-chart metaphor*; it is not proof that lenses work better. The spike should test the claim, not assume it.

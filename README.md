<h1 align="center">
  <img src="images/doctrine_logo.png" alt="Doctrine">
</h1>

<h1 align="center">A gated engineering operating layer for AI coding agents for Enterprise/Startups/SoloBuilder Profiles. (Beta)</h1>

<p align="center">
  <a href="https://github.com/aroora-ai-labs/doctrine/actions/workflows/doctrine.yml"><img src="https://github.com/aroora-ai-labs/doctrine/actions/workflows/doctrine.yml/badge.svg" alt="doctrine CI"></a>
  <a href="https://github.com/aroora-ai-labs/doctrine/tags"><img src="https://img.shields.io/badge/version-v0.7.0-1a2b5e" alt="version v0.7.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-1a2b5e" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-1a2b5e" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/dependencies-zero-1a2b5e" alt="zero dependencies">
  <a href="#quick-start"><img src="https://img.shields.io/badge/Claude_Code-plugin-e8642c" alt="Claude Code plugin"></a>
  <a href="#any-mcp-capable-agent"><img src="https://img.shields.io/badge/MCP-doctrineos-00a3c4" alt="MCP server: doctrineos"></a>
</p>

<p align="center">
  <a href="#the-problem">The problem</a> ·
  <a href="#what-doctrine-does">What it does</a> ·
  <a href="#what-it-looks-like">What it looks like</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#whats-inside">What's inside</a> ·
  <a href="#an-os-for-agents">The OS model</a> ·
  <a href="#how-its-built-and-proven">Proof</a> ·
  <a href="#honest-limits">Limits</a>
</p>

---

## The problem

A capable coding agent doesn't fail by writing bad code. It fails in ways that
are reproducible, specific, and expensive:

| Failure | What it looks like |
|---|---|
| **Fabricated success** | "All tests pass" — with no test run. Invented APIs that look plausible. |
| **Placeholder as done** | A `TODO` reported as shipped. |
| **Self-approval** | The agent that wrote it reviews it and approves it. Changing hats changes the narration, not the knowledge. |
| **Amnesia** | Every session starts from zero. The same dead end gets re-explored monthly. |
| **Unbounded loops** | Three rounds of the same error class, each narrated as progress. |
| **Helpful catastrophe** | Force-push, `rm -rf`, publish, spend — done fast, done well, done wrong. |

Every one is a **process** failure, not a capability failure. Doctrine's bet is
that process failures need process infrastructure — not a better model.

## What Doctrine does

It turns a repository into a disciplined software company: explicit
requirements, adversarial review gates, tested code, honest reports — **enforced
by tooling, not vibes.**

- 🚦 **Gates G0→G7** with right-sized ceremony — a typo fix never convenes a
  council; a release always does
- 👥 **42 roles**, and verifiers are *dispatched, not worn* — a fresh-context
  subagent reviews the work, because a builder reviewing its own build is a
  changed narration, not a changed mind
- 📚 **64 skill playbooks** — backend to mobile, ML, data, privacy, incident
  response, security operations, and sandboxing
- 🧠 **Hash-chained session state** — the repo remembers so the model doesn't
  have to (`checkpoint` → `hydrate`)
- 🛡️ **A `PreToolUse` guard that says no** — secrets and immutable evidence are
  denied *before* the tool runs; §5 actions and test-weakening escalate to you
- ⚖️ **Anti-fabrication law** — real output pasted, "fixed" requires re-running
  the original probe, and *"blocked"* is a respectable status
- 🔗 **Gold Build deployment** (enterprise profile) — deploy only from
  content-pinned, hash-chained provenance
- 🪶 **Zero dependencies, no runtime required** — stdlib-only Python; the gates
  run on serial role-switching or your agent's native subagents

Works with **Claude Code, Codex, Cursor, Windsurf, Copilot, Gemini CLI, Cline,
Roo, Amazon Q, Continue, JetBrains Junie** — and anything that reads
[AGENTS.md](.Doctrine/adapters/AGENTS.md) or speaks MCP.

## What it looks like

You don't invoke Doctrine. **The repo is the cue** — every task engages it, and
the agent opens by declaring how it intends to work, before doing any of it:

```text
[DOCTRINE ENGAGED]
Class: M — feature touching logic; single module
Role:  [ROLE: Chief Architect] (hats change per gate)
Loads: skills/architecture.md, standards/coding-standards.md
Gates: G2 → G3 → G4 → G5
Governance: none
Profiles: enterprise=off startup=off personal=on
```

Then it executes the gates **autonomously** — stopping only at a failed gate or
a §5 escalation, where a human decides. At G4/G5 the work goes to a fresh
verifier that cannot see the builder's reasoning, only the artifact on disk.

And when it tries something it shouldn't, the guard answers first:

```text
Doctrine: this command would modify '.doctrine-state/checkpoint.json' - the
hash-chained state checkpoint (use doctrine_state.py). A shell redirect is
still a write. Use the owning tool, or record the exception in
.doctrine-state/guard.json under 'allow'.
```

## Quick start

**Any repo (installer)** — works today, no marketplace, no publish:

```bash
git clone https://github.com/aroora-ai-labs/doctrine
python doctrine/tools/doctrine_install.py --target <your-repo> \
    --tool claude,cursor,codex   # add --solo, --startup, or --enterprise
cd <your-repo> && python tools/doctrine_state.py init && make verify
```

Pick the profile that matches how you actually work:

| Flag | Profile | Ceremony |
|---|---|---|
| `--solo` / `--personal` | Solo Builder | Creative build → deterministic DevOps verification. Governance fences real risk, not ordinary ideation. |
| `--startup` | Founder-ops | Adds growth, sales, support, finance, legal roles — all **draft-only**; you send. |
| `--enterprise` | Merge council | Adds the Gold Build ladder, permission matrix, and governance co-signs. |

**Claude Code (plugin)** — needs a public marketplace, so use the installer for
private repos:

```text
/plugin marketplace add aroora-ai-labs/doctrine
/plugin install doctrine@doctrine-marketplace
/doctrine-init
```

<a id="any-mcp-capable-agent"></a>

**Any MCP-capable agent.** The installer drops a `.mcp.json` registering the
`doctrineos` server — corpus lint, state plane, and gold-build gates as native
tools. **Nothing is published to a registry, and nothing needs to be:** the
server is a local script, registered by path, so it works in private repos and
air-gapped environments the same as anywhere else.

```bash
claude mcp add doctrineos -- python tools/doctrine_mcp.py   # Claude Code (local)
```

```toml
# Codex config.toml
[mcp_servers.doctrineos]
command = "python"
args = ["tools/doctrine_mcp.py"]
```

Full install matrix: [.Doctrine/05-packaging.md](.Doctrine/05-packaging.md).

**Drive it.** Every task engages automatically — or be explicit:

| Command | Does |
|---|---|
| `doctrine: <task>` or `/doctrine <task>` | classify, staff, gate, execute |
| `/role <name> [task]` | act as one hat (`/role security-reviewer`) |
| `/checkpoint` | save session state so the repo remembers, not you |
| `/soc-triage`, `/soc-hunt`, `/sandbox` | security operations and isolation |

## What's inside

| | Count | |
|---|---:|---|
| **Roles** | 42 | engineering · governance heads · founder-ops · domain specialists |
| **Skill playbooks** | 64 | full SDLC + security operations + sandboxing |
| **Hard standards** | 8 | coding, API design, errors, deps, git, governance, merge |
| **Language profiles** | 10 | per-language conventions |
| **Domain overlays** | 15 | healthcare, finance, quant, aerospace, agentic-AI… |
| **Artifact templates** | 15 | brief, ADR, plan, review, QA, release, retro, risk |
| **Ready subagents** | 14 | 8 parallel workers + 6 fresh-context verifiers |
| **Tests** | 324 | `make verify` = lint + ruff + tests |

Every one of those numbers is **lint-enforced** against the filesystem — a
stale count fails CI rather than quietly misleading you.

## An OS for agents

**An operating system for coding agents — not the machine that runs them.**
Doctrine owns the *policy* (how work is scheduled, isolated, remembered, and
privileged); the harness — Claude Code, Codex, Cursor — owns the *CPU*.

| OS primitive | In Doctrine |
|---|---|
| **Kernel** | `.Doctrine.md` (always loaded) + the fail-closed gates |
| **Processes** | tasks through **G0→G7**, classified S/M/L/HOTFIX, run *as* roles |
| **Memory** | the hash-chained state plane (`.doctrine-state/`) |
| **Syscalls** | **§5** gates every irreversible or external action — the human is root |
| **Protection ring** | the `PreToolUse` guard decides *before* the tool runs |
| **Address-space isolation** | `skills/sandboxing.md` — size the tier, then **prove** the boundary |
| **Provenance** | gold records, tag-attested, re-checked against git |
| **`ps` for a fleet** | `doctrine_fleet status` — version, drift, state, release distance |

Agent-count-agnostic: one agent wearing role hats, or a fleet of workers plus
fresh-context verifiers. Full mapping — including where the metaphor holds and
where it's only illustrative — in
[docs/doctrine-as-an-os.md](docs/doctrine-as-an-os.md).

## How it's built (and proven)

**Doctrine is built with Doctrine — halfway.** The corpus was authored before
the tooling existed to gate it. But everything since, including the enforcement
tooling itself, shipped through Doctrine's own pipeline: brief → plan → build →
**adversarial verifier fan-out**. The honest claim is *self-hosting in
progress*, not a closed loop.

Four review rounds ran. Every round produced real findings — a reproduced path
traversal, a state-corrupting write-order bug, a rollback chain forkable by
`git clone`, zero-byte sign-offs satisfying "no verdict, no gold". Each was
vetoed, remediated with a named regression test, and re-verified by re-running
the original exploit.

The strongest evidence is a finding against *itself*: an independent round
overturned a sign-off the system had already given, proving the gates catch the
author — including when the author is Doctrine. The full audit trail is
committed under [docs/reviews/](docs/reviews/) and [docs/qa/](docs/qa/), and
every lesson became permanent law via G7 retrospectives.

Start reading at [.Doctrine.md](.Doctrine.md) — the root operating system
(everything else loads on demand via its routing table).

```text
.Doctrine.md          the law (always loaded)
.Doctrine/            roles, skills, standards, templates, adapters,
                      state-plane spec, packaging
tools/                stdlib-only enforcement: state plane, corpus lint,
                      gold builds, MCP server, installer, operations bridge
plugin/               Claude Code plugin (byte-parity lint-enforced)
tests/               324 tests; `make verify` = lint + ruff + tests
.doctrine-state/      this repo's own hash-chained session memory
```

## Honest limits

Doctrine's first law is *never fabricate* — which binds its own README. What it
does **not** do:

- **The Bash guard is a tripwire, not a boundary.** Shell is Turing-complete, so
  no static analysis of it is complete. The real boundary is one layer down —
  a read-only mount — which [`skills/sandboxing.md`](.Doctrine/skills/sandboxing.md)
  tells you how to pick and how to *prove*.
- **Gold records are tamper-evident, not tamper-proof.** A record forged and
  committed in one step has no prior state to diff against; that class needs a
  human reading the diff.
- **Verifier isolation is a strong default, not a sandbox.** Verifier subagents
  lack Edit/Write but retain Bash.
- **Without the `PreToolUse` hook wired, Doctrine is advice.** That hook is what
  turns four of the ten non-negotiables into decisions rather than intentions.
- **The corpus is prose whose effect is not yet measured.** Lint proves it is
  internally consistent, not that it makes output better.

Claiming more strength than a mechanism has is the same fabrication the first
law forbids. Details: [.Doctrine/05-packaging.md](.Doctrine/05-packaging.md).

## License

[MIT](LICENSE) — © 2026 Aroora AI Labs (Mahesh Vaikri).

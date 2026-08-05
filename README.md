<h1 align="center">
  <img src="images/doctrine_logo.png" alt="Doctrine">
</h1>

<p align="center">
  <a href="https://github.com/aroora-ai-labs/doctrine/actions/workflows/doctrine.yml"><img src="https://github.com/aroora-ai-labs/doctrine/actions/workflows/doctrine.yml/badge.svg" alt="doctrine CI"></a>
  <a href="https://github.com/aroora-ai-labs/doctrine/tags"><img src="https://img.shields.io/badge/version-v0.7.0-1a2b5e" alt="version v0.7.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-1a2b5e" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-1a2b5e" alt="Python 3.11+">
  <a href="#quick-start"><img src="https://img.shields.io/badge/Claude_Code-plugin-e8642c" alt="Claude Code plugin"></a>
  <a href=".Doctrine/05-packaging.md"><img src="https://img.shields.io/badge/MCP-doctrineos-00a3c4" alt="MCP server: doctrineos"></a>
</p>

**A gated engineering operating system for AI coding agents.** Doctrine
turns a repository into a disciplined software company: explicit
requirements, adversarial review gates, tested code, honest reports —
enforced by tooling, not vibes.

- **42 roles**, verifiers dispatched as fresh-context subagents whose tool
  grants exclude Edit/Write (they still hold Bash, so the isolation is a
  strong default, not a sandbox)
- **63 skill playbooks + 8 standards + 10 language profiles** — full-SDLC
  coverage from backend to mobile, ML, data, privacy, incident response,
  and security operations (triage, detection engineering, hunting, forensics)
- **Gates G0→G7** with right-sized ceremony (a typo fix never convenes
  a council; a release always does)
- **Personal/solo builder profile** — `--personal` / `--solo` routes routine
  work through a creatively free Solo Builder phase, then deterministic DevOps
  verification; governance fences real risks rather than ordinary ideation
- **MAPLE by default** — selected for every install, with native/serial fallback
  and explicit installation of the free/open-source AGPL runtime
- **Hash-chained session state** — the repo remembers, the model doesn't
  have to (`.doctrine-state/`, checkpoint → hydrate)
- **Gold Build deployment** (opt-in enterprise profile) — deploy only
  from content-pinned, hash-chained provenance records
- **Anti-fabrication law** — real output pasted, "fixed" requires the
  re-executed original probe, negative findings are wins

Works with **Claude Code, Codex, Cursor, Windsurf, Copilot, Gemini CLI,
Cline, Roo, Amazon Q, Continue, JetBrains Junie**, and anything that
reads [AGENTS.md](.Doctrine/adapters/AGENTS.md) or speaks MCP.

## An OS for agents

**An operating system for coding agents — not the machine that runs them.**
Doctrine owns the *policy* (how work is scheduled, isolated, remembered, and
privileged); the harness — Claude Code, Codex, Cursor, MAPLE — owns the *CPU*.
The classic OS primitives map onto real components:

- **Kernel** — `.Doctrine.md` (always loaded) fused with the fail-closed gates
  (`doctrine_lint` / `doctrine_verify` / gold-build)
- **Processes** — tasks through gates **G0→G7**, classified S/M/L/HOTFIX, run
  *as* roles; verifier grants exclude Edit/Write, though they retain Bash, so
  the isolation is a strong default rather than a sandbox (ADR-012)
- **Memory** — the hash-chained **state plane** (`.doctrine-state/`): checkpoint →
  hydrate; the repo remembers so the model doesn't have to
- **Syscalls** — **§5** gates every irreversible or external action; the human is root
- **Protection ring** — the `PreToolUse` guard (`doctrine_guard`) decides before
  the tool runs: secrets and immutable evidence deny, §5 and test-weakening ask.
  Sound on Write/Edit; a *tripwire* on shell commands (ADR-012)
- **Provenance** — gold records carry the tag's **attestation**
  (`--require-signature`), and `doctrine_gold gate` re-checks them against git:
  tamper-evident in CI, never tamper-proof inside a repo you can write
- **`ps` for a fleet** — `doctrine_fleet status` shows every governed repo's
  version, drift, state and release distance in one read-only table

It's agent-count-agnostic: one agent wearing role hats, or a fleet of workers +
fresh-context verifiers. Full mapping — including where the metaphor holds and
where it's only illustrative — in
[docs/doctrine-as-an-os.md](docs/doctrine-as-an-os.md).

## Quick start

**Claude Code (plugin):**

```text
/plugin marketplace add aroora-ai-labs/doctrine
/plugin install doctrine@doctrine-marketplace
/doctrine-init
```

The plugin path needs the marketplace (public/shared). **Local or private repo?**
Use the installer below — no marketplace, no publish; it now also auto-registers the
MCP server.

**Any repo (installer):**

```bash
git clone https://github.com/aroora-ai-labs/doctrine
python doctrine/tools/doctrine_install.py --target <your-repo> \
    --tool claude,cursor,codex   # add --solo, --startup, or --enterprise
cd <your-repo> && python tools/doctrine_state.py init && make verify
```

**Any MCP-capable agent** — the installer drops a **`.mcp.json`** registering the
`doctrineos` server (corpus lint, state plane, gold-build gates as native tools), so
Claude Code / Cursor / any `.mcp.json`-aware client offers it on approval — no
marketplace, no publish. Register by hand where a client needs it:

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

**Drive it (once installed).** Every task engages the doctrine automatically (the
repo is the cue) — or be explicit:

- `doctrine: <task>` (any agent) or **`/doctrine <task>`** — classify, staff, gate, execute
- **`/role <name> [task]`** — act as one hat: `/role security-reviewer`, `/role chief-architect` (reviewer roles run fresh-context)
- **`/checkpoint`** — save session state so the repo remembers, not you

### WorkHawk

The bundled WorkHawk agentic engineering workbench consumes Doctrine as its
currently connected governance module. It renders the current repository's
real activation, state-chain, Git, release, and verification evidence without
making the frontend part of Doctrine's installable core. Start the loopback
bridge from the repository root, then WorkHawk:

```bash
python tools/doctrine_dashboard.py
cd workhawk && npm ci && npm run dev
```

Open `http://localhost:3003/`. The bridge exposes no arbitrary command surface;
its only mutation is the fixed Doctrine verifier. MAPLE, STIX, and Trust are
shown as unavailable until real connectors exist. Remote hosting,
multi-repository aggregation, editor/terminal execution, and public deployment
are intentionally not claimed by this bundle. Full operating and security
notes: [workhawk/README.md](workhawk/README.md). Source CI checks the WorkHawk
lockfile, lint, types, production build/tests, dependency audit, and hosted
Chromium behavior.

## How it's built (and proven)

This repo governs itself. The enforcement tooling was shipped through
Doctrine's own pipeline: brief → plan → build → **adversarial verifier
fan-out**. Four review rounds ran; every round produced real findings —
a reproduced path traversal, a state-corrupting write-order bug, a
rollback chain forkable by `git clone`, zero-byte sign-offs satisfying
"no verdict, no gold" — each vetoed, remediated with a named regression
test, and re-verified by re-running the original exploit. The full
audit trail is committed under [docs/reviews/](docs/reviews/) and
[docs/qa/](docs/qa/), and every lesson became permanent law via G7
retrospectives.

Start reading at [.Doctrine.md](.Doctrine.md) — the root operating
system (everything else loads on demand via its routing table).

```text
.Doctrine.md          the law (always loaded)
.Doctrine/            roles, skills, standards, templates, adapters,
                      state-plane spec, packaging
tools/                stdlib-only enforcement: state plane, corpus lint,
                      gold builds, MCP server, installer, WorkHawk bridge
workhawk/             source-only agentic engineering workbench
plugin/               Claude Code plugin (byte-parity lint-enforced)
tests/               195 tests; `make verify` = lint + ruff + tests
.doctrine-state/      this repo's own hash-chained session memory
```

## License

[MIT](LICENSE) — © 2026 Aroora AI Labs (Mahesh Vaikri).

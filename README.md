# Doctrine

[![doctrine](https://github.com/aroora-ai-labs/doctrine/actions/workflows/doctrine.yml/badge.svg)](https://github.com/aroora-ai-labs/doctrine/actions/workflows/doctrine.yml)

**A gated engineering operating system for AI coding agents.** Doctrine
turns a repository into a disciplined software company: explicit
requirements, adversarial review gates, tested code, honest reports —
enforced by tooling, not vibes.

- **19 roles** with tool-enforced separation of duties (reviewers
  physically cannot edit code)
- **30 skill playbooks + 7 standards + 6 language profiles** — full-SDLC
  coverage from backend to mobile, ML, data, privacy, incident response
- **Gates G0→G7** with right-sized ceremony (a typo fix never convenes
  a council; a release always does)
- **Hash-chained session state** — the repo remembers, the model doesn't
  have to (`.doctrine-state/`, checkpoint → hydrate)
- **Gold Build deployment** (opt-in enterprise profile) — deploy only
  from content-pinned, hash-chained provenance records
- **Anti-fabrication law** — real output pasted, "fixed" requires the
  re-executed original probe, negative findings are wins

Works with **Claude Code, Codex, Cursor, Windsurf, Copilot, Gemini CLI,
Cline, Roo, Amazon Q, Continue, JetBrains Junie**, and anything that
reads [AGENTS.md](.Doctrine/adapters/AGENTS.md) or speaks MCP.

## Quick start

**Claude Code (plugin):**

```text
/plugin marketplace add aroora-ai-labs/doctrine
/plugin install doctrine@doctrine-marketplace
/doctrine-init
```

**Any repo (installer):**

```bash
git clone https://github.com/aroora-ai-labs/doctrine
python doctrine/tools/doctrine_install.py --target <your-repo> \
    --tool claude,cursor,codex   # add --enterprise --ci as needed
cd <your-repo> && python tools/doctrine_state.py init && make verify
```

**Any MCP-capable agent** — register the `doctrineos` server (lint,
state plane, gold-build gates as native tools):

```toml
# Codex config.toml
[mcp_servers.doctrineos]
command = "python"
args = ["tools/doctrine_mcp.py"]
```

Full install matrix: [.Doctrine/05-packaging.md](.Doctrine/05-packaging.md).

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
                      gold builds, MCP server, installer
plugin/               Claude Code plugin (byte-parity lint-enforced)
tests/                82 tests; `make verify` = lint + ruff + tests
.doctrine-state/      this repo's own hash-chained session memory
```

## License

[MIT](LICENSE) — © 2026 Aroora AI Labs (Mahesh Vaikri).

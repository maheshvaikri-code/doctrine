# 05 — Packaging & Distribution

Two things ship, on two different vehicles:

1. **The law** (`.Doctrine.md`, `.Doctrine/`, tools, wiring) lives IN each
   governed repo, committed — installed once by `tools/doctrine_install.py`.
   Doctrine is per-repo law; it cannot live in a plugin cache.
2. **The tooling surface** reaches every agent two ways: native wiring
   (hooks/commands/agents) and the **doctrineos MCP server**
   (`tools/doctrine_mcp.py`) — stdlib stdio JSON-RPC exposing
   `doctrine_lint`, `state_{status,verify,hydrate,checkpoint}`,
   `gold_{check,record}` to any MCP-capable agent.

## The installer (any repo, any tool)

```
python tools/doctrine_install.py --target <repo> --tool claude,cursor,codex
                                 [--enterprise] [--ci] [--force] [--local]
```

Copies the law + enforcement suite + tests + Makefile, the AGENTS.md boot
(only if absent), per-tool adapter overlays, and the Claude wiring;
appends (never replaces) CLAUDE.md imports, and writes a single
marker-delimited managed block to `.gitignore`. Files that exist with
different content are skipped with a warning — `--force` is a deliberate
act. `--enterprise` seeds the merge/promotion profile. `--local` makes the
managed block cover the WHOLE installed framework (corpus, tools, tests,
adapters at their variable paths, MCP registration) instead of just
machine-local state, so Doctrine stays out of the repo's history — one
block to add or delete; `docs/` gate artifacts are never ignored.

## Install matrix

| Agent | Doctrine law | Commands/agents | Tooling access |
|---|---|---|---|
| **Claude Code** | `/doctrine-init` (plugin) or installer `--tool claude` | Plugin: `/plugin marketplace add <this repo>` → `/plugin install doctrine@doctrine-marketplace` — ships /checkpoint, /doctrine-init, /doctrine-verify, /gold-check, 14 subagents, SessionStart hydrate hook | plugin `.mcp.json`, or `claude mcp add doctrineos -- python tools/doctrine_mcp.py` |
| **Codex CLI/IDE** | installer `--tool codex` (AGENTS.md native) | custom prompts: copy `plugin/commands/*.md` into `~/.codex/prompts/` | `config.toml`: `[mcp_servers.doctrineos] command="python" args=["tools/doctrine_mcp.py"]` |
| **Cursor** | installer `--tool cursor` (rules overlay) | — (AGENTS.md + rules drive behavior) | `.cursor/mcp.json` with the same server entry |
| **Windsurf** | installer `--tool windsurf` | — | MCP plugin config with the same entry |
| **GitHub Copilot** | installer `--tool copilot` | — | repo `.vscode/mcp.json` / org MCP registry |
| **Gemini CLI** | installer `--tool gemini` | `gemini-extension.json` may wrap the commands | `settings.json` `mcpServers` entry |
| **Cline / Roo / Amazon Q / Continue / Junie** | installer `--tool <name>` | — | each tool's MCP config, same server entry |
| **Anything else** | installer (AGENTS.md boot) | — | MCP if available; else the CLIs directly |

## Python packaging

`pyproject.toml` builds a `doctrineos` wheel with console scripts
(`doctrine-state`, `doctrine-lint`, `doctrine-gold`, `doctrine-mcp`,
`doctrine-install`, `doctrine-metrics`, `doctrine-signature`,
`doctrine-awaken`, and the loopback-only `doctrine-dashboard`) for `pipx
install` distribution. The wheel carries the TOOLS only — the law travels by
repo: `doctrine-install` needs a doctrine source tree (`--source <clone of this
repo>`). **Publishing to PyPI or any registry is an external action: explicit
human go required**
(`.Doctrine.md` section 5), through the G6 release checklist — and on an
enterprise repo, from a gold record.

## Versioning rule

The plugin manifest, marketplace entry, pyproject, and MCP serverInfo
carry the doctrine version; bump them with the `.Doctrine.md` header in
the same commit (the corpus lint checks version sync with the CHANGELOG).

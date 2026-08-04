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
                                 [--personal|--solo] [--enterprise]
                                 [--startup] [--force] [--local]
                                 [--ci [--ci-provider github|gitlab|azure]]
```

Copies the law + enforcement suite + tests + required companion artifacts
(including the dashboard OpenAPI contract) + Makefile, the AGENTS.md boot
(only if absent), per-tool adapter overlays, and the Claude wiring; appends
(never replaces) CLAUDE.md imports, and writes a single marker-delimited
managed block to `.gitignore`. Files that exist with different content are
skipped with a warning — `--force` is a deliberate act. `--enterprise`
seeds the merge/promotion profile. `--local` makes the managed block cover
the installed framework (corpus, tools, tests, adapters at their variable
paths, MCP registration) instead of just machine-local state, so Doctrine
stays out of the repo's history — one block to add or delete; `docs/`
artifacts remain committable.

Every install seeds `Workforce runtime: maple`; the installer selects the
runtime but does not install or import the external AGPL package. `--maple`
remains accepted as a backward-compatible no-op. `--personal` and `--solo` are
aliases that seed `Delivery profile: personal` and, unless already selected,
`Agent latitude: creative`. The profile selects creative Solo Builder work →
deterministic DevOps verification. The latitude field is a portable behavior
policy, not a provider temperature setting; a pre-existing explicit latitude
is preserved. Personal and enterprise profiles are mutually exclusive; startup
is compatible with either.

## Reinstall preservation contract

A reinstall, including `--force`, overwrites only Doctrine-managed corpus,
tools, companion tests/contracts, and selected adapter files. It never removes
target-only files and never writes repository-owned runtime or planning data
under `.doctrine-state/`, `memory/`, `sessions/`, `docs/plans/`,
`docs/briefs/`, `docs/adr/`, `docs/reviews/`, `docs/qa/`, `docs/releases/`, or
`docs/retro/`. The sole project-brief mutation is append-only: missing profile
markers may be added to `docs/brief.md`; its existing bytes are otherwise
preserved. The fixed dashboard OpenAPI file under `docs/contracts/` is an
explicit Doctrine-managed companion artifact.

`--verify` may initialize missing state-plane structure after copying, but it
must not replace existing checkpoints, decisions, effects, distillates, or
repo-local application state. Regression coverage seeds state, memory,
sessions, and plan artifacts, force-reinstalls Doctrine, and requires every
seeded byte to remain identical.

## The enforcement gate (`PreToolUse`)

`tools/doctrine_guard.py` is what turns the law from advice into a decision.
It reads the runtime's pre-execution payload on stdin and answers on stdout;
the shipped `.claude/settings.json` and `plugin/hooks/hooks.json` wire it for
`Write|Edit|MultiEdit|NotebookEdit|Bash`. Any runtime with an equivalent
pre-execution contract can call it the same way — JSON in, JSON out.

| Class | Verdict | Why |
|---|---|---|
| Secret-shaped content in a write or command | **deny** | §7 #2 — never commit secrets |
| Write to a gold record, the state checkpoint, `.env`, or (in a consumer repo) the installed corpus | **deny** | immutable evidence; §12 forbids editing an installed corpus |
| Force-push, history rewrite, `--no-verify`, publish, `terraform destroy`, `curl \| sh` | **ask** | §5 — the human decides irreversible and external actions |
| An edit adding a skip/xfail marker to a test file | **ask** | §7 #4 — never silence a failing test to go green |

Posture: **silent** outside a doctrine repo (the law is not in play);
**fail-closed** inside one — an unparseable request is denied, because a
governed repo must not gain a bypass by malforming a request. Local policy
lives at `.doctrine-state/guard.json`:

```json
{"protected_paths": ["infra/*"], "allow": ["tests/fixtures/*"]}
```

`allow` exempts a path from the path and secret rules — the escape hatch for
legitimate secret-shaped fixtures. A malformed policy file is ignored, never
obeyed, and **blanket patterns (`*`, `**`, `.`, `/`) are dropped even from a
well-formed file**: "allow everything" is not a policy, it is the off switch.

**The enforcement surface is itself guarded.** This policy file, the hook
wiring (`.claude/settings.json`, `CLAUDE.md`, `AGENTS.md`), `pyproject.toml`
(its package name decides whether the installed corpus is protected here),
`.doctrine-state/fleet.json` and `.github/workflows/` all require an explicit
human **ask** before an agent may change them. An earlier version protected
none of these, and three independent verifiers each disabled the entire guard
from inside the repo it governs with a single write. They **ask** rather than
deny because widening policy is a legitimate human act; what must never happen
is the governed party doing it silently.

Honest limits, measured rather than assumed:

- Pattern matching finds known credential formats, not every secret. A value
  with no credential-shaped name, or one containing spaces, is not caught, and
  a secret **assembled across two separate tool calls** is never seen whole.
  Pair it with a real scanner at G5 (`skills/security.md`).
- Command enforcement resolves the paths a command *names*. A path built at
  runtime — `cd docs/releases && echo x > gold/f.json`, or one assembled from
  a shell variable — is beyond a pre-execution text check.
- It binds only runtimes that honour a pre-execution hook, and only the tools
  its matcher lists. MCP filesystem/exec servers are ungoverned.
- It gates four checkable non-negotiables, not all ten.

## Fleet view (many repos, one posture)

```
python tools/doctrine_fleet.py status ../repo-a ../repo-b
python tools/doctrine_fleet.py status --root .. --json
```

Reports each repo's doctrine version, drift from this source tree (`current` /
`behind vX` / `ahead` / `modified` / `incomplete`), state-plane posture,
worktree cleanliness, release distance, and gold-record count. Repos also come
from `.doctrine-state/fleet.json` (`{"repos": ["../a", "../b"]}`).

Strictly read-only, and exit 1 when any repo drifts — so a scheduled job can
watch a portfolio. Drift is repaired by reinstalling
(`doctrine_install.py --target <path> --force`), never by hand-editing an
installed corpus.

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
`doctrine-awaken`, `doctrine-guard`, `doctrine-fleet`, and the
loopback-only `doctrine-dashboard`) for `pipx
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

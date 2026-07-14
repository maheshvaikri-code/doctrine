# Quickstart — from zero to a verified, governed repo

The Doctrine System turns any repo into an AI-run engineering organization:
classified tasks, role-based work, adversarial review gates, hash-chained
session state. This is the shortest path from nothing to a working, verified
install.

> **Prerequisite (today):** the law travels by repo, so you need a clone of
> the Doctrine source. A public one-line bootstrap (`curl | bash` / `pipx`)
> arrives when the project goes open-source; until then, clone first.

## 1. Get the source

```bash
git clone <doctrine-repo-url> doctrine
cd doctrine
```

## 2. Install into your project — one command, verified

From the doctrine clone, point `--target` at your repo and add `--verify`:

```bash
python tools/doctrine_install.py --target ../my-project --verify
```

That single command:

1. copies the law (`.Doctrine.md` + `.Doctrine/`), the enforcement tools, the
   tests, and the Claude Code wiring into your project (existing files are
   never clobbered — different content is skipped with a warning unless
   `--force`);
2. initializes the state plane in your project;
3. runs the gate suite (`doctrine_verify`) there and reports each gate.

When it prints `turnkey: installed and verified - gates green`, the install is
proven working — not assumed. If a gate fails, it says so and changes nothing
to force a pass; you fix and rerun.

Pick your agent(s) with `--tool` (default `claude`):

```bash
python tools/doctrine_install.py --target ../my-project \
    --tool claude,cursor,codex --verify
```

`--tool all` installs every adapter. Supported: claude, codex, cursor,
windsurf, copilot, gemini, cline, roo, amazonq, continue, junie.

## 3. Opt into profiles and the runtime (optional)

Flags seed your project's `docs/brief.md`:

| Flag | Effect |
|------|--------|
| `--enterprise` | Merge Council + Gold Build promotion (`Merge profile: enterprise`) |
| `--startup` | Founder-ops roles: growth, sales, support, finance, legal (`Company profile: startup`) |
| `--maple` | Opt into the MAPLE multi-agent runtime (`Workforce runtime: maple`) — see `.Doctrine/integrations/maple.md` |

```bash
python tools/doctrine_install.py --target ../my-project --enterprise --verify
```

## 4. Engage

In your project, with your coding agent, start any task with the cue:

```
doctrine: <your task>
```

The agent opens with the Engagement Block — Class, Role, Loads, Gates,
Governance, Profiles — then executes the gates autonomously, pausing only for
escalations you must decide (anything irreversible or external). Artifacts
land under `docs/`; at session end, `/checkpoint` records verified state.

## 5. Re-verify anytime

```bash
python tools/doctrine_verify.py     # lint -> ruff (if present) -> tests -> state
```

No `make` needed; it is cross-platform (Windows, macOS, Linux).

## Where to go next

- The law and how to use it: `.Doctrine.md` (§2 the Engagement Protocol, §6 the routing table).
- Packaging, MCP server, and per-tool wiring: `.Doctrine/05-packaging.md`.
- The MAPLE runtime integration: `.Doctrine/integrations/maple.md`.
- Publishing/releasing is always a human decision (`.Doctrine.md` §5).

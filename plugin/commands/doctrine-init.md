---
description: Install the Doctrine System into this repository (law, tools, wiring)
---

Install the Doctrine System into the current repository:

1. Run: `python "${CLAUDE_PLUGIN_ROOT}/../tools/doctrine_install.py"
   --target . --tool claude $ARGUMENTS`
   (add more tools like `--tool claude,cursor,codex`, `--personal`/`--solo`
   for creative Solo Builder → deterministic DevOps verification,
   `--enterprise` for merge/promotion, or `--ci` for the GitHub Actions gate).
   MAPLE is selected by default.
   If the plugin cache lacks the sibling `tools/` directory, clone the
   doctrine repo and run the same command with `--source <clone>`.
2. Paste the installer's real output. If it skipped differing files,
   show them to the human before considering `--force` — never clobber
   silently.
3. Initialize the state plane: `python tools/doctrine_state.py init`.
4. Run `make verify` (corpus lint + ruff + tests) and paste the tail.
5. From now on, follow `.Doctrine.md` — classify the task, wear one role
   at a time, and route via its section 6 table.

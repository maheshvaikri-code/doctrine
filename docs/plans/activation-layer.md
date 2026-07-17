# Plan — Doctrine activation layer (L0 + L1)

<!-- G2 artifact. Author: Chief Architect. Implements the brief; design in ADR-004. -->

## Threat sketch
- **Assets:** the agent's context (the reminder is injected into it); the repos the
  tools run inside (incl. non-doctrine repos, since the hook fires everywhere).
- **Entry points:** the `UserPromptSubmit` hook runs `doctrine_engage.py` on every
  turn, in whatever repo is open; the installer copies both tools into consumer repos.
- **Worst plausible abuse / failure:** the hook firing (and printing) in a repo that
  is *not* a doctrine repo (noise, or worse, misleading injection); a tool crash on a
  Windows cp1252 pipe breaking every turn. → Mitigations: `doctrine_engage` no-ops
  unless `.Doctrine.md` is found; ASCII-only output; plugin hook `os.path.exists` guard.

## Steps
1. `tools/doctrine_engage.py` — `find_root` (walk to `.Doctrine.md`); print the
   compact reminder only if found; ASCII-only; tolerate any argv.
2. `tools/doctrine_awaken.py` — `audit(root)` returns `(rows, awake)`; critical vs
   recommended checks; ASCII markers `[OK]/[MISS]/[WARN]`; `--target`, `--quiet`.
3. Wire `UserPromptSubmit` into `.claude/settings.json` (plain) and
   `plugin/hooks/hooks.json` (guarded), mirroring the existing SessionStart shape.
4. Add both tools to `doctrine_install.py` `TOOL_FILES`.
5. `tests/test_doctrine_awaken.py` — awake/​not-awake/​non-doctrine cases + engage
   `find_root`.
6. Version 0.6.18 → 0.6.19 across carriers; CHANGELOG; §11 wiring note.
7. Verify: smoke both tools, JSON parse, ruff, `doctrine_lint`, full `doctrine_verify`.

## Deferred (recorded, not silent)
L2 path-rules pack and L3 `PreToolUse` gates — ADR-004 roadmap rows; not in this slice.

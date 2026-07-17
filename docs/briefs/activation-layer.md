# Brief — Doctrine activation layer

<!-- G0 artifact. Author: Product Owner. -->

**Problem.** Repos that have Doctrine installed often do not *trigger* it — the
Engagement Protocol is loaded into context but not obeyed (skipped block, routing
table never consulted, wrong/no role loaded for the task), or the load was never
fully wired. Doctrine is advisory; obedience is probabilistic and degrades in long
sessions and on tasks that don't feel doctrine-y.

**Goal.** Make Doctrine *reliably wake up* in any repo where it is installed,
without hard-blocking every action — and make "installed but not triggering"
diagnosable in one command.

**Scope (this slice — L0 + L1).**
- `doctrine_awaken.py` — activation doctor: audit a repo's wake-up wiring, report
  each gap with a remediation, exit non-zero on a critical gap.
- `doctrine_engage.py` + a `UserPromptSubmit` hook — re-arm the Engagement Protocol
  every turn (injected compact reminder).
- Wire the hook into `.claude/settings.json` and `plugin/hooks/hooks.json`
  (consumer-safe guard); ship both tools via the installer.

**Out of scope (roadmap, ADR-004):** L2 `.claude/rules/` path-routing pack; L3
`PreToolUse` hard gates for the non-negotiables.

**Acceptance criteria (each a runnable check).**
- [ ] `python tools/doctrine_engage.py` prints the reminder inside a doctrine repo, prints nothing outside one.
- [ ] `python tools/doctrine_awaken.py` reports **AWAKE** for a fully-wired repo (exit 0) and **NOT FULLY AWAKE** with the missing `UserPromptSubmit` row for a repo lacking the hook (exit 1).
- [ ] `.claude/settings.json` and `plugin/hooks/hooks.json` remain valid JSON and carry the new hook.
- [ ] `ruff`, `doctrine_lint`, and the full `doctrine_verify` suite pass.
- [ ] Consumer-safe: `doctrine_engage` is silent outside a doctrine repo; the plugin hook guards on `os.path.exists`.

**Non-negotiable applied up front:** consumer-safety (the v0.6.10→v0.6.18 retro's
dominant bug class) is designed in, not patched after a field escape.

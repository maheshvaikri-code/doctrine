---
on: ["class:M|L", "intent:review|slop|verify the code"]
cost: read
provides: skill
---

# Skill: AI-Slop Detection

> The reviewer discipline of catching the failure modes **specific to
> AI-generated code and content** — the smells that survive a naive read but rot
> the codebase. It composes with the anti-fabrication law (Non-Negotiable #1),
> "no placeholder reported as done" (#9): those
> forbid the acts; this skill is the fresh-context *detector* at G4/G5.

## Scope

G4 code review (`roles/code-reviewer.md`) and G5 verification; the UI variant at
`roles/web-designer.md` / `roles/ux-designer.md` (design slop). Judge what is on
disk, not the author's fluency — confident, well-formatted output is exactly where
slop hides.

## The slop taxonomy — what to look for

1. **Invented surface.** APIs, imports, config keys, CLI flags, or env vars that do
   not exist. Grep the real definition; a plausible name is not proof (#1).
2. **Plausible-but-wrong.** Code that *reads* correct and cites real-looking
   functions but does not do what it claims — verify behavior against the actual
   API/spec, not the vibe.
3. **Over-engineering.** Abstraction, config surface, or layers for a one-off
   (YAGNI) — an interface with one implementation, a strategy pattern for
   two cases.
4. **Boilerplate bloat.** Verbose scaffolding, defensive noise on impossible paths,
   and comments that restate the code line-for-line.
5. **Placeholder-as-done.** `TODO`, "implement later", stubbed returns, or mock/
   sample data presented as a finished feature (#9). `TODO` = not done.
6. **Comment slop.** Comments that narrate the obvious, or that *lie* — aspirational
   or stale docstrings describing behavior the code no longer has.
7. **Test theater.** `assert True`, tests that exercise the mock instead of the
   code, happy-path-only coverage, or snapshots regenerated to whatever the code
   emits. A test that cannot fail proves nothing.
8. **Fabricated evidence.** "Tests pass" with no pasted output; invented benchmark
   or coverage numbers; a summary of output presented as the output (#1).
9. **Ignores the codebase.** Re-implements an existing util, breaks the local
   pattern/style, or adds a dep for what's already present. Search the repo
   before concluding nothing reusable exists.
10. **Security theater.** A check that looks like validation but isn't — a no-op
    auth middleware, a regex that matches everything, permissive defaults dressed as
    safe. (Route real findings to `roles/security-reviewer.md`.)
11. **Confident-wrong prose.** A PR body or doc asserting things not true of the
    actual diff. Read the diff, not the description.

## Do

- Verify every non-trivial claim against the real artifact (grep the symbol, run
  the test, read the diff) — fluency is not correctness.
- File slop as ranked findings like any G4 review; a pattern of slop is a signal to
  tighten the loop, not just fix the instance.

## Don't

- Don't approve because it "looks professional" — polish is slop's camouflage.
- Don't let a plausible identifier stand unverified, or a test you didn't watch fail.

## Review checklist (G4/G5 slop pass)

- [ ] Every referenced API/import/flag confirmed to exist
- [ ] No placeholder / stub / mock presented as complete
- [ ] Tests can actually fail and exercise the code, not the mock
- [ ] "Passing" claims backed by pasted, re-runnable output
- [ ] No re-implementation of existing utils; local patterns honored
- [ ] Validation/auth/security checks actually check something

## Common failure modes

Rubber-stamping fluent output; a plausible-but-nonexistent function surviving to
merge; green from a test that asserts nothing; a stubbed path shipped as done; a PR
description believed over its diff.

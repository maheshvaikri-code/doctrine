# What and why

<!-- What changes, and the problem it solves. The "why" matters more than the
     "what" — the diff already shows the what. -->

**Class:** S / M / L — <!-- S: typo/doc/config, no behavior change.
M: feature/bugfix/refactor, one module. L: new module, schema, public API,
anything cross-cutting. Default to M if unsure. -->

## Verification — paste real output

<!-- Not "gates pass". The actual output. A claim without output is the one
     thing this project cannot accept (Non-Negotiable #1). -->

```text
$ make verify

```

## Checklist

- [ ] `make verify` green — **output pasted above**, not summarised
- [ ] Ruff run at the pinned **0.15.15** (a newer ruff reports unrelated files)
- [ ] Behaviour change ships with a test, named after the bug it prevents
- [ ] No check deleted, skipped, or weakened to go green
- [ ] No secrets, keys, tokens, or `.env` content
- [ ] One logical change — no unrelated drive-by edits
- [ ] Docs/changelog updated if public surface changed
- [ ] No new runtime dependency (or: discussed in an issue first)

### If this touches the corpus (`.Doctrine/`)

- [ ] Matches the shape of neighbouring roles/skills
- [ ] Routing row added to `.Doctrine.md` §6 (new skill) / §10 (new role)
- [ ] `ROLE_GATE` / `SKILL_EXTRA` entry added in `tools/doctrine_signature.py`
- [ ] `python tools/doctrine_signature.py --write` run; signature blocks not hand-edited
- [ ] Counts updated everywhere lint checks them

## Anything left undone

<!-- Known gaps, deliberate omissions, follow-ups. "Blocked" and "partially
     done" are respectable statuses here. Silence about a gap is not. -->

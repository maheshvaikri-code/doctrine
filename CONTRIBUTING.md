# Contributing to Doctrine

**Contributions are genuinely welcome** — and this is an unusual repo to
contribute to, because the thing you are changing is also the process you
change it by. Doctrine governs itself. Your pull request goes through the same
gates the doctrine prescribes for everyone else.

That sounds heavier than it is. Ceremony is right-sized: a typo fix is a
two-minute change, not a committee.

New here? Good first contributions are listed at the bottom.

## Ground rules — the four that actually matter

These are the [Non-Negotiables](.Doctrine.md) applied to contributors. Almost
every rejected PR fails one of them.

1. **Never fabricate.** Paste real output. "Tests pass" without a pasted run is
   the one thing this project cannot accept, because the whole premise is that
   honest reporting is enforceable.
2. **Behavior changes ship with tests.** A bug fixed is a regression test added,
   named after the bug.
3. **Never weaken a failing check to go green.** Fix the cause or say you are
   blocked. "Blocked" is a respectable status here.
4. **No secrets, ever.** Keys, tokens, `.env`. The `PreToolUse` guard will
   refuse them, but do not rely on it.

## Set up

Python **3.11+**. There are **no runtime dependencies** — that is a deliberate
design constraint, so please do not add any (see *Dependencies* below).

```bash
git clone https://github.com/aroora-ai-labs/doctrine
cd doctrine
python tools/doctrine_state.py init     # if you want the state plane locally
make verify                             # lint + ruff + tests
```

### Pin ruff to the CI version

CI pins **`ruff==0.15.15`**. A newer ruff enables new rules and will report
failures across files your change never touched — this is the single most
common false alarm for contributors.

```bash
pip install ruff==0.15.15
# or, without touching your environment:
uvx ruff@0.15.15 check tools tests
```

## The gates your change must pass

Exactly what CI runs — run them locally first:

| Gate | Command |
|---|---|
| Corpus lint | `python tools/doctrine_lint.py` |
| Ruff | `python -m ruff check tools tests` (**0.15.15**) |
| Tests | `python -m unittest discover -s tests` |
| Gold records | `python tools/doctrine_gold.py gate` |
| All of the above | `make verify` |

`doctrine_lint` is stricter than it looks. It checks that every backticked
`skills/…md` reference resolves, that plugin copies stay byte-identical to
their `.claude/` twins, that versions do not desync across carriers, and that
**every count claim matches the filesystem** — so if you add a skill, the
README numbers must move with it.

## Pick your class

Doctrine classifies work, and the classification sets the ceremony:

| Class | What it is | What is expected |
|---|---|---|
| **S** | typo, comment, doc tweak, config value — no behavior change | The change + a self-review. No brief, no plan. |
| **M** | feature, bugfix, refactor touching logic; one module | Plan → build → review → verification. Tests required. |
| **L** | new module, schema change, public API change, anything cross-cutting | Full G0→G7, including a brief and an ADR. |

Default to **M** if unsure. Maintainers may reclassify — that is normal and not
a criticism.

## Contributing to the corpus (roles, skills, standards)

The markdown *is* the product, so corpus changes get real review.

- **Match the shape.** Read two or three neighbours first. Skills use
  `# Skill:`, `**Scope.**`, `## Principles`, `## Do`, `## Don't`,
  `## Review checklist`, `## Common failure modes`. Role cards use frontmatter
  plus `**Mission.**`, `**Activates when.**`, `**Loads.**`, `**Hands off to.**`.
- **Earn the context budget.** Everything loads into a finite window. A
  playbook must say something a competent engineer would not already default
  to. Generic advice is a cost, not a contribution.
- **Write the failure modes.** The most valuable part of most playbooks is the
  list of ways it actually goes wrong. Prefer specifics you have seen over
  categories you can imagine.
- **Wire it up.** A new skill needs a routing row in `.Doctrine.md` §6; a new
  role needs a row in §10 and a `ROLE_GATE` entry in
  `tools/doctrine_signature.py`. Then run:

```bash
python tools/doctrine_signature.py --write
python tools/doctrine_lint.py
```

- **Do not hand-edit signature blocks.** They are generated between the
  `SIGNATURE:BEGIN/END` markers.

## Dependencies

Doctrine is **stdlib-only Python**, and that is a feature: it installs into any
repo on any OS with nothing to resolve, and the gates keep working in
air-gapped environments.

A new runtime dependency is very unlikely to be accepted. If you believe one is
necessary, open an issue **first** with the case, per
[`standards/dependency-policy.md`](.Doctrine/standards/dependency-policy.md).
Test-only and dev-only tooling is judged more leniently.

## Commits and pull requests

- **One logical change per commit** (§7 #6). Small and reversible.
- Follow [`standards/git-conventions.md`](.Doctrine/standards/git-conventions.md):
  `type(scope): summary` — `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
- **Explain the why in the body.** This repo's history is used as evidence;
  commit messages carry reasoning, not just a diff summary.
- **Paste real verification output** in the PR description. Not a claim that
  gates pass — the output.
- Stay in scope. Spotted an unrelated problem? Mention it; don't fix it in the
  same PR.

## What gets a PR rejected

Being direct so you do not waste effort:

- Claimed test results with no pasted output
- A behavior change with no test
- A check silenced, skipped, or narrowed to make CI green
- Placeholder or `TODO` code described as complete
- A new dependency added without the policy conversation
- A corpus addition that restates common knowledge at the cost of context
- Counts updated in one surface but not the others (lint catches this)

## Reporting bugs and proposing ideas

- **Bugs** — include the command, the **full real output**, your OS, and your
  Python and ruff versions. A reproduction beats a description.
- **Doctrine proposals** (a new role, skill, or gate change) — open an issue
  describing the *failure mode it prevents* before writing it. The bar is
  evidence that the gap is real, not that the idea is plausible.
- **Security** — do **not** open a public issue. See
  [SECURITY.md](SECURITY.md).

## Good first contributions

- Try the installer on one of your own repos and report where the docs misled
  you — genuinely valuable, and the fastest way to find real gaps.
- Add a language profile under `.Doctrine/standards/languages/`.
- Add failure modes to a skill you have real scars from.
- Improve an adapter in `.Doctrine/adapters/` for an agent you actually use.
- Tighten a lint or guard check — with a test that fails before your fix.

If a lint rule, a gate, or this document confused you, that is a defect worth
reporting. Confusion is a finding.

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Licence

Contributions are licensed under the [MIT Licence](LICENSE), the same as the
project.

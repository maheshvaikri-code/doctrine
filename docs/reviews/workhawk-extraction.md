# Code Review - WorkHawk application extraction @ 4ada7e2

**Reviewer roles:** Code Reviewer, Security Reviewer, Project Reviewer
**Date:** 2026-07-25
**Reviewed against:** [project brief](../briefs/workhawk-extraction.md),
[implementation plan](../plans/workhawk-extraction.md), and
[ADR-009](../adr/009-workhawk-application-boundary.md)

**Review method:** Serial fresh-hat review by the implementing agent. Sub-agent
delegation was not authorized for this task, so this is not represented as an
independent reviewer pass.

## Executed evidence

```text
npm run lint
exit 0

npm run typecheck
exit 0

npm test
6 tests; 6 pass; 0 fail

npm run audit
found 0 vulnerabilities

python -m unittest discover -s tests -p "test_doctrine_dashboard.py"
Ran 14 tests in 5.360s
OK

python -m ruff check tools/doctrine_dashboard.py tests/test_doctrine_dashboard.py
All checks passed!

python tools/doctrine_lint.py
doctrine_lint: corpus clean
```

Hosted evidence for exact commit
`4ada7e2c2353404533013d7d09f83fb5a07fc958`:

- [WorkHawk run 30189529300](https://github.com/aroora-ai-labs/doctrine/actions/runs/30189529300):
  Ubuntu success, Windows success, six of six production tests on both
  systems, zero dependency vulnerabilities, and hosted Chromium seven of seven.
- [Doctrine run 30189529281](https://github.com/aroora-ai-labs/doctrine/actions/runs/30189529281):
  Ubuntu and Windows on Python 3.11 and 3.12 all succeeded; each combination
  executed 186 tests.

## Findings

| # | Sev | Location | Finding | Resolution |
|---|---|---|---|---|
| 1 | [BLOCKER] | `workhawk/build/sites-vite-plugin.ts` | The repository-wide `build/` ignore rule silently excluded the moved Sites plug-in. A fresh checkout would therefore fail even though the local build retained the file. | Force-track the exact rename and assert its presence in the source/CI contract test. fixed@`8a0d63a` |
| 2 | [MINOR] | `workhawk/playwright.config.mjs` | Port `3003` was already occupied locally, causing the first E2E web-server attempt to stall instead of exercising the UI. | Add a digits-only, range-checked `WORKHAWK_E2E_PORT` override while keeping `3003` as the default. fixed@`8a0d63a` |
| 3 | [MINOR] | `workhawk/app/globals.css` | Adding four module rows could make the fixed navigation inaccessible on a short viewport because the sidebar did not scroll independently. | Add contained vertical scrolling and exercise a 390 x 600 viewport in hosted Chromium. fixed@`8a0d63a` |
| 4 | [MINOR] | `workhawk/tests/browser/workhawk.spec.mjs` | The first module assertion proved only one “Unavailable” label rather than the individual MAPLE, STIX, and Trust rows required by AC4. | Assert Doctrine connected and each future module unavailable by its own row. fixed@`8a0d63a` |
| 5 | [MINOR] | `workhawk/tests/browser/workhawk.spec.mjs:135` | The first hosted run used a non-exact `WORKHAWK` locator that also matched the footer and fixture commit title. The UI was correct, but one browser scenario failed strict locator resolution. | Scope the assertion to exact brand text; the next hosted run passed seven of seven. fixed@`43d1a30` |
| 6 | [MINOR] | `workhawk/public/workhawk-logo.png` | The human-supplied official logo arrived after the initial extraction review and was not part of the reviewed commit. | Preserve the exact raster in public assets, crop it non-destructively in the compact shell, and prove source presence, SSR reference, production HTTP delivery, and hosted browser rendering. fixed@`4ada7e2` |

All findings are resolved. The diff preserves the one-way
`WorkHawk -> Doctrine API` dependency, adds no executable module connector, and
does not move editor, terminal, identity, or remote-execution authority into
the frontend.

## Scope check

The implementation matches the approved extraction slices: application move,
product identity, typed module registry, Doctrine adapter preservation,
workflow migration, official brand raster, operating documentation, and
automated evidence. It does not deploy, publish, copy the frontend into
Doctrine consumers, or claim that MAPLE, STIX, and Trust are connected.

The official raster is tracked byte-for-byte at
`workhawk/public/workhawk-logo.png`. A separate derived
`workhawk/public/brand/workhawk-mark.png` remains untouched and untracked; it
is unused and is not represented as part of the reviewed build.

## Security review

- Staged credential-pattern scan found no secret-like assignment or private
  key.
- No dependency was added or upgraded; the npm lock dependency graph is
  unchanged apart from package identity, and audit reports zero
  vulnerabilities.
- WorkHawk does not use dynamic HTML injection, `eval`, caller-selected
  commands, or shell execution.
- The production test harness is the only frontend child process. It uses an
  argument array without a shell and deterministic termination.
- The Doctrine bridge remains loopback-only, exact-origin, bounded, and limited
  to its fixed verifier operation.

**Security verdict:** SIGN-OFF for the existing local single-user boundary.

## Verdict

- [x] Pass (0 open BLOCKER or MAJOR findings)
- [ ] Return to build

G4 passes.

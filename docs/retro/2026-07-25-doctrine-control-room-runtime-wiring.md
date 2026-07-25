# Retrospective - Doctrine Control Room runtime wiring - 2026-07-25

## Facts

Shipped locally: a versioned loopback bridge, truthful repository snapshot,
bounded verification action, validated API client, five-state live Control
Room, operating docs, 14 bridge tests, and two dashboard tests.

Gates walked: G0 through G4 completed; G5 automated and security checks passed;
real-browser G5 interaction testing is degraded/unavailable; no external
deployment occurred.

Defects caught after initial build: dirty-worktree attribution, mid-run
repository mutation, a non-terminal worker exception path, signed exit-code
parsing, reduced-motion/touch behavior, dead prototype CSS, contradictory gate
output, and newly disclosed frontend dependency advisories.

## What worked

- Small commits and named regressions made every review finding traceable.
- The bridge remained a narrow adapter: one fixed mutation, loopback only, no
  shell, no caller-selected command or path.
- Live negative evidence was useful. A stale verification stayed visible as
  partial evidence instead of being silently promoted to current truth.
- Re-running the dependency audit late in the loop caught advisory drift that
  an earlier clean result could not guarantee.

## What failed or hurt

- The first live verification was started while uncommitted work existed. It
  passed, but could not truthfully identify the behavior under test and was
  discarded.
- The first dependency remediation forced a new `brace-expansion` module shape
  under old `minimatch`; audit passed but lint crashed with
  `TypeError: expand is not a function`.
- `python -m unittest tests.test_doctrine_dashboard` failed because `tests/`
  is not an importable package. Discovery with `-s tests -p ...` is the correct
  repository command.
- The browser controller had no installed backend, preventing real interaction
  and screen-reader evidence.

## Root causes

### Evidence could be attributed to the wrong repository state

The run recorded only `HEAD` -> uncommitted files were not represented -> the
request boundary did not require a clean worktree -> the worker also did not
recheck state after completion -> evidence identity modeled a commit as the
whole executable state. Root cause: tooling model gap. Fixed with clean-tree
checks before acceptance and after execution.

### Contradictory gate output could pass

The parser counted four known gate records -> it assumed the verifier exit code
made their contents trustworthy -> an explicit `FAIL` was not included in the
overall predicate -> no adversarial contradictory-output test existed -> the
adapter was interpreting evidence more weakly than Doctrine itself. Root cause:
fail-closed logic and test gap. Fixed by requiring exact gate identity, all
`PASS`, exit zero, and a matching terminal success count.

### Audit-only override broke lint

The override targeted a vulnerable package globally -> old consumers expected
the CommonJS function export -> the patched major exposed a different module
shape -> audit success was treated as insufficient until lint ran -> aggregate
legacy config kept vulnerable transitive consumers in the graph. Root cause:
dependency-graph compatibility gap. Fixed by replacing the aggregate config
with current flat-config components and re-running clean install, lint, build,
tests, and audit.

## Doctrine and tooling amendments

| # | Amendment | Target | Class-S change filed? |
|---|---|---|---|
| 1 | Add browser-backed Control Room E2E coverage for loading, error, empty, partial, live, keyboard, focus, and reduced-motion behavior. | future dashboard CI workflow | no; application/tooling follow-up |
| 2 | Preserve the contradictory gate-output regression as a permanent fail-closed invariant. | `tests/test_doctrine_dashboard.py` | no; implemented |
| 3 | Treat an audit result as one gate in a dependency change, never as proof of runtime/lint compatibility. | project review checklist/plan evidence | no doctrine-law change needed |

## Honest negative findings worth remembering

- The verification attached to commit `e40e81d7a348` ran before later edits and
  is stale; it must not be cited as final evidence.
- A global `brace-expansion` override produced `found 0 vulnerabilities` but
  broke ESLint. That route was removed.
- Source/render contract tests are valuable but do not substitute for a real
  browser or assistive-technology pass.

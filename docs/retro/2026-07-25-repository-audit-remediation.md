# Retrospective — Repository Audit Remediation
<!-- G7 artifact. -->

## What worked

- The audit used executable counterexamples rather than relying on code-reading:
  compact TOML, misleading comments/tables, missing Ruff, and warnings-as-errors.
- Existing source/consumer scoping tests made the intended boundary explicit.
- Stdlib `tomllib` fixed the whole text-heuristic class without adding weight.
- The authoritative remote was checked before creating any tag.

## What failed

- Structured project metadata had been treated as raw text.
- A required quality gate was modeled as an optional convenience.
- Source-repo dogfooding favored Claude activation while marketing universal
  agent support.
- README numeric claims and release tags were outside existing consistency
  checks.
- The protocol test waited for its child but did not close all owned streams.

## Root causes

1. Early bootstrap logic optimized for a tiny implementation rather than a
   trustworthy boundary.
2. “Tool unavailable” was classified as “skip” instead of an environment error
   that must fail a source gate.
3. Activation criticality was evaluated from one client’s perspective.
4. Release records evolved faster than tag discipline.
5. Test success was checked without promoting resource warnings.

## Permanent changes

- Parse structured formats with their stdlib parser at trust boundaries.
- Required gate unavailable means failed, never green-with-skip.
- Universal boot is activation-critical and dogfooded at the source root.
- Supported Python minors are explicit CI matrix dimensions.
- Integration tests that own subprocess pipes close every stream and have a
  warnings-as-errors regression probe.

## Follow-up

Before any external push or release, run the GitHub Actions matrix and decide
whether the local `v0.6.46` tag should be pushed. That remains a human-gated G6
action.

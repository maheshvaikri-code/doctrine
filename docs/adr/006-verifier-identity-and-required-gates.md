# ADR-006 — Parsed Source Identity and Fail-Closed Required Gates
<!-- G1 artifact. Status: accepted. -->

## Context

`doctrine_verify` and `doctrine_lint` identified the Doctrine source repository
by searching for the literal text `name = "doctrineos"` in `pyproject.toml`.
Valid TOML formatting produced false negatives, while comments and unrelated
tables produced false positives. Separately, source verification skipped Ruff
when it was unavailable and still returned success.

## Decision

- Parse `pyproject.toml` with Python 3.11's stdlib `tomllib` and identify the
  source repository only when `[project].name == "doctrineos"`.
- Treat unreadable or malformed TOML as not proving source identity.
- Keep consumer verification scoped to Doctrine's installed surface.
- Treat Ruff as a required source-repository gate: unavailable means failed,
  with an actionable pinned-install message.
- Pin the same Ruff version in CI and exercise every declared Python minor.

## Alternatives considered

1. **More flexible regular expression.** Rejected because regex still cannot
   reliably distinguish TOML tables from comments and strings.
2. **Add a dedicated source marker file.** Viable, but duplicates identity
   already defined by PEP 621 metadata and creates another consistency carrier.
3. **Continue skipping unavailable Ruff.** Rejected because a green verifier
   would not mean all advertised source gates executed.

## Consequences

- No new dependency: `tomllib` is available at the declared Python floor.
- Consumer repositories containing the word `doctrineos` no longer run their
  host suites accidentally.
- Fresh source checkouts must install the pinned Ruff gate before verification
  can report success.

## Invalidation trigger

Revisit if Doctrine stops using PEP 621 project metadata or lowers its Python
floor below 3.11.

# Standard: Coding Standards

General rules first; language sections override where they speak.

## General
- Optimize for the reader. Code is read ~10× more than written; the reader
  is a stranger under time pressure.
- Names are the first documentation: `remaining_retries` not `n`;
  functions are verbs, values are nouns, booleans read as predicates
  (`is_ready`, `has_expired`).
- Functions do one thing; if you need "and" to describe it, split it.
  Depth of nesting > 3 is a smell; early-return the edges.
- Comments explain **why** (constraints, tradeoffs, links to issues/ADRs).
  A comment explaining *what* means the code failed — fix the code.
- No magic values: name constants, with units in the name where ambiguity
  is possible (`TIMEOUT_SECS`).
- Formatting is the formatter's job, enforced in CI. Nobody debates
  whitespace in review, ever.
- Public surface documented; internal helpers earn docs when non-obvious.

## Rust
- Toolchain: `rustfmt` (check in CI) · `clippy --all-targets -- -D warnings`
  · MSRV declared in `Cargo.toml` and tested in CI.
- Errors: `Result` everywhere fallible. Libraries: `thiserror` enums with
  meaningful variants. Binaries: `anyhow` with `.context()` at each layer.
- **No `.unwrap()`/`.expect()` in library code paths.** Permitted in tests,
  examples, and `main` startup where failure is unrepresentable — with
  `expect("why this cannot fail")` phrasing.
- `unsafe` is a loan against review time: minimal block, `// SAFETY:`
  comment stating the upheld invariants, Security-Reviewer eyes at G5.
- Ownership idioms: borrow before clone; `&str`/`&[T]` in APIs over owned
  where possible; `impl Trait` params for flexibility; avoid lifetime
  gymnastics a small redesign would erase.
- No `panic!` for expected conditions; panics are for broken invariants.
- Prefer exhaustive `match` over `_` arms on your own enums — let the
  compiler find your missed cases when variants grow.

## Python
- Target modern supported minors (declare in `pyproject.toml`).
- Tooling: `ruff` for lint **and** format · `pyright` (or mypy strict) —
  clean on new/changed code; legacy debt tracked, not ignored inline.
- Type hints required on all public functions and encouraged everywhere;
  `Any` is a flagged exception, not a habit.
- Data at boundaries: `dataclasses` (internal) / `pydantic` (parsing
  external input); dicts don't cross module boundaries as pseudo-objects.
- Idioms: `pathlib` over `os.path` · f-strings · context managers for every
  resource · comprehensions until they stop being readable · no mutable
  default arguments · explicit `__all__` or underscore-private convention.
- Exceptions: package-rooted hierarchy; catch narrowly; `raise X from err`
  to preserve cause; library code raises, application edges decide.
- `logging`, never `print`, in importable code.

## TypeScript / UI code
- `strict: true`; no `any` without an inline justification comment.
- Types at the data boundary (parse/validate responses); interfaces for
  public props; discriminated unions over boolean flags.
- ESLint + Prettier in CI, same as everything else: enforced, not debated.

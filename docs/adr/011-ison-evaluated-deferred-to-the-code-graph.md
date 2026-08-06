# ADR-011: ISON/ISONL/ISONGraph evaluated, adoption deferred to the code graph
<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-08-06 · **Status:** accepted
**Deciders:** Chief Architect + human (framework owner, also the ISON author)

## Context

`skills/graphify.md` and its integration were removed in `d838896`/`807a304`,
leaving Doctrine with no structure-retrieval capability. ISONGraph
([ISON-format/isongraph](https://github.com/ISON-format/isongraph), MIT,
`ison-graph` 1.2.0, first-party) was proposed as the replacement.

Two facts settled the shape of the question:

1. **ISONGraph is not an extractor.** Its own README: *"ISONGraph is **not** a
   code analysis or AST parsing tool… no code-scanning, tree-sitter
   integration, or static analysis. It assumes graphs are already built."*
   graphify's job was turning source into a graph; ISONGraph starts one step
   later. It is the layer beneath the vacancy, not a drop-in for it.
2. **The published benchmarks are real and were reproduced in kind** — they
   measure token efficiency of *representation*, on data whose rows share a
   shape. Doctrine's context is prose by design.

## Decision

We will **not** adopt ISON, ISONL, or ISONGraph into Doctrine now, and will
**not** add `ison-graph`/`ison-py` as a dependency. The evaluation is recorded
here so it is not re-run. Adoption is deferred until the first-party graphify
replacement exists, at which point the code graph — high-volume, uniform,
genuinely graph-shaped — is the data these formats are for.

## Evidence

Measured against this repo's own state plane, tokens at the repo's own
accounting (`TOKEN_CHARS = 4`), minified JSON as the baseline:

| State | Rows | Shape | ISON | ISONL |
|---|---|---:|---:|---:|
| Distillate, typed nodes | 15 | prose-heavy | **+12.4%** | +12.7% |
| Distillate, one mixed node type | 12 | prose-heavy | **−2.3%** | −2.0% |
| `DECISIONS.ndjson` | 21 | prose-heavy | +8.3% | **+8.5%** |
| Checkpoint control blocks | 31 | short uniform fields | +28.2% | **+28.7%** |

**ISONL beat ISON on every shape**, by 0.2–0.5 pp. If anything is ever wired,
it is ISONL.

**The decisive measurement** is the hydration bundle's composition — the only
place Doctrine puts state into a context window:

| Section | Tokens | Shape |
|---|---:|---|
| Invariants | 843 | prose |
| Distillate | 1,576 | prose |
| Active intents | 9 | structured |
| Decisions | 13 | structured |
| Unresolved effects | 11 | structured |

**Structured data totals ~33 of 2,524 tokens.** At +28.7% that is a **~9-token**
saving — in exchange for Doctrine's first runtime dependency, against a
zero-dependency install that is a stated product promise (README badge,
`05-packaging.md`) and the reason the corpus installs into any repo with
nothing to resolve. `standards/dependency-policy.md` exists to refuse exactly
this trade, and being first-party makes the discipline more necessary, not
less.

## The finding most likely to be re-derived painfully

**ISON factors repeated keys *per node type*.** Modelling the same distillate
as typed nodes (`claim`, `dead_end`, `open_thread`) yields **+12.4%**; modelling
it as one node type with a discriminator field yields **−2.3%** — *worse than
minified JSON*. Same data, same library.

Any future integration must therefore **own its node-type mapping inside a
shim**, never leave typing to the caller. A lazily-typed integration will
measure as a regression and be blamed on the format.

## Consequences

- No dependency added; the zero-dependency install claim stays true.
- The `graphify` routing row stays removed. Nothing points at a tool that is
  not there — a routed skill that silently does nothing reads as covered when
  it is not.
- When the first-party extractor lands, it fills that vacancy with ISONGraph
  underneath, and `integrations/README.md`'s contract applies: pinned version,
  **verified** date with pasted output, and a documented degrade path when the
  library is absent.
- ISONCS is a genuine conceptual match for the state plane's canonicalization
  (UTF-8, LF, sorted keys, single trailing newline). It is **not** adopted:
  all 31 checkpoints were re-chained on 2026-08-05, and changing
  canonicalization invalidates every hash again, in this repo and in every
  consumer. If ever worth doing it is a standalone migration with its own
  backup, never a side effect of adopting a serializer.

## Revisit when

The extractor produces a real `graph.json`-equivalent for this repo. Re-run the
measurement against **that** artifact — uniform, high-volume, graph-shaped — and
decide on those numbers, not these.

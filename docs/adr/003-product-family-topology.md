# ADR-003: Product-family topology — three repos, one-way deps, a compatibility contract

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-07-14 · **Status:** accepted (topology); family gate enforcement deferred
**Deciders:** Chief Architect (+ human: "say go and I'll formalize it")

## Context

The stack has grown into a product family: DOCTRINE (governance law + the `doctrineos`
tooling), MAPLE (`maple-oss`, the multi-agent runtime, AGPL, first-party), and a
forthcoming first-party product — a "governed engineering organization you talk to"
(the daemon + chat gateway scoped in `docs/briefs/productization.md`). These want
different licenses, release cadences, and
visibility, so a monorepo would force the most restrictive of each on all. But three
repos that must run together need a written contract for "which versions work with which,"
or they drift into a knot. This ADR fixes the topology before the product repo spins up,
so the contract precedes the code.

## Decision

We will keep **three separate repos** with a **one-way dependency graph**: the product
(`product-app`) depends on both `doctrine` and `maple-oss`; `doctrine` and `maple-oss` stay
independent of each other (Doctrine treats MAPLE as an opt-in integration; MAPLE does not
know Doctrine exists). No cycles. **Doctrine governs each repo individually** (install the
law into each — already true for `maple-oss`). Cross-repo coordination is a **compatibility
manifest** (`templates/compatibility-manifest.md`) filled into the product repo: it pins
the certified `doctrine` + `maple` versions for each product release and records the
integration-test evidence. The product's release/promotion carries a **family gate** — the
product does not promote unless its pinned stack passes the Doctrine↔MAPLE family smoke
(the shape in `integrations/maple.md`). **This ADR is homed in the `doctrine` repo** (the
governance vantage); the running family gate is **deferred** until `product-app` exists — a
gate for a repo that is not there yet is unenforceable and premature.

## Alternatives considered

| Option | Pros | Cons | Why not |
|--------|------|------|---------|
| A (chosen): 3 repos, one-way deps, compatibility manifest + deferred family gate | independent licenses/cadence/visibility; no cycles; contract precedes code | cross-repo version coordination is real ongoing work | it is the honest shape of the family |
| B: monorepo | one CI, one version, atomic changes | AGPL (MAPLE) spreads to all; forced lockstep releases; MAPLE already public and separate | licensing + cadence make it a non-starter |
| C: 3 repos, no written contract | zero process | "which versions work together" becomes tribal knowledge; drift is silent | the exact failure a family gate prevents |
| D: build the running family gate now | complete | `product-app` does not exist; a gate over a missing repo is fiction | deferred, not skipped — recorded here |

## Consequences

- **Positive:** each repo moves at its own speed under its own license; the dependency
  graph is acyclic and legible; the version-compatibility contract is written before the
  product repo exists, so it guides creation instead of being retrofitted.
- **Negative / debt accepted:** someone must keep the manifest current on each product
  release (a release-manager duty); the family integration gate is designed but not yet
  enforced (no `product-app` to enforce it in). Both are named, not hidden.
- **Invalidation triggers:** a decision to monorepo after all (would supersede this);
  a fourth first-party component joining the family (extend the graph, keep it acyclic);
  `product-app` coming into existence (activates the deferred family gate — its own G1).

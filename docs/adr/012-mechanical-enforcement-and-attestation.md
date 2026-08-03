# ADR-012: Mechanical enforcement at the tool boundary, attestation via git
<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-08-03 · **Status:** accepted
**Deciders:** Chief Architect + human (scope approved: "fix everything")
**Extends:** ADR-004 (activation layer), ADR-005 (MCP tool governance)

## Context
Doctrine states ten Non-Negotiables and a gate pipeline, then relies on the
agent to honour them. Activation (ADR-004) makes the law *present*; it does not
make it *binding*. An agent that ignores the engagement block, edits a
protected file, or writes a credential meets no mechanism — only prose. At the
release boundary, `doctrine_gold` enforces evidence rigorously but proves
consistency, not authorship: the entire chain is recomputable by anyone with
repository write access, so a gold record answers "was this internally
coherent?" and never "who approved it?".

Both gaps are the same shape: the system trusts a narrator. An enterprise
control plane cannot.

## Decision
We will bind the doctrine at two mechanical boundaries and nowhere else.

**At the point of action**, `tools/doctrine_guard.py` runs as a `PreToolUse`
hook and returns a deny decision for four classes: secret-shaped content
entering the repository, writes to protected paths, destructive shell commands,
and writes attempted by a verifier role. It is a *decision* hook, not an
advisor: a denial stops the tool call. Outside a Doctrine repository it exits
silently (fail-open, because the law is not in play); inside one, an input it
cannot parse is denied (fail-closed, because a governed repo must not gain a
bypass by malforming a request).

**At the promotion boundary**, attestation rides on git's existing signature
verification (`git verify-tag`) rather than a new trust system. A signed
annotated tag already carries a cryptographic identity the developer controls;
`doctrine_gold record` records that identity in the gold record, and
`--require-signature` refuses promotion without it. Doctrine adds no key
custody, no CA, no network dependency, and no third-party client.

## Alternatives considered
| Option | Pros | Cons | Why not |
|--------|------|------|---------|
| A (chosen): PreToolUse guard + git-native signature | Denies at the point of action; zero new deps; uses keys the org already manages | Guard is per-agent-runtime wiring; git signing must be configured by the human | — |
| B: sigstore/cosign keyless signing | Strong identity, transparency log | New dependency + network + OIDC identity provider = §5 escalation, and unusable offline | Deferred; the record format leaves room for it |
| C: Post-hoc audit of transcripts | No runtime coupling | Detects after the damage; cannot deny | Detection is not enforcement |
| D: Do nothing (status quo) | No work | Leaves the audit's headline finding open | Rejected by the brief |

## Consequences
- Positive: the four Non-Negotiables most often violated in practice
  (secrets, scope, irreversible actions, separation of duties) become
  mechanical rather than rhetorical. Promotion can now answer "who signed".
- Positive: no new dependency, so the stdlib-only constraint and the offline
  install path survive intact.
- Negative / debt accepted: the guard binds only agents that honour a
  `PreToolUse` contract (Claude Code today). Other runtimes still rely on the
  adapter overlays; the tool is written runtime-neutral (JSON in, JSON out) so
  a second adapter is wiring, not a rewrite.
- Negative / debt accepted: git signature verification proves the *tag* was
  signed by a key in the verifier's trust store. It does not prove the signer
  read the evidence, and an unsigned-by-policy repo gains nothing until the
  human configures signing keys.
- Negative / debt accepted: pattern-based secret detection has false positives
  and false negatives. It is a floor, not a replacement for a scanner.
- Invalidation triggers: a runtime-neutral enforcement standard across agents
  (reopen the guard's coupling); org policy requiring transparency-log
  attestation (reopen option B); the guard producing enough false denials that
  users disable it (reopen the pattern set, not the mechanism).

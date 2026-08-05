# ADR-010: Mechanical enforcement at the tool boundary, attestation via git
<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-08-03 · **Status:** accepted, amended 2026-08-03 (see
Correction below)
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
hook and returns a decision for four classes: **deny** for secret-shaped
content entering the repository and for writes to protected paths (immutable
evidence, the installed corpus in a consumer repo); **ask** for destructive or
external shell commands (§5), for edits that weaken a test (§7 #4), and for
writes to the repo's own enforcement surface. It is a *decision* hook, not an
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

## Correction 2 (2026-08-04, after four rounds) — READ THIS FIRST

The decision below says the doctrine is bound "at two mechanical boundaries."
**Only one of them is a boundary.** Five independent security passes, each
attacking the previous one's fixes, established that:

- **Write/Edit interception is sound** for the paths it is handed: a file path
  is data.
- **Bash interception is a tripwire, not a boundary.** Shell is
  Turing-complete; no static text analysis of it is complete. Rounds 1–4 each
  found new spellings (redirects; `touch`/`install`/`git checkout`; `env`
  wrappers, newline segmentation, `awk` program text; then `cd` chains,
  container renames and glob deletes). Every round was fixed and the next
  round found more. Treat it as catching the accident and the careless, never
  as containment for a determined actor inside the repo.
- **Attestation proves the tag was signed, never the record.** Records are
  written *after* their tag, so no signature covers a record's contents.
- **`doctrine_gold gate` verifies against HEAD, not against history.** Its
  first version hashed each file against a hash stored *in the record it was
  verifying*, so a self-consistent forgery passed. A second version anchored
  on git's committed copy plus a manifest, and a **fifth** independent pass
  showed that was still narrower than the words around it: deletion detection
  depended entirely on the manifest (a legacy repo has none), and — the limit
  that remains — an actor with ordinary commit access can forge a record and
  commit the forgery in one step, with no amend and no force-push, and the
  gate has no prior state to diff it against. Deletion/relocation is now
  checked against git's *history* on the directory, not only its current
  tree, closing the manifest-only gap. The single-commit-forgery gap is not
  closeable by any HEAD-relative check; it is not "fixed", it is disclosed,
  and it is caught by a human reading the diff before a release-bound merge,
  not by another automated gate. Full account, including what "CI on the
  pushed commit" does and does not add: `.Doctrine/05-packaging.md`.

Nothing below is deleted, because the errors are the record. Where the text
below says "boundary", read the table in `.Doctrine/05-packaging.md`.

## Correction (2026-08-03, after independent verification)

This ADR originally listed **"writes attempted by a verifier role"** as the
fourth deny class, and claimed separation of duties had become mechanical.
Three independent verifiers found that no such rule exists in the code, and
never did. The decision text above has been corrected to describe what ships.
The record of the error stays here, because an ADR that quietly rewrites
itself teaches nothing.

**Why the rule was dropped, and why that is the right call.** The `PreToolUse`
payload carries no role. Any marker the agent writes to announce "I am the
reviewer now", the agent can decline to write — enforcement on a self-attested
signal is the security theater `skills/ai-slop.md` exists to catch.

**What actually enforces it**, per the verifier-dispatch rule now in
`02-role-protocol.md`: verifier subagents are dispatched with tool grants that
exclude Edit/Write. **This is partial, and the gap must be stated**: those
grants include `Bash`, which is a write channel — a security reviewer
demonstrated it by creating files with `cat >` after the guard denied the
equivalent redirect. So the isolation is real against a reviewer that edits
by accident, and porous against one that decides to. Closing it needs either
a role-aware payload from the runtime or a Bash-free verifier grant; that is
tracked as P2.3 in `docs/plans/next-phase-v0.8.0.md`, not claimed here.

Two further corrections from the same pass, both now fixed in code: the
guard's own policy file and `pyproject.toml` were writable, so the governed
agent could switch the whole control off in one call; and the command-path
rule matched raw substrings, which both let non-redirect write primitives
through and denied ordinary work. See `docs/reviews/enterprise-control-plane.md`.

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

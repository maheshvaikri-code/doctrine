# Brief — Enterprise Control Plane (v0.7.0)
<!-- G0 artifact. Task class: L (new modules + cross-cutting). -->

## Problem
Doctrine's audit found the law well specified but thinly enforced. Four gaps
block use as an enterprise development operating layer:

1. **Enforcement is model obedience.** The shipped hooks run only at
   `SessionStart` and `UserPromptSubmit`. Nothing mechanically stops an agent
   from writing a secret, editing a file its role may not touch, or reporting a
   gate it never ran. The doctrine's Non-Negotiables are advisory at the point
   of action.
2. **No attestation.** `human_approval` in a gold record is free text and
   sign-offs are content hashes. The chain proves internal consistency, never
   authorship: anyone with repository write can recompute it whole.
3. **Single CI vendor.** Only GitHub Actions ships. Repos on GitLab or Azure
   DevOps have no supported gate wiring.
4. **No cross-repo view.** Every artifact is per-repo. A portfolio running
   Doctrine in N repositories has no way to see installed versions, drift from
   source, state posture, or release distance without visiting each one.

A fifth defect surfaced during the audit: the bridge test suite failed
intermittently (~1 run in 6 under load).

## Scope
1. `tools/doctrine_guard.py` — a `PreToolUse` decision hook: fail-closed
   secret blocking, protected-path refusal, destructive-command refusal, and
   verifier write-isolation. Denies at the point of action, before the edit.
2. `doctrine_gold` attestation — verify the release tag's cryptographic
   signature through git (GPG/SSH keys the developer already holds), record the
   signer identity in the gold record, and offer `--require-signature` so a
   pipeline can refuse unsigned promotion.
3. `tools/doctrine_fleet.py` — cross-repo status: installed doctrine version,
   drift against a source tree, state-plane posture, worktree cleanliness,
   latest gold record; text and JSON output.
4. GitLab CI + Azure DevOps gate templates at parity with the Actions workflow.
5. Root-cause fix + deterministic regression test for the bridge flake.

## Non-goals
A hosted control plane or server-side policy distribution; certificate
authorities, key custody, or a signing service (key choice is the human's);
rewriting the state chain's crypto; auto-remediation of fleet drift (the fleet
tool reports, the human decides); scanning a host repo's own code.

## Acceptance criteria

> **Amended 2026-08-03**, after independent verification. The first criterion
> below originally required the guard to deny "a verifier-role write". That
> rule was never implemented and could not be, because the hook payload
> carries no role and a self-attested one proves nothing (ADR-012,
> Correction). The criterion is corrected here rather than quietly dropped —
> narrowed scope is reported scope. Verifier isolation now lives in the
> dispatch rule in `02-role-protocol.md`, with its Bash-shaped gap stated.

- The guard **denies**, with a reason, a secret-shaped write and a write to a
  protected path; it **asks** on a §5 destructive/external command, on an edit
  that weakens a test, and on a write to the repo's own enforcement surface —
  and stays silent on ordinary edits and on reads. Malformed or unknown input
  never crashes the agent, and never yields silence inside a governed repo
  (fail-open only where the doctrine is not in play; fail-closed within it,
  including payloads that fail to parse at all).
- `doctrine_gold record` refuses an unsigned tag under `--require-signature`,
  records signer identity when the tag is signed, and behaves exactly as
  before without the flag (no existing record shape breaks).
- `doctrine_fleet status` reports version/drift/state/release for N repos, in
  text and JSON, never mutating a repository it inspects.
- The bridge regression test fails against the pre-fix module and passes after.
- `doctrine_lint` clean, `ruff` clean, full suite green, run at the end on the
  final commit with real output pasted.

## Constraints
Python ≥3.11, stdlib only, Windows + POSIX. No new dependency (a signing
service or `sigstore` client would be a §5 escalation). The guard must never
be a silent bypass: when it cannot evaluate a request inside a Doctrine repo,
it denies rather than allows.

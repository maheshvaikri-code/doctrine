# ADR-010: Project bridge execution state into WorkHawk

**Date:** 2026-07-26
**Status:** accepted
**Deciders:** Chief Architect

## Context

The Doctrine bridge already owns a single bounded verification job and exposes
both the repository snapshot and a dedicated current-verification resource.
WorkHawk starts that job but currently polls the full snapshot, has no separate
start-request state, and does not expose the job record as an operator surface.
The UI must become operationally complete without gaining command authority or
creating a second execution-state owner.

## Decision

WorkHawk will treat the bridge as the sole verification-state authority. The
client will hold a temporary `starting` lock only while the POST is unsettled,
then project the accepted `Verification` record into the current snapshot. A
running job will be polled through `GET /api/v1/verifications/current` every
1.5 seconds. Terminal state will stop that poll and trigger one full snapshot
refresh to reconcile repository-level partial reasons and evidence. The UI will
render only contract fields and will preserve the last valid record if a poll
fails.

```text
operator
   |
   | start (eligible + client lock)
   v
WorkHawk ---- POST /verifications ----> Doctrine bridge
   |                                      |
   |<------- accepted Verification -------|
   |
   |---- GET /verifications/current ----> |  every 1.5 s while running
   |<------- authoritative record --------|
   |
   `---- GET /snapshot ------------------> |  once after terminal state
```

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Dedicated current-resource polling (chosen) | Uses the existing bounded contract; avoids repeatedly collecting Git/evidence state; preserves one execution owner | Still periodic rather than event-driven | - |
| Continue polling the full snapshot | Already implemented; terminal state eventually appears | Recollects unrelated repository data every 1.5 seconds and obscures the execution resource | Wasteful and semantically imprecise |
| Add SSE or WebSocket execution events | Lower latency and natural event flow | New server/public contract, reconnect semantics, browser lifecycle, and test surface | No demonstrated need for sub-second updates |
| Optimistic client-side gate progression | Visually active without polling | Fabricates states the verifier has not reported | Violates evidence integrity |

## Failure modes

- **Start request rejects:** clear the temporary lock, retain the prior
  snapshot, and announce the bridge's stable actionable message.
- **Start response is lost:** clear the lock and refresh the snapshot so an
  accepted server-side job can be rediscovered without retrying the POST.
- **Current poll fails:** retain the last valid verification, mark execution
  synchronization degraded, and continue bounded polling while the last status
  is running.
- **Terminal snapshot refresh fails:** retain the terminal verification record
  and identify repository synchronization as degraded; do not erase completion.
- **Repository is dirty:** prevent the POST in the browser while preserving the
  bridge's authoritative dirty-tree rejection as defense in depth.
- **Component unmounts:** abort outstanding snapshot, start, and current-run
  requests.

## Consequences

- Positive: the operation has one owner, one explicit lifecycle, and visible
  evidence from acceptance through completion.
- Positive: polling becomes cheaper and matches the resource being observed.
- Positive: duplicate browser POSTs are prevented without weakening the
  bridge's concurrency guard.
- Negative: WorkHawk maintains two bounded read paths and one additional
  synchronization status.
- Negative: a temporary poll outage is visible as degraded even when the
  underlying verifier continues successfully.
- Invalidation triggers: a versioned event-stream contract, durable run ledger,
  cancellation authority, or multiple concurrent jobs would reopen this
  decision.

# Project Brief - WorkHawk verification execution wiring

**Date:** 2026-07-26
**Class:** L - completes a cross-cutting browser-to-bridge execution lifecycle
across the API client, operator UI, browser QA, architecture, and operating
evidence
**Requested by:** human

## Problem

WorkHawk can start Doctrine verification, but it does not yet present the
operation as a complete execution lifecycle. The start request has no explicit
client-side in-flight lock, the UI polls the entire repository snapshot instead
of the existing current-verification resource, dirty-tree rejection is only
discovered after an attempted run, and the accepted job's identity and timing
remain hidden. Operators need one truthful execution surface that makes it
obvious what can run, what is running, what completed, and why an operation is
unavailable or failed.

## Scope

- **In:** Consume the existing Doctrine v1
  `GET /api/v1/verifications/current` operation while a job is running.
- **In:** Add an immediate starting state that prevents duplicate POSTs before
  the bridge returns the accepted job.
- **In:** Reconcile terminal verification state with one full repository
  snapshot refresh.
- **In:** Present bounded execution metadata already returned by the contract:
  run ID, commit, start/finish times, duration, exit code, test count, status,
  and gate results.
- **In:** Disable verification before execution when the snapshot reports a
  dirty tree, and name the exact remediation in visible text.
- **In:** Keep the last verified execution visible when current-run polling
  temporarily fails, while identifying synchronization as degraded.
- **In:** Cover accepted, running, completed, dirty, rejected, polling-error,
  loading, partial, empty, and bridge-error paths in browser and source tests.
- **Non-goals:** Arbitrary command execution, cancellation, process output
  streaming, durable run history, MAPLE/STIX/Trust connectors, evidence export,
  remote authentication, release publishing, or external deployment.
- **Deferred:** Server-sent execution events, cancellation, signed result
  export, and a durable multi-run ledger.

## Acceptance criteria

1. Given a clean repository and no active run, when the operator starts
   verification, then WorkHawk disables every verification trigger before the
   request settles, sends exactly one POST, and announces that the request is
   starting.
2. Given an accepted verification, when its status is running, then WorkHawk
   polls only `/api/v1/verifications/current`, updates gate/execution evidence
   from each valid response, and stops polling after a terminal status.
3. Given a terminal current-verification response, when WorkHawk reconciles the
   run, then it performs one repository snapshot refresh and presents the
   terminal status, run identity, commit, elapsed time, exit code, and observed
   test count without invented fields.
4. Given a dirty repository snapshot, when the operator inspects either the
   primary action or command palette, then verification is disabled, the UI
   says to commit or stash changes, and no POST is sent.
5. Given a rejected start request, when the bridge returns its stable error,
   then the UI announces the exact actionable message, clears the starting
   state, and permits retry when the repository remains eligible.
6. Given current-run polling fails after a job was accepted, when the last
   valid run is still available, then WorkHawk retains that evidence, labels
   execution synchronization as degraded, and permits a manual repository
   refresh rather than replacing the whole dashboard with an error state.
7. Given desktop or a 390-pixel viewport with reduced motion, when the complete
   execution flow and failure states are exercised in Chromium, then all
   controls remain keyboard operable, async changes are announced, there is no
   horizontal overflow, and automated WCAG A/AA checks report no violations.
8. Given dependency and authority review, when the change is inspected, then
   the v1 bridge contract and fixed-verifier authority are unchanged and no
   dependency has been added.

## Constraints

- Existing API v1 shapes and endpoint paths remain unchanged.
- Polling cadence remains bounded at 1.5 seconds and every fetch is abortable.
- WorkHawk must never infer gate completion, process output, or connector state.
- The Doctrine bridge remains loopback-only, exact-origin, single-job, and
  fixed-command.
- Motion remains the sole animation runtime.
- External publishing remains a human approval gate.

## Assumptions

- "Proper execution" means completing the existing bounded Doctrine
  verification lifecycle, not expanding WorkHawk into a general command
  runner.
- The bridge remains the authoritative owner of execution state; browser state
  is a disposable projection.
- The current snapshot remains the source for repository eligibility.

## Open questions

- None blocking. Cancellation, streamed output, and durable history change the
  authority or contract and are intentionally deferred.

**Human confirmed:** yes - the instruction explicitly requests continuing the
UI wiring with proper execution.

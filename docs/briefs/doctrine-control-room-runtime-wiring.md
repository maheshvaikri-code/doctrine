# Project Brief - Doctrine Control Room runtime wiring

**Date:** 2026-07-25

**Class:** L - adds a local service boundary and a versioned HTTP API

**Requested by:** human

## Problem

The Control Room currently looks operational but displays invented portfolio
values and queues prototype actions. A Doctrine operator cannot use it to learn
the current repository state or run the verification gate, and the realistic
placeholder data can be mistaken for evidence.

## Scope

- **In:** Connect the existing dashboard to the current Doctrine repository
  through a loopback-only local bridge.
- **In:** Display real repository identity, activation posture, state-chain
  status, recent Git activity, evidence counts, and release identity.
- **In:** Run one allowlisted action, Doctrine verification, with progress and
  final gate evidence.
- **In:** Make loading, empty, partial, error, and success states arise from
  real runtime conditions.
- **In:** Version and document the JSON contract and local operating steps.
- **Non-goals:** Multi-repository portfolio aggregation, remote hosting,
  authentication, organization/user management, MAPLE or STIX connectors,
  evidence export, Gold promotion, release publishing, and arbitrary command
  execution.
- **Deferred:** Authenticated remote bridge, portfolio registry, durable run
  history, signed evidence export, and OpenHawk/MAPLE/STIX telemetry.

## Acceptance criteria

1. Given the bridge is available, when the dashboard loads, it shows the
   current repository name, version, branch, commit, working-tree state,
   activation checks, state checkpoint, evidence counts, and recent commits.
2. Given a clean worktree and no verification is running, when an operator
   chooses **Run verification**, the bridge returns an accepted job, the UI
   shows progress, and the final status shows each Doctrine gate and the
   observed test count.
3. Given the bridge is unavailable, when the dashboard loads or retries, an
   accessible error state explains how to start the bridge and never presents
   prototype values as current evidence.
4. Given partial repository state, such as no prior verification or a degraded
   activation check, the UI identifies the exact missing evidence while
   preserving the verified snapshot fields.
5. Given an unapproved browser origin, dirty worktree, non-JSON mutation
   request, body larger than 1 KiB, or a second concurrent verification
   request, the bridge rejects it without executing a command.
6. Given a verification request, the bridge invokes only the repository's
   fixed `tools/doctrine_verify.py` path with the current Python interpreter,
   no shell, and a bounded runtime/output.
7. Production build, lint, dashboard tests, bridge tests, Doctrine verification,
   and the runtime dependency audit pass locally.

## Constraints

- Python 3.11+ and Node.js 22.13+.
- No new runtime dependency.
- Bridge binds to `127.0.0.1`; default allowed UI origins are
  `http://localhost:3003` and `http://127.0.0.1:3003`.
- Request body is capped at 1 KiB, captured verification output at 32 KiB, and
  verification runtime at 180 seconds.
- Existing Sites/Vinext structure and visual language remain intact.
- External publishing remains a human approval gate.

## Assumptions

- The first operational release controls one trusted local repository.
- The operator starts the bridge and dashboard from the same machine.
- A verification is intentionally non-destructive but may consume CPU for
  roughly one minute.
- Company profile: off. Merge profile: standard.

## Open questions

- None blocking. Remote and multi-repository operation are explicitly deferred.

**Human confirmed:** yes, through the 2026-07-25 instruction to wire the UI and
continue autonomously.

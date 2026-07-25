# ADR-008: Use a loopback bridge for Doctrine Control Room operations

**Date:** 2026-07-25

**Status:** accepted

**Deciders:** Chief Architect; security design reviewed at G5

## Context

Doctrine's authoritative state and enforcement tools are repository-local
Python programs and files. The Vinext dashboard can run in a browser or
Cloudflare Worker, neither of which may read the operator's filesystem or spawn
those tools. The UI needs a narrow runtime boundary without turning a visual
surface into a general-purpose remote shell.

## Decision

We will add a Python standard-library HTTP bridge that binds only to
`127.0.0.1`. It exposes a versioned read-only snapshot and one asynchronous,
allowlisted verification operation. The React client parses the returned
contract at its boundary and derives all five UI states from real conditions.
The bridge rejects unknown browser origins, non-JSON or oversized mutations,
dirty-worktree verification, and concurrent verification requests. It invokes
a fixed script path using an argument array, never a shell.

The v1 boundary is:

- `GET /api/v1/health`
- `GET /api/v1/snapshot`
- `GET /api/v1/verifications/current`
- `POST /api/v1/verifications`

The committed OpenAPI document is the contract. Additive optional fields are
compatible within v1; removal, changed meaning, or changed types require v2.

## Data flow

```text
Browser UI
  | GET snapshot / POST verification
  v
127.0.0.1 bridge
  |-- parses pyproject.toml and Doctrine state artifacts
  |-- reads bounded Git metadata through fixed argument arrays
  |-- audits Doctrine activation through doctrine_awaken
  `-- runs tools/doctrine_verify.py as one bounded background job
        |
        `-- returns stable JSON status; captured output is truncated to 32 KiB
```

When the bridge is absent, the UI enters its error state. When some evidence is
missing or stale, it enters partial state and names the gaps. A failed
verification is live negative evidence, not a transport error.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Loopback stdlib bridge (chosen) | Uses Doctrine's real local authority; zero dependency; narrow blast radius | Requires a second local process; remote use is deferred | - |
| Execute Python from the Cloudflare Worker | One web origin and deployment | Worker runtime cannot spawn local Python or access the operator repository | Cannot satisfy the local evidence requirement |
| Let the browser read files or run commands | No companion service | Browsers correctly prohibit this; any workaround would be unsafe and non-portable | Violates the platform and security model |
| Package a static JSON snapshot at build time | Simple and deployable | Immediately stale; actions cannot work; risks presenting old data as current | Fails the truthfulness requirement |

## Capacity and failure assumptions

- One trusted repository and one active operator.
- Snapshot traffic below 2 requests/second.
- At most one verification job; a second request receives `409`.
- Git metadata calls time out after 5 seconds.
- Verification times out after 180 seconds and captures at most the last
  32 KiB for the UI.
- A bridge failure affects only the dashboard; CLI and CI authority remain
  unchanged.

## Security sketch

- **Assets:** repository metadata, verification output, local CPU, and the
  authority to execute Doctrine's fixed verifier.
- **Entry points:** HTTP headers, request path, JSON body, and browser origin.
- **Worst plausible abuse:** a malicious webpage repeatedly starts expensive
  local verification or exfiltrates repository metadata.
- **Controls:** loopback binding, exact origin allowlist, clean-tree
  attribution, JSON-only mutation, 1 KiB body cap, one-job lock, fixed
  executable/script arguments, timeouts, output bounds, and no arbitrary
  repository/path/action input in requests.

## Consequences

- Positive: The dashboard becomes truthful and operational without a new
  dependency or privileged browser integration.
- Positive: CLI and CI remain authoritative; the UI is a bounded adapter.
- Negative: Hosted HTTPS pages cannot safely depend on a plain HTTP loopback
  bridge. Remote operation needs a separately authenticated design.
- Negative: Verification history is machine-local scratch, not enterprise
  evidence storage.
- Invalidation triggers: multi-user or remote access, more than one repository,
  remote mutations, signed export, or a requirement to integrate MAPLE/STIX
  runtime events.

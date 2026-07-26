# Implementation Plan - Doctrine Control Room Windows assets

**Brief:** user-reported Control Room loading defect
**Design/ADRs:** [local bridge ADR](../adr/008-doctrine-control-room-local-bridge.md)
**Class:** M

## Acceptance criteria

1. A Windows production preview returns the server-rendered page and every
   referenced CSS and JavaScript asset with `200` and the correct content type.
2. Rendered CSS contains no host filesystem font URL.
3. The loopback API remains exact-origin restricted and returns the current,
   non-partial repository snapshot to the repaired preview.
4. The repair adds no dependency and preserves Linux-hosted browser behavior.

## Slices

| # | Slice | Role | Files touched | Proven by | Status |
|---|---|---|---|---|---|
| 1 | Reproduce shell-200/assets-404 failure and isolate the Windows separator mismatch | Frontend Engineer | runtime probes | six rendered assets returned 404 before repair | done |
| 2 | Add a scoped production-launch compatibility shim and remove host-path font output | Frontend Engineer | launcher, layout, CSS, package scripts | production HTTP regression | done - 5/5 dashboard tests |
| 3 | Document local production startup and occupied-port handling | Tech Writer | dashboard README, changelog | rendered contract and manual command review | done |
| 4 | Run review, security, QA, and hosted browser gates | Reviewer roles | review/QA artifacts | local + hosted gate results | done |

## Risks and rollback

- Risk: temporarily normalizing `path.relative` could affect unrelated server
  initialization. Mitigation: patch only on Windows and restore the native
  function immediately after vinext constructs its production server/cache.
- Risk: removing `next/font` changes typography. Mitigation: use explicit,
  high-quality native UI and monospace stacks with no network or filesystem
  dependency.
- Rollback: restore the vinext `start` script and `next/font` layout imports,
  then remove the production-server regression.

## Loop profile

Ratchet, budget 3:

1. Page `200`, all six assets `404` - root cause identified.
2. Compatibility launcher plus system font stack - assets and suite green.
3. Hosted browser confirmation and any named repair, if required.

## Status snapshot

Complete. Local evidence: page `200`; six of six rendered assets `200`; bridge
snapshot `200`, correct CORS origin, verification passed, zero partial reasons;
lint, types, build, five tests, and audit green. Hosted evidence: Windows and
Ubuntu dashboard gates passed, Chromium passed all seven browser scenarios, and
Doctrine passed on Python 3.11 and 3.12 on both operating systems.

The local interactive browser controller had no available backend. Hosted
Chromium therefore supplies the real-browser automation evidence; no remote
site was deployed for this local Control Room repair.

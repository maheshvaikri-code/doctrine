# Plan — Enterprise Control Plane (v0.7.0)
<!-- G2 artifact. Owner: Chief Architect. Brief: docs/briefs/enterprise-control-plane.md -->

Five work packages. WP1 landed first (it unblocked a trustworthy baseline);
WP2–WP5 touch disjoint files and could run in parallel.

## WP1 — Bridge flake (done first)
- **Files:** `tools/doctrine_dashboard.py`, `tests/test_doctrine_dashboard.py`
- **Cause:** early-rejection paths answered and closed while the request body
  was still in flight; the late body hit a closed socket and the OS replied RST
  (`ConnectionAbortedError` / WinError 10053), destroying the unread response.
- **Fix:** drain the announced body at the single `_send_json` choke point, and
  bound every connection read with `REQUEST_TIMEOUT_SECONDS`. The oversized
  branch explicitly opts out of draining — refusing to read is its purpose.
- **Evidence:** a deterministic reproduction (headers, pause, late body) fails
  10/10 before and passes 10/10 after; it ships as a regression test.

## WP2 — `tools/doctrine_guard.py` (PreToolUse enforcement)
- **Contract:** reads the hook payload as JSON on stdin, writes a JSON decision
  on stdout, exit 0. Unknown/foreign payloads outside a Doctrine repo exit
  silently; unparseable payloads inside one deny.
- **Rules (fail-closed, in order):** secret-shaped content · protected-path
  write (files, and the enforcement surface itself) · destructive command ·
  test weakening. *(This slice originally named verifier-role write isolation
  as the fourth rule. It was never implementable from a payload that carries
  no role — see ADR-012's Correction — and the substitution is recorded here
  rather than quietly swapped.)*
- **Configurable:** `.doctrine-state/guard.json` may extend protected paths and
  allowlist explicit exceptions; absent config = shipped defaults.
- **Tests:** one per rule (deny + reason), plus: ordinary edit allowed,
  non-Doctrine repo silent, malformed payload denied, config extension honored,
  allowlist honored.
- **Wiring:** `plugin/hooks/hooks.json` + `.claude/settings.json` (repo's own),
  installer `TOOL_FILES`, pyproject script.

## WP3 — Gold attestation
- **Files:** `tools/doctrine_gold.py`, `.Doctrine/state-plane/schemas/gold.schema.json`
- Add `verify_tag_signature()` → `{"signed": bool, "signer": str|None,
  "key": str|None}` from `git verify-tag --raw`; record as `attestation`.
- `--require-signature` on `record` refuses an unsigned tag; `check` reports
  attestation and accepts `--require-signature` symmetrically.
- Schema gains an optional `attestation` object — **optional** so existing
  records stay valid (records are immutable; a correction is a new tag).
- **Tests:** unsigned tag records without attestation; unsigned + flag refuses;
  signature verification parses a real `--raw` output shape; check honors the
  flag. (A real signed tag needs a key, so signature *parsing* is tested
  against captured `git` output rather than by generating a key in CI.)

## WP4 — `tools/doctrine_fleet.py`
- **Input:** repo paths as arguments, or `--root <dir>` to scan one level for
  git repos, or `.doctrine-state/fleet.json`.
- **Per repo, read-only:** doctrine version (`.Doctrine.md` header), drift vs
  `--source` (corpus byte-compare of the law + README carriers), state-plane
  posture, worktree clean/dirty, latest tag + gold record.
- **Output:** aligned text table (ASCII only — Windows cp1252) and `--json`.
- **Exit:** 0 clean, 1 when any repo drifts from source (a CI-usable signal).
- **Tests:** two temp repos (current + drifted), JSON shape, non-repo skipped,
  never writes to an inspected repo.

## WP5 — CI parity
- `.Doctrine/templates/ci/gitlab-ci.yml`, `.Doctrine/templates/ci/azure-pipelines.yml`
  at parity with `.github/workflows/doctrine.yml` (lint → ruff → suite).
- Installer `--ci` gains `--ci-provider github|gitlab|azure`.

## Cross-cutting
- Version → 0.7.0 across all lint-enforced carriers (`.Doctrine.md`, CHANGELOG,
  pyproject, `doctrine_mcp.py`, plugin.json, README badge).
- Routing table entries so the new tools are discoverable; `05-packaging.md`
  manifest updated; `doctrine_signature.py --write` re-run if role/skill files
  change.
- Gate artifacts: review `docs/reviews/`, QA `docs/qa/`, retro `docs/retro/`.

## Risks
- **Guard false denials** block real work. Mitigation: narrow, high-precision
  patterns; an allowlist; every denial names the rule and how to proceed.
- **Guard self-lock** — the guard could block edits to itself. Mitigation:
  protected paths cover the corpus and secrets, not the tools directory.
- **Schema change breaking old records.** Mitigation: `attestation` optional,
  and a test asserts an old-shape record still validates.

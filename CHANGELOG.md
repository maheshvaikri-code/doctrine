# Changelog

All notable changes to the Doctrine System are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [SemVer](https://semver.org/) (0.x — doctrine under active development).

## [Unreleased]

## [0.4.0] - 2026-07-12

### Added
- **Enterprise merge & promotion profile** (OPT-IN via
  `Merge profile: enterprise` in the brief; defaults unchanged
  otherwise): `standards/merge-and-promotion.md` — Merge Council with
  unanimity quorum for release-bound merges, a permission matrix
  (role → merge/tag/promote/deploy rights → enforcement mechanism), and
  the Gold Build ladder (candidate → soak → GOLD; deploy only from a
  gold record; **the hash chain is the rollback ladder**).
- `templates/merge-verdict.md` (council verdict record, filed at
  `docs/merges/`), `schemas/gold-build.schema.json` (content-pinned
  `hashedref`s, `prev_gold_sha256` chain), and `tools/doctrine_gold.py`
  (`record`: refuses without verdict + sign-offs + human approval, all
  content-pinned; `check`: the deploy gate — schema, re-hash, chain
  topology, tag→commit binding).
- Doctrine amendment (this round's lesson): `skills/backend.md` —
  content-hash references; existence is not evidence, mtime is not an
  authority signal.

### Security
- Delta review round-trip #3: security VETO reproduced chain forking
  via mtime forgery and "no verdict, no gold" satisfied by zero-byte
  files. Closed: chain order derives ONLY from prev-hash links (single
  genesis, no forks, full reachability — a broken ladder blocks ALL
  deploys); verdict and sign-offs content-pinned and re-hashed at the
  deploy gate; annotated-tags-only; tag format validated before git
  argv; hardened relpath schema. Re-verified by original exploits:
  APPROVE + SIGN-OFF. Suite: 70 tests.

## [0.3.0] - 2026-07-12

### Added
- **Sessions are now stateful by default.** `hydrate --if-present` (quiet
  no-op on an empty plane, for hooks) and `hydrate --emit-agents`
  (deterministic marker-managed state block in root AGENTS.md — any
  AGENTS.md-reading tool becomes stateful with zero integration).
  Claude Code wiring shipped: `.claude/settings.json` SessionStart hook,
  `CLAUDE.md` bundle import, `/checkpoint` slash command wrapping the
  propose→dispose protocol. A Stop-hook auto-checkpoint is deliberately
  absent: distillates are model-authored; a mechanical hook cannot write
  an honest one.
- `04-agent-adapters.md` State-plane wiring section; HYDRATION.md CLI
  section marked implemented.
- New standing-audit item 7 in `skills/security.md`: agent-context
  emission is an injection surface (second finding of that class this
  release cycle — the closed loop promoted it to law).

### Security
- Delta review round-trip on the emit path: the security VETO reproduced
  a managed-block breakout (marker tokens in model-authored state text
  escaping into committed AGENTS.md on re-emit, self-propagating).
  Closed with defense in depth: MARKER_RES rejection at checkpoint
  time, HTML-comment-token refusal at emit time (covers intent files
  written by other tools), strict one-ordered-pair marker integrity,
  byte-exact preservation outside the markers. Both verifiers re-ran the
  original probes: APPROVE + SIGN-OFF. Suite: 49 tests.

## [0.2.1] - 2026-07-12

### Added
- **G7 retrospective filed** (`docs/retro/2026-07-12-state-tooling.md`)
  by the Project Reviewer: 5-whys on the two deepest escaped defects,
  honest-negatives section, eight doctrine amendments — all applied:
  transactional append-only artifacts (backend), failure-path tests
  assert absence of side effects + valid×invalid cross-products
  (testing), own-state identifiers are a path trust boundary (security),
  required Threat sketch for Class L plans (template), ASCII-safe
  terminal output (python profile), OS-constraint ⇒ CI matrix leg
  (cicd), case-insensitively unique top-level dirs (repo-devops),
  "fixed" requires the re-executed original probe (dos-and-donts §7).
- `integrations/floci.md` — **floci verified real** (floci.io,
  github.com/floci-io, MIT): the cloud skills' emulator dependency
  resolves; documented fallbacks (LocalStack — auth-gated since 2026-03,
  Azurite, gcloud emulators).

### Changed
- CI: actions pinned to full commit SHAs (H-2 condition closed);
  `windows-latest` matrix leg added — the cp1252 output class is now
  covered by environment, not only by unit test.

## [0.2.0] - 2026-07-12

### Added
- **The doctrine is now mechanically enforced.** `tools/doctrine_state.py`:
  stdlib-only reference implementation of the state plane — init /
  checkpoint (propose→dispose, hash-chained, secret-scanned) / verify
  (chain + state_index re-hash incl. graph) / hydrate (budgeted bundle
  with per-section degrade-to forms, refuses unverified chains) / prune
  (dead_ends merge forward) / status. `tools/doctrine_lint.py`: 8-check
  corpus CI gate (references, formats, counts, version sync, canonical
  examples) — on its first run it caught real drift in the corpus.
  38 unit tests; Makefile (`make verify`) + GitHub Actions
  (least-privilege, ruff + corpus lint + suite).
- **First full dogfood of the doctrine's own process**: brief (G0), plan
  (G2), build (G3), then the G4/G5 verifier fan-out with its own
  subagents. Round 1: code review REQUEST-CHANGES (1 blocker, 7 major),
  security VETO (reproduced path traversal), QA FAIL (state-corrupting
  ordering bug). All findings remediated with regression tests; round 2:
  APPROVE-WITH-NITS + security SIGN-OFF + QA PASS. Artifacts under
  `docs/reviews/` and `docs/qa/`.

### Changed
- **State-plane spec 0.2.0**: state root renamed `.doctrine/state/` →
  `.doctrine-state/` (case-insensitive filesystems merge `.doctrine/`
  into `.Doctrine/`, landing runtime state inside the corpus — found by
  QA); checkpoint schema gains `$defs/intent_id` (path-traversal defense
  on `active_intents` and `state_index.intents` keys); examples
  re-serialized to canonical bytes (they violated their own no-trailing-
  whitespace rule).

### Security
- Round-1 veto findings all closed and re-verified by the original
  exploits: intent-id traversal (3 layers), CI token scope, unverified-
  chain hydration, unbounded JSON, stray-file crash, secret-like state
  content (fail-closed scan), git subprocess hardening. Actions
  SHA-pinning deferred with recorded rationale.

## [0.1.6] - 2026-07-12

### Added
- **Language profiles** (`standards/languages/`): Rust, Python, TypeScript
  (extracted from the old coding-standards sections and expanded with
  Testing/Dependencies), plus first-class Go, JVM (Java 21+/Kotlin), and
  .NET (C# 12+) profiles — the doctrine is no longer a Rust/Python/TS-only
  shop.
- **Five new adapters**: Cline (`.clinerules/`), Roo Code (`.roo/rules/`),
  Amazon Q (`.amazonq/rules/`), Continue (`.continue/rules/`), JetBrains
  Junie (`.junie/guidelines.md`); install map updated in
  `04-agent-adapters.md`.
- **Monorepo section** in `skills/repo-devops.md`: native workspaces,
  path-filtered CI, CODEOWNERS, nested AGENTS.md pointers.

### Changed
- `standards/coding-standards.md` rewritten as a language-neutral core +
  profile routing table; unprofiled languages get General rules + the
  ecosystem's canonical toolchain, with new profiles proposed via G7.

## [0.1.5] - 2026-07-12

### Added
- **Ten new skill playbooks** closing the enterprise-coverage gaps:
  `privacy-compliance`, `incident-response`, `resilience`, `concurrency`,
  `ml-engineering`, `data-engineering`, `iac`, `mobile`, `i18n`,
  `accessibility` — all in the house format (Principles/Defaults/Do/
  Don't/checklist/failure modes), 45–70 lines each.
- **Four new roles**: SRE (SLOs/error budgets; wears Incident Commander on
  HOTFIX, may freeze releases on budget burn), Data Engineer, ML Engineer
  (no prompt/model change without eval evidence), Compliance Officer
  (fresh-context verifier; can block ship pending human legal review).
- **Four new subagents** in `.claude/agents/` (sre, data-engineer,
  ml-engineer workers; compliance-officer verifier) — now 14 total:
  8 workers + 6 verifiers.

### Changed
- Routing table: eleven new rows (privacy, incidents, resilience,
  concurrency, ML, data, IaC, mobile, i18n, a11y).
- G5 gains conditional Compliance participation; HOTFIX names the SRE as
  Incident Commander; role counts updated everywhere (19 roles, 30 skills).

## [0.1.4] - 2026-07-12

### Changed
- The five previously orphaned skills (no role Loaded them) now have
  owners: `backend-engineer` loads `observability.md` and `performance.md`
  conditionally; `devops-engineer` loads `cloud-<provider>.md` per the
  brief's recorded `Cloud target` and its Activates-when now names cloud
  deploy/IaC work.

## [0.1.3] - 2026-07-12

### Added
- **FDE integrated as a first-class role**: `roles/fde.md` (frontmatter
  normalized to the role-card convention), skills
  `floci-{provision,seed,parity,promote}.md` under `skills/`, plus
  `rubrics/discovery.rubric.md`, `schemas/parity-ledger.schema.json`,
  `examples/floci.manifest.yaml`. Role index and routing table now route
  customer prototype/demo/PoC asks to it.
- **ponytail + graphify shims integrated**: `skills/ponytail.md` (brevity
  ladder, added to the "Any code at all" routing row) and
  `skills/graphify.md` (graph-before-grep, new structure-questions routing
  row); human-facing setup docs under `integrations/`.
- **State plane wired in**: routing row for session start/end/handoff;
  `01-workflow.md` session discipline references checkpoint + hydration.
- `integrations/` index with per-pack overview docs (fde, ponytail,
  graphify); AGENTS.md compression regenerated per the `04` sync rule.

### Changed
- Role count 14 → 15, skill count 14 → 20 (README layout and
  `02-role-protocol.md` updated); FDE added to the roles that stay in the
  main thread (`03-parallel-execution.md §5`) — its P1/P6 gates are
  human-interactive.
- Former pack folders `.Doctrine/FDE/` and `.Doctrine/graphify_PonyTail/`
  dissolved into the standard tree (all moves history-preserving renames).

## [0.1.2] - 2026-07-12

### Added
- `.Doctrine/state-plane/` — the doctrine-state-plane pack (checkpoint
  protocol, distillate schema, hydration compiler spec) extracted into the
  tree; it previously existed only as two redundant zips at the repo root.

### Removed
- All packaging debris from the raw pack drops, every removed copy verified
  byte-identical to the kept canonical first (originals reachable at
  `v0.1.0`): four root-level export zips, inner pack zips, flattened
  top-level duplicates in `FDE/` and `graphify_PonyTail/`, partial
  `mnt/user-data/outputs/` export copies, and the literal
  `{brace-expansion}` scaffold directories.
- Canonical single copies now: `.Doctrine/FDE/fde-floci-pack/`,
  `.Doctrine/graphify_PonyTail/doctrine-integrations/`,
  `.Doctrine/state-plane/`.

## [0.1.1] - 2026-07-12

### Fixed
- `.Doctrine/README.md` skill-playbook count corrected (ten → fourteen).
- G4/G5 gate-labeling conflict resolved: `code-reviewer` subagent description
  now names the G4/G5 review fan-out (per `03-parallel-execution.md §4`)
  instead of implying security-reviewer and qa-engineer run at G4.
- `.Doctrine.md §8` artifact tree: retrospective filename aligned with the
  template (`retro/<date>-<slug>.md`); release-checklist filing path added
  (`docs/releases/vX.Y.Z.md`) and mirrored in the template header.
- `01-workflow.md` G1 exit clarified: the ADR set *is* the design document
  (no separate design-doc template exists by design).
- Severity labels in `templates/code-review-report.md` aligned to the
  bracketed form used by the role card and workflow (`[BLOCKER]` …).

### Removed
- Duplicate `.Doctrine/agents/` folder (byte-identical copy of
  `.claude/agents/`). Canonical location is `.claude/agents/`, as stated in
  `.Doctrine.md §11` and the README layout.

### Added
- `CLAUDE.md` bootstrap shipping the `@.Doctrine.md` import that `§11` and
  `adapters/AGENTS.md` instruct users to create.
- `CHANGELOG.md` (this file), `.gitignore`, `.gitattributes` (LF-canonical,
  matching the pack-wide canonicalization rules).
- Doctrine version of record now tracked in the `.Doctrine.md` header.

## [0.1.0] - 2026-07-12

### Added
- Baseline import of the Doctrine System as received: root operating system
  (`.Doctrine.md`), 14 role cards, 14 skill playbooks, 6 standards,
  7 templates, gated workflow G0–G7, role protocol, parallel-execution
  protocol, multi-agent adapters (AGENTS.md + overlays), 10 Claude Code
  subagents, and un-integrated add-on packs (FDE/floci, graphify+ponytail,
  doctrine-state-plane zips) preserved for history.

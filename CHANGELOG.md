# Changelog

All notable changes to the Doctrine System are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [SemVer](https://semver.org/) (0.x — doctrine under active development).

## [Unreleased]

## [0.6.9] - 2026-07-13

### Added
- **Governance layer (GRC)** — four heads above the gates, policy
  separated from enforcement (`standards/governance.md`): **Head of
  AI** (model/vendor policy, eval standard, responsible-AI boundary,
  model inventory), **Head of Data** (data contracts, lineage,
  retention map, one-definition-per-entity), **CISO** (security
  posture, threat-model registry, exception register — every accepted
  risk carries the human's signature AND an expiry; the
  security-reviewer keeps the G5 ship veto), **Risk Officer**
  (enterprise risk register, `templates/risk-register.md` →
  `docs/risk/register.md`, deltas reviewed at every G7; "a risk nobody
  re-reviews is a surprise on a schedule"). G1 gains the governance
  co-sign (mandatory on enterprise-profile repos). Deliberate
  non-role, recorded in the standard: hands-on "cybersecurity" stays
  with engineers + the security-reviewer — three hats, no fourth.
- **Core delivery craft completed** (user-spotted gap): new
  `skills/architecture.md` (the G1 craft: boundaries where change
  happens together; an ADR with one option is a memo; failure modes
  before happy path) and `skills/requirements.md` (the G0 craft:
  problems not solutions; ACs are executable sentences; QA's
  adversarial classes start at intake). Wired into chief-architect and
  product-owner Loads.
- Counts: 30 roles, 40 skills, 8 standards, 9 templates.

## [0.6.8] - 2026-07-13

### Added
- **Startup craft skills** — the discipline layer under the v0.6.7
  founder-ops roles, house format, seven playbooks: `marketing`
  (positioning is one sentence; a launch is a release, apology draft
  pre-written), `content` (write from the CHANGELOG outward; every
  claim carries a claims-table row for pre-send review), `sales`
  (FDE-scripted demos rehearsed to hash-stable; verbatim CRM notes;
  lost-deal truth feeds G0), `customer-support` (severity = user
  impact; reproduce before routing), `finance` (runway from measured
  burn, never hope-math; measured|estimated|projected labels survive
  quotation), `legal-basics` (obligations register; policy must match
  the actual data map; never practices law), `fundraising` (KPIs
  defined once and stable; lowlights as prominent as highlights).
  Role Loads wired; skill count 31 → 38.

## [0.6.7] - 2026-07-13

### Added
- **Startup profile** (OPT-IN via `Company profile: startup` in the
  brief; installer `--startup` seeds it): seven founder-ops roles —
  Growth Marketer, Content Marketer (claims trace to shipped tags),
  Sales/GTM (demos via the FDE; pricing is a human decision), Support
  Engineer (the user→gates bridge: a reproduced bug becomes a G0 brief
  or HOTFIX), Finance Ops (models, never moves money), Legal Ops
  (drafts, never practices law), Investor Relations (real metrics with
  fidelity labels; "good news and bad in the same font size"). Two iron
  laws on every card: **draft-never-send** (all external actions are
  the human's, §5) and the **honesty law beyond code** (no invented
  testimonials/figures; estimates labeled). All main-thread roles.
  Role count 19 → 26; routing table +7 rows; tests 110 → 111.

## [0.6.6] - 2026-07-13

### Added
- `tools/doctrine_verify.py` — the one-command gate suite,
  cross-platform (stock Windows has no `make`; a Windows-first consumer
  hit exactly that). Runs lint → ruff (skipped with a note when not
  installed) → tests → state-chain verify (skipped before `state
  init`); `make verify` now delegates to it. Verified live: 4 gates
  green through the single command. Plugin /doctrine-verify and
  installer next-steps updated.

### Fixed
- **Escaped packaging defect**: `doctrine_metrics.py` (added v0.6.1)
  was never in the installer's `TOOL_FILES`, so consumer repos lacked
  it while their copied SessionStart hook referenced it unguarded —
  every session in an installed repo opened with a hook error. Now
  shipped, with a regression test asserting every `tools/doctrine_*.py`
  is in `TOOL_FILES` (the class, not the instance). Existing installs:
  re-run the installer. Tests 109 → 110.

## [0.6.5] - 2026-07-13

### Changed
- **History rewritten** (operator decision): `Co-Authored-By` trailers
  stripped from all 44 commits via git-filter-repo; all 17 tags
  rewritten in place. Requires `git push --force --all && git push
  --force --tags`; stale clones must be re-cloned. Pre-rewrite history
  preserved in a local bundle.
- **Provenance migrated from trailers to the enrichment overlay**:
  `doctrine_metrics enrich --mark-authorship agent_assisted` asserts
  authorship for every HEAD-reachable commit (a blanket operator claim,
  documented as such). Verified live: CodeMonk again reports
  44 agent / 0 human without any trailer. Commit shas quoted in the
  audit trail (reviews/QA/retro) re-mapped to the rewritten history via
  the filter-repo commit-map (strict 40-hex parsing, word-boundary
  replacement); state-plane `at_commit` anchors are content-hash-chained
  and stay untouched — pre-rewrite anchors are historical.
- Post-rewrite metrics snapshot filed; enrichment message now reports
  entries vs reviewed separately. Tests 107 → 109.

## [0.6.4] - 2026-07-13

### Added
- **Token-capture wiring documented exactly** (closes the last unfed
  metric family, TCR / cost-per-landed-change): capture is a
  session-launch choice — OTel env must exist before the agent starts,
  no hook can enable it retroactively. Two wirings in
  `integrations/codemonk.md`: `codemonk wrap --otel -- claude`
  (endpoint spawned, env pre-wired) or a standing `codemonk collect`
  on 127.0.0.1:4318 with the four env exports (extracted from CodeMonk
  0.10.0 source, verified live). Events land in `codemonk_tokens.jsonl`
  (gitignored); report via `codemonk tokens --log`.
- `doctrine_metrics capture-hint` — a SessionStart hint (never a gate,
  always exit 0) fires only when a metrics-adopted repo runs
  uncaptured; wired into `.claude/settings.json` and the plugin hooks.
  3 new tests (107 total).

## [0.6.3] - 2026-07-13

### Added
- **Gate instrumentation** — `doctrine_metrics.py gates` mines the
  process's own story from what the pipeline already files: per-release
  cycle time, commit/fix volume, and review-verdict events (counted only
  on added artifact lines that NAME a verdict, so prose "veto" and
  pasted `CHECK FAILED` output cannot inflate the numbers; adverse =
  REQUEST-CHANGES/VETO/FAIL). First real report committed at
  `docs/metrics/gates-2026-07-13.md`: 14 release windows, 36 commits,
  7 fix commits, 4 adverse verdicts — the five review rounds are now
  visible as data. A zero-adverse release with material change is
  flagged for retro scrutiny, mirroring the HITL/CESR erosion gate.

### Fixed
- **Escaped defect from v0.6.2** (found by flaky-test triage, fixed
  fail-closed): after a shared-distillate merge, the loser's orphaned
  original distillate stayed at the forked seq, leaving
  `_distillate_files[-1]` ambiguous by hash order — verify desynced on
  roughly half of hash draws. Merge now archives every same-seq
  distillate no survivor references. Suite deterministic across three
  consecutive full runs (104 tests).

## [0.6.2] - 2026-07-12

### Added
- **State-plane concurrency** (spec 0.3.0) — closes audit gap #1, the
  linear-chain assumption. Same worktree: an advisory session lease
  (`local/lease.json`, TTL 1h, gitignored) guards chain append;
  `checkpoint --steal` takes over loudly. Across clones: `verify`
  reports `CHAIN FORKED` naming both heads (hydrate refuses — a fork is
  a loud full stop); `merge --loser` archives the losing head +
  distillate under `forks/` (history never deleted), repoints to the
  winning head, salvages the loser's dead_ends into the next
  checkpoint's pending file (scanned at merge time — a poisoned loser
  cannot soft-lock the plane), prints learned/open_threads for honest
  re-proposal, and runs a MANDATORY post-merge verify. Leaf-only;
  descendants refuse with iterate-from-the-leaf guidance.

### Fixed (review round #5: APPROVE-WITH-NITS + security SIGN-OFF)
- All findings landed: merge StateErrors cleanly on malformed losers
  (SC-1), lease parse hardened via load_json (LE-1), post-merge verify
  mandatory (MG-1), shared distillates never archived (MG-2), salvage
  scanned at merge (SV-1), plan wording corrected (SC-2), empty salvage
  and stray-directory messages honest (SC-3/SC-5), prune comment
  accurate (SC-4). Tests 92 → 96 incl. a genuine two-clone fork
  simulation and three-way-fork coverage by the reviewer's probes.

## [0.6.1] - 2026-07-12

### Added
- `tools/doctrine_metrics.py enrich` — bridges the doctrine's review
  artifacts to CodeMonk: scans `docs/reviews|qa|merges` for commit
  references, verifies each against the repo (hex-validated before git
  argv, ancestor-of-HEAD only), and emits the enrichment overlay.
  **Verified end-to-end on this repo: HITL 0% → 27.3%** — the nine
  review-round commits now count as reviewed, with the fidelity label
  stated in the output (verifier fan-out, human-arbitrated). Enriched
  snapshot filed alongside the baseline; wired into pyproject
  (`doctrine-metrics`); 4 new tests (86 total).

## [0.6.0] - 2026-07-12

### Added
- **The Doctrine measures itself** — closes self-measurement, gap #2 of
  the fully-equipped-EOS audit. New `skills/metrics.md` (measure the
  process; HITL reduction only counts while CESR holds; metrics are G7
  inputs, never weapons; the honesty law applies to numbers) and
  `integrations/codemonk.md` — **CodeMonk 0.10.0** pinned as the
  metrology subsystem (CESR, agent engagement, HITL gated on CESR,
  token churn, cost per landed change; golden-vector metric spec, zero
  runtime deps). Verified by execution on this repo: 31 agent changes
  detected via commit trailers, CESR 100% (zero reverts — accurate);
  baseline filed at `docs/metrics/2026-07-12-baseline.md` with fidelity
  notes (git-only HITL reads 0 until review enrichment is wired).
- Routing row for process measurement; G7 attaches the scorecard where
  metrics are adopted; Project Reviewer conditionally loads the skill.
- `supportfolder/` gitignored (drop zone; upstream is pinned, never
  vendored — per the integrations rule).

## [0.5.0] - 2026-07-12

### Added
- **Packaged distribution** (`.Doctrine/05-packaging.md`):
  `tools/doctrine_install.py` installs the law + enforcement suite into
  any repo (idempotent, append-never-replace, never clobbers without
  `--force`, per-tool adapters, `--enterprise`/`--ci`);
  `tools/doctrine_mcp.py` — stdlib stdio MCP server exposing
  lint/state/gold tools to Claude Code, Codex, Cursor, Windsurf,
  Copilot, Gemini and any MCP-capable agent; **Claude Code plugin**
  (`/plugin marketplace add` → `/plugin install doctrine`) with
  /doctrine-init, /doctrine-verify, /gold-check, /checkpoint, 14
  subagents, guarded SessionStart hook, bundled MCP config — plugin
  wiring is byte-parity with `.claude/`, enforced by new lint checks;
  `pyproject.toml` builds the `doctrineos` wheel (publish human-gated).
- LICENSE (MIT). Version-sync lint: plugin manifest, pyproject, and MCP
  serverInfo must match the `.Doctrine.md` header.

### Fixed (review round #4: security SIGN-OFF; code REQUEST-CHANGES → fixed)
- Consumer repos now verify clean out of the box: lint skips
  source-repo-only checks (plugin parity, CHANGELOG sync) where those
  files don't exist, survives missing files as findings not crashes.
- MCP server no longer dies on malformed input: non-object lines/params/
  arguments and unknown/missing tool args are JSON-RPC errors; raw-line
  RecursionError caught; 5 MB line bound; serve-loop catch-all.
- Installer: refuses nested source/target (self-ingestion), preserves
  CRLF in appended files, never writes through symlinks without --force.

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

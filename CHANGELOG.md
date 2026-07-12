# Changelog

All notable changes to the Doctrine System are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [SemVer](https://semver.org/) (0.x — doctrine under active development).

## [Unreleased]

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

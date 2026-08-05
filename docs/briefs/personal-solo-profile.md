# Project/Task Brief — Personal/solo builder profile and default MAPLE
<!-- G0 artifact. File as docs/brief.md or docs/briefs/<task>.md -->

**Date:** 2026-07-29 · **Class:** L — public installer flags and the
cross-cutting gate model change · **Requested by:** human

## Problem
Doctrine currently assumes a software-company operating model for every
repository. That ceremony is useful for teams and enterprises but burdens a
personal or solo builder with standing architecture, review, governance,
privacy, compliance, and legal roles even when the task has no corresponding
risk. MAPLE is also opt-in even though it is the intended workforce runtime.

## Scope
- In: add equivalent `--personal` and `--solo` installer flags; define a
  personal delivery profile; add a Solo Builder perspective; make MAPLE the
  declared default workforce runtime; give reversible local building a creative
  agent-latitude default while retaining a deterministic DevOps verification
  boundary; update law, workflow, adapters, documentation, and regression
  tests.
- **Non-goals:** automatically install or vendor the free/open-source AGPL
  MAPLE package;
  disable the permanent safety floor; suppress risk-specific privacy,
  compliance, legal, security, or regulated-domain controls when a task
  actually creates those risks; publish a release.
- Deferred: automatic discovery of arbitrary consumer build commands beyond
  the repository's documented/native verification entry points.

## Acceptance criteria (numbered, testable)
1. Given a default installation, `docs/brief.md` declares
   `Workforce runtime: maple` without requiring `--maple`.
2. Given either `--personal` or `--solo`, the installed brief declares
   `Delivery profile: personal`; both flags have identical behavior.
3. Given personal mode, the law routes ordinary work through Solo Builder
   build/self-review and DevOps verification without mandatory G0/G1/G2/G4/G6/
   G7 artifacts or standing governance/compliance/legal roles.
4. Given a task with actual personal-data, regulated, authentication,
   credential, destructive, publishing, paid-service, or other external risk,
   personal mode still activates the matching risk overlay and human
   escalation.
5. Given `--personal` with `--enterprise`, installation fails before mutating
   the target; personal remains compatible with `--startup`.
6. Given legacy `--maple`, installation remains accepted and does not duplicate
   the runtime marker.
7. Source lint, Ruff, installer/profile tests, and the full Doctrine test suite
   run with real evidence.
8. Given a new personal/solo install, the brief declares
   `Agent latitude: creative`; an existing explicit latitude is preserved.
   Governance constrains risky effects rather than ordinary local ideation,
   while tests, evidence, and promotion boundaries remain deterministic.

## Constraints
Python stdlib only; existing installer API remains backward compatible; no
network or package installation; existing uncommitted dashboard packaging fix
and user-owned brand assets remain intact.

## Assumptions (chosen defaults — correct me if wrong)
- “MAPLE enabled for all” means selected in Doctrine's runtime policy and
  recorded in installed briefs; availability still degrades to native
  subagents or serial roles.
- `--solo` is an alias, not a second profile with divergent semantics.
- Personal mode relaxes ceremony, not truthfulness, secrets handling, test
  integrity, or human control over irreversible/external actions.
- Agent latitude is a portable work-policy field, not a promise that every
  provider exposes or that Doctrine changes an LLM temperature parameter.

## Open questions (blocking — answered before G1)
- None.

**Human confirmed:** yes · 2026-07-29

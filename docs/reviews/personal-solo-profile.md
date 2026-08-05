# Code Review — Personal/solo profile and default MAPLE @ main working tree
<!-- G4 artifact. Verdict: PASS (same-session review limitation recorded). -->

**Reviewer role:** Code Reviewer · **Date:** 2026-07-29
**Base commit:** `9006dd5fd33c4ca11e871cf3b4ed3a9f01f54c10`
**Reviewed against:** `docs/briefs/personal-solo-profile.md`,
`docs/adr/011-personal-delivery-and-default-maple.md`, and
`docs/plans/personal-solo-profile.md`
**Executed:** `git diff --check`; targeted reference/stale-wording scans;
packaging and awakening regression suites; `python tools/doctrine_verify.py`;
black-box installer invocations.

## Findings

| # | Sev | Location | Finding | Suggested fix | Resolution |
|---|-----|----------|---------|---------------|------------|
| 1 | [MINOR] | `docs/adr/001-turnkey-distribution.md`, `docs/adr/003-product-family-topology.md`, `docs/plans/productization-v0.1.md` | Historical documents still called MAPLE opt-in without identifying the current superseding decision. | Add dated amendments pointing to ADR-011 while preserving the historical record. | resolved in working tree |
| 2 | [MINOR] | `tools/doctrine_install.py`, `.Doctrine/templates/project-brief.md` | Initial explicit-latitude preservation recognized the installer's plain marker but not the bold metadata form emitted by the project-brief template. A reinstall could append creative beside a templated deterministic choice. | Recognize both canonical plain and template metadata fields; make the regression use the public template form. | resolved in working tree |

No open BLOCKER, MAJOR, MINOR, or NIT findings remain.

## What was checked

- The two CLI spellings share one argparse destination and one canonical
  `Delivery profile: personal` marker.
- Personal installs seed `Agent latitude: creative` exactly once, standard
  installs do not invent it, and a templated explicit deterministic choice is
  preserved.
- Creative latitude is consistently separated from scope, permissions,
  iteration budgets, tests, evidence, risky effects, and promotion. Governance
  fences only the surface that activated it.
- Personal/enterprise conflicts are checked before `target.mkdir` or any copy;
  both flag-to-flag and existing-brief transitions have regression tests.
- Startup remains orthogonal to personal mode.
- MAPLE is always selected exactly once, while the legacy argument remains
  accepted and no package, import, or network mutation was introduced.
- The law, workflow, role protocol, governance standard, adapters, installer,
  templates, public docs, and tests agree on creative Solo Builder →
  deterministic DevOps verification and risk-triggered overlays.
- Root and canonical adapter `AGENTS.md` files are byte-identical; generated
  signatures are current; `git diff --check` is clean.
- The previously present control-room contract packaging edits remain intact.
  User-owned untracked WorkHawk brand assets were not touched.

## Independence limitation

The active tool rule prohibited spawning a fresh verifier and this interface
cannot open a separate chat programmatically. This report is therefore an
explicitly labeled same-session adversarial pass, not an independent
fresh-context review. Objective G5 evidence is recorded separately.

## Verdict

- [x] Pass (0 BLOCKER; 0 open MAJOR)
- [ ] Return to build

The implementation is internally consistent and its specified behaviors are
covered. Independent fresh-context review remains a process limitation, not a
known product defect.

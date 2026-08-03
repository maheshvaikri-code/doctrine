# Implementation Plan — Personal/solo profile and default MAPLE
<!-- G2 artifact. File as docs/plans/<task>.md. Update as reality diverges. -->

**Brief:** `docs/briefs/personal-solo-profile.md` · **Design/ADRs:**
`docs/adr/011-personal-delivery-and-default-maple.md` · **Class:** L

## Slices (ordered; each leaves the tree green)
| # | Slice | Role | Files touched | Proven by (tests) | Status |
|---|-------|------|---------------|-------------------|--------|
| 1 | Add failing profile/runtime installer tests | QA Engineer | `tests/test_doctrine_packaging.py` | initial packaging run failed on 6 missing behaviors; regression set now green | done+evidence |
| 2 | Implement aliases, conflicts, and default MAPLE marker | DevOps Engineer | `tools/doctrine_install.py` | packaging suite 29/29, including both existing-profile conflict directions | done+evidence |
| 3 | Define personal workflow, Solo Builder role, risk overlays, and MAPLE default | Chief Architect | `.Doctrine.md`, workflow/governance/integration/role/boot files | corpus lint clean; signatures generated/current; boot files byte-identical | done+evidence |
| 4 | Update public documentation and changelog | Tech Writer | README, QUICKSTART, packaging/tooling/templates, CHANGELOG | stale-current-wording scan clean | done+evidence |
| 5 | Review and verification | Code Reviewer / QA / Security | diff + test suite + reports | full source verify 4/4 gates; 194 tests; CLI probes; reports filed | done+evidence |
| 6 | Add creative-build / deterministic-boundary semantics requested in follow-up | Solo Builder / DevOps Engineer | installer, personal law/workflow/role/governance/engagement docs, tests, public docs | packaging 30/30; activation 7/7; source verify 4/4 with 195 tests; black-box CLI markers | done+evidence |

## Threat sketch (required for Class L)
Assets touched: installer target filesystem, consumer brief, governance
routing. Entry points / untrusted inputs: CLI flag combinations and pre-existing
brief content. Worst plausible abuse: personal mode is interpreted as permission
to expose private data, waive security, publish, or report unexecuted tests.

## Risks & rollback points
- Risk: aliases diverge → one argparse destination and one canonical marker →
  rollback: remove both flags and marker together.
- Risk: profile silently combines with enterprise → pre-mutation conflict check
  against flags and existing brief → rollback: reject personal installs.
- Risk: default MAPLE is mistaken for an installed dependency → explicit
  documentation and fallback contract → rollback: restore opt-in marker.
- Risk: personal mode weakens the invariant floor → repeated law/boot wording
  and regression review → rollback: remove the personal exception.
- Risk: “creative” is mistaken for broader permissions or nondeterministic
  evidence → split latitude from action authority and verification explicitly
  at every personal-profile entry point → rollback: remove the marker while
  retaining the Solo Builder path.

## Deviation log (append-only, as they happen)
- 2026-07-29: Graphify output and CLI were unavailable; impact mapping used
  targeted repository references and is recorded as a degraded local fallback.
- 2026-07-29: Follow-up clarified that solo agents need creative latitude
  during reversible work; added slice 6 rather than treating deterministic
  verification as deterministic creation.

## Status snapshot (update at session end / handoff)
Done (with evidence): all six slices; source verify 4/4 gates and 195 tests
green; black-box CLI probes green · Next: commit only if requested · Blocked
on: independent fresh-context G4/G5 is unavailable under the active
no-delegation tool rule, so review is explicitly labeled same-session.

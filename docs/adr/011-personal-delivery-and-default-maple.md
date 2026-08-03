# ADR-011: Personal delivery profile and default MAPLE selection
<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-07-29 · **Status:** accepted
**Deciders:** Chief Architect + human
**Supersedes in part:** ADR-001 and ADR-003 (MAPLE opt-in semantics only)

## Context
Doctrine's class-based pipeline still models a complete organization for
personal repositories. The installer separately treats MAPLE as opt-in even
though MAPLE is Doctrine's intended workforce transport. The change must reduce
solo-builder ceremony without creating a flag that silently waives evidence,
security boundaries, or human authority.

## Decision
We will add one canonical `Delivery profile: personal`, exposed through
equivalent `--personal` and `--solo` installer flags. Its normal path is Solo
Builder G3 build/self-review followed by a DevOps verification gate; other
organizational gates and artifacts are advisory unless the work's actual risk
surface activates them. Personal and enterprise are mutually exclusive, while
startup is orthogonal. Every installation will declare
`Workforce runtime: maple`; legacy `--maple` remains a compatibility no-op.
Doctrine will not install, vendor, or import MAPLE, and falls back to native
subagents or serial roles when the external runtime is unavailable.

Personal mode also separates **creative build latitude** from **deterministic
boundaries**. A new personal brief declares `Agent latitude: creative` unless
the user already selected `creative`, `balanced`, or `deterministic`. Creative
latitude governs reversible local exploration—candidate generation, spikes,
comparison, and implementation choices within scope. It does not enlarge
permissions. Tests, evidence, secrets handling, external effects, and
promotion remain deterministic/fail-closed. Risk overlays fence the risky
surface; they do not silently lower the whole builder's latitude. This is a
portable policy marker, not a provider-specific sampling-temperature setting.

## Alternatives considered
| Option | Pros | Cons | Why not |
|--------|------|------|---------|
| One personal profile with two CLI aliases (chosen) | One semantic contract; builder-friendly vocabulary; no drift | Adds a conditional path to the law | — |
| Separate personal and solo profiles | Could tune each independently | Ambiguous distinction; inevitable policy drift | The requested perspectives have the same gate intent |
| Installer flag only | Small code change | Writes inert text; agents still run full gates | Does not change behavior |
| Disable all gates in personal mode | Maximum speed | Fabricated success, leaked secrets, broken releases, and irreversible actions become easy | Violates the permanent safety floor |
| Auto-install `maple-oss` in every target | Runtime immediately present; MAPLE remains free/open-source | Hidden network/environment mutation and a consumer-controlled dependency lifecycle | Doctrine stays stdlib and runtime-agnostic |
| Make solo work deterministic end-to-end | Highly repeatable editing behavior | Suppresses useful divergence before the solution is known; confuses ideation with verification | Determinism belongs at evidence/effect boundaries |

## Consequences
- Positive: personal repositories get a direct builder loop with one evidence
  boundary; creative local exploration is explicit; MAPLE is consistently
  selected; aliases are easy to discover.
- Negative / debt accepted: risk-trigger routing remains judgment-based, and
  MAPLE selection does not guarantee the external package is available.
  Agent hosts may not expose a literal model-control knob, so compliance is
  behavioral rather than a guaranteed sampling parameter.
- Invalidation triggers: personal users still experience routine organizational
  ceremony; personal mode causes missed risk overlays; MAPLE becomes vendorable
  under a compatible distribution/license decision; or two aliases need
  meaningfully different behavior.

## Governance disposition
The human explicitly selected MAPLE as the default. No AGPL code enters
Doctrine or consumer repositories through this change. CISO/AI policy review:
the permanent safety floor and risk-triggered overlays remain; no standing
enterprise register or co-sign is imposed on risk-free personal work.

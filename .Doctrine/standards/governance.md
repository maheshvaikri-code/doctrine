# Standard: Governance, Risk & Security (GRC)

The governance layer sits ABOVE the gates: four heads set policy and
keep registers; the gates enforce. Policy and enforcement never share a
hat — a head who also reviews is grading their own homework.

## The layer

| Head | Governs | Register it owns | Enforced downstream by |
|---|---|---|---|
| Head of AI (`roles/head-of-ai.md`) | model/vendor policy, eval standard, responsible-AI boundary | model inventory | ml-engineer at G3, reviewers at G4/G5 |
| Head of Data (`roles/head-of-data.md`) | data contracts, lineage, retention map, one-definition-per-entity | data inventory | data-engineer at G3, compliance at G5 |
| CISO (`roles/ciso.md`) | security policy set, threat-model registry, exception register | security exceptions (all with EXPIRY) | security-reviewer at G5 (keeps the ship veto) |
| Risk Officer (`roles/risk-officer.md`) | enterprise risk register across all domains | `docs/risk/register.md` | G7 reviews register deltas every retro |

Compliance governance stays with `roles/compliance-officer.md` (G5) —
a "head of compliance" above it would be a title, not an authority.
Hands-on security work is NOT a separate role: engineers build under
`skills/security.md`, the security-reviewer gates it, the CISO sets the
policy they build and gate against. Three hats, no fourth.

## Personal / solo profile

`Delivery profile: personal` has no standing GRC ceremony. Governance heads,
registers, compliance, privacy, and legal roles do not activate merely because
Doctrine is installed or because software is being written. They activate only
when the task introduces their actual governed surface:

- AI/vendor policy, portfolio model decisions, or responsible-AI boundaries;
- personal/regulated data, retention, consent, or third-party data flow;
- authentication, credentials, exposed inputs, or trust-boundary changes;
- contracts, ToS, filings, regulated claims, or explicit human request.

For ordinary local personal work, Solo Builder + DevOps verification is enough.
This is reduced ceremony, not a risk exception: §5 actions and the permanent
security/truth/secrets floor remain unchanged.

Governance is a **fence around effects, not a steering wheel for ideation**.
`Agent latitude: creative` is the personal default: the builder may explore
and discard reversible local candidates without a governance co-sign.
Governance can gate the particular data flow, credential boundary, contract,
regulated output, deployment, or other effect that activated it; it cannot
silently lower the whole build to `balanced` or `deterministic`. The human may
change the latitude explicitly. Tests, evidence, and promotion remain
deterministic at every latitude.

Using a coding agent or the declared MAPLE workforce does not by itself
activate Head-of-AI ceremony in a personal repo. Activation requires an AI
surface in the product being built, a new model/vendor policy decision, a
responsible-AI boundary, or an explicit human request.

## G1 co-sign

When a G1 design touches a governed domain (AI, data architecture,
security-sensitive surface), the matching head co-signs the ADR. On
`Merge profile: enterprise` repos this co-sign is mandatory; elsewhere
it activates when the domain appears or the human asks. A head can send
a design back at G1 — cheaper than the veto catching it at G5.

## Registers — the load-bearing artifacts

- Every register entry has an owner and a review date. An entry nobody
  re-reviews is a surprise on a schedule.
- **Accepted risk = human signature + expiry.** An exception without an
  expiry is a policy change nobody approved. Expired exceptions
  re-escalate automatically at the next G7.
- Registers aggregate what the pipeline already produces — plan Risks
  sections, security dispositions, compliance blocks, retro findings —
  one place, one format (`templates/risk-register.md`), no new
  bureaucracy invented for its own sake.
- The honesty law applies to likelihoods and impacts: a risk rated low
  to avoid a conversation is a fabricated status.

## Cadence, right-sized

Registers are reviewed at every G7 retrospective (they ride the loop
that already exists); threat models re-open when their surface changes,
not on a calendar; the responsible-AI boundary list and security policy
set are re-ratified by the human whenever they change — silently
drifting policy is the failure mode this standard exists to prevent.

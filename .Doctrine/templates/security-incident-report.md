# Security Incident Report — <INC-YYYY-NNN> <short title>
<!-- G5 artifact for the HOTFIX/security path; its retrospective is G7.
     File as docs/incidents/<INC-id>.md. Owned by the Incident Responder
     (roles/incident-responder.md). Written during the incident, not after.
     Every timestamp UTC. Unknown is a valid answer; invented detail is not. -->

**Status:** open / contained / eradicated / recovered / closed
**Severity:** SEV1 / SEV2 / SEV3 / SEV4 (from the matrix in `skills/security-operations.md`)
**Commander:** <person> · **Opened:** <UTC> · **Closed:** <UTC>
**Comms channel:** <in-band / out-of-band — say which, and why>

## Summary

Three to five sentences: what happened, what was affected, what was done,
current state. Written for someone who will read only this section.

## Confidence

| Claim | Confidence | Basis |
|---|---|---|
| Initial access vector | high/med/low | evidence artifact(s) |
| Blast radius bounded | high/med/low | what was checked, what was not |
| Eradication complete | high/med/low | persistence classes enumerated |

Low confidence stated plainly beats high confidence asserted. A gap in
telemetry is a finding — record it here rather than filling it with narrative.

## Timeline (UTC)

| Time (UTC) | Source | Observed / Inferred | Event |
|---|---|---|---|
| … | artifact or log id | observed | … |
| … | — | **inferred** | … |

Mark every inference. Note telemetry gaps explicitly as rows.

## Scope

- **Systems affected:** …
- **Identities affected:** …
- **Data involved:** … (personal data? → `roles/compliance-officer.md` now, not later)
- **Checked and found clean:** … (what you ruled out, and how)
- **Not checked:** … (honest; this is where the next hunt starts)

## Actions taken

| Time (UTC) | Action | By | Rationale | Reversible? |
|---|---|---|---|---|
| … | contain/eradicate/recover step | … | … | yes/no |

Destructive or business-impacting actions record the human approval that
authorised them (§5).

## Evidence

| Artifact | Acquired from | By | At (UTC) | Method + tool version | Hash | Location |
|---|---|---|---|---|---|---|
| … | … | … | … | … | … | … |

Chain of custody per `skills/digital-forensics.md`. A gap here weakens every
conclusion above.

## Root cause

What allowed it — the control that was missing, misconfigured, or bypassed.
Not "user clicked a link": that is the trigger, not the cause. Blameless on
people, unsparing on controls.

## Persistence enumerated

- [ ] Accounts / credentials rotated
- [ ] API keys, tokens, OAuth grants revoked
- [ ] Scheduled tasks / cron / services reviewed
- [ ] Mail rules / forwarding / delegation checked
- [ ] Implants, startup items, and backdoors searched for
- [ ] Third-party and federated access reviewed

## Follow-ups

| # | Action | Type (detection/hunt/control/telemetry) | Owner | Due |
|---|---|---|---|---|
| 1 | … | detection → `roles/detection-engineer.md` | … | date |

Every incident owes at least one detection and one hunt hypothesis, or a
written reason why neither is possible.

## Human decisions on record (§5)

| Decision | Decided by | At (UTC) | Notes |
|---|---|---|---|
| Notification / disclosure | <human> | … | … |
| Law enforcement contact | <human> | … | … |
| Destructive containment | <human> | … | … |

Regulatory clocks may start before the investigation ends — record when
legal/compliance were engaged, not just that they were.

## Retrospective (G7 — mandatory)

Filed as `docs/retro/<date>-<slug>.md`. Link it here.

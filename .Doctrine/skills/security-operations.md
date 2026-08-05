# Skill: Security Operations (SOC)

**Scope.** Running a security operations capability against a live estate:
telemetry in, detections firing, alerts triaged, security incidents commanded
to closure, and the loop back into better detections. The **backbone** skill —
`skills/detection-engineering.md` (writing what fires),
`skills/threat-hunting.md` (looking without an alert),
`skills/digital-forensics.md` (proving what happened), and
`skills/threat-intelligence.md` (knowing what to look for) overlay only their
distinct craft.

**Not `skills/incident-response.md`.** That skill owns *production* incidents —
availability, latency, a bad deploy — where the correct instinct is **mitigate
first, diagnose second**, and rollback beats forward-fix. A security incident
inverts part of that: an adversary is *adaptive*, evidence is *perishable*, and
a hasty "just restart it" can destroy the only proof of how they got in and tip
them off to move. Both are real; do not run one with the other's reflexes.

## Principles

- **Detection without triage is noise; triage without detection is luck.** A
  SOC is a pipeline, and its throughput is set by its narrowest stage — usually
  analyst attention, not tooling.
- **Every alert ends in a recorded disposition.** True positive, false
  positive, benign true positive, or escalation. An alert that is silently
  ignored trains the next analyst to ignore its whole class.
- **Alert fatigue is a security failure, not an analyst failure.** If the
  false-positive rate makes the queue unworkable, the *detection* is the
  defect. Tune or retire it (`skills/detection-engineering.md`) — never
  normalise "we ignore those."
- **Evidence before eradication.** Capture volatile state (memory, network
  connections, running processes) *before* you kill or reimage, unless active
  harm makes waiting worse. Once it's gone, no amount of later diligence
  recovers it.
- **Assume the adversary reads your response.** They may hold other access, or
  be watching the very channel you are coordinating in. Move to out-of-band
  comms the moment compromise of the primary channel is plausible.
- **Time is the metric that matters.** Dwell time — intrusion to detection — is
  the number that separates an event from a breach.

## The pipeline

```
telemetry → detection → alert → TRIAGE ──┬─ false positive → tune the rule
                                          ├─ benign true positive → document
                                          └─ true positive → INCIDENT
                                                 ↓
                        contain → eradicate → recover → post-incident review
                                                 ↓
                                        new/updated detections
```

The loop back to detections is what makes it a *capability* rather than a
queue. An incident that produces no detection change has taught the
organization nothing mechanical.

## Triage — the analyst's decision

Every alert gets four questions, in order, and stops at the first "no":

1. **Is it real?** (Does the telemetry actually show what the rule claims?)
2. **Is it authorized?** (Change ticket, known admin, scheduled scan — benign
   true positive: the activity happened, and it was legitimate.)
3. **What is the blast radius?** (One host, one identity, one segment — or is
   the scope still unbounded?)
4. **Does it escalate?** (Against a written severity matrix, not a mood.)

Record the answer to each. "Closed — FP" with no reasoning is not a
disposition, it is a shrug that survives in the record as if it were analysis.

## Severity — decide it before you need it

A severity matrix belongs in the runbook, written on a calm day, keyed to
observable facts (data classification touched, privilege level obtained,
number of identities/hosts, internet-facing or internal, active or historical).
Deciding severity during the incident, from the incident, is how politics
enters the response.

## Incident command

The **incident-responder** role (`roles/incident-responder.md`) commands a
security incident, as the SRE commands a reliability one. Single commander,
explicit roles (comms, scribe, forensics, remediation), a written timeline from
the first minute. The scribe is not optional: **the timeline is the deliverable**
that regulators, insurers, and the post-incident review all read.

**Containment before eradication before recovery.** Containment stops the
bleeding (isolate the host, disable the identity, block the C2 domain);
eradication removes the foothold (every foothold — assume more than one);
recovery restores service with the vulnerability actually closed. Skipping to
recovery is how the same intrusion recurs on day four.

## Metrics that mean something

- **MTTD / MTTR** — mean time to detect / respond. Trend, not absolute.
- **Dwell time** — the honest headline number.
- **False-positive rate per detection** — the tuning backlog, ranked.
- **Coverage** — which ATT&CK techniques have a detection *that has fired at
  least once in a test* (see `skills/detection-engineering.md`; untested
  coverage is a spreadsheet, not a capability).
- **Escalation accuracy** — how often a tier-1 escalation was warranted. Both
  directions are informative; only punishing over-escalation produces silence.

## Do

- Write the runbook **before** the incident, and rehearse it (tabletop at
  minimum, purple-team if you can). An unrehearsed runbook is a wish.
- Keep a **shift handoff** ritual: open incidents, watch items, anything
  deliberately deferred. Handoff gaps are where slow-burn intrusions live.
- Preserve chain of custody from the first artifact
  (`skills/digital-forensics.md`) — you rarely know at hour one whether this
  ends in a courtroom or a Jira ticket.
- Feed every true positive back into detection, and every false positive into
  tuning. Close the loop or the queue only grows.
- Practise the comms path (legal, privacy, exec, regulator, customer) as
  deliberately as the technical path. Notification clocks in some regimes start
  at *awareness*, not at conclusion — `skills/privacy-compliance.md`.

## Don't

- Don't reimage the only evidence before capture, absent active harm.
- Don't let an alert class stay noisy indefinitely — tune it or kill it.
- Don't run a security incident on the reliability playbook's instincts
  (mitigate-first, restart, roll back) without asking what that destroys.
- Don't coordinate an active intrusion response in a channel the intruder may
  hold.
- Don't declare "contained" on the first foothold found. Assume persistence
  elsewhere until searched for and refuted.
- Don't attribute publicly (`skills/threat-intelligence.md` — attribution is
  slow, political, and rarely changes what you must do next).

## Review checklist

- [ ] Every alert in the window has a recorded disposition with reasoning
- [ ] Severity assigned against the written matrix, not ad hoc
- [ ] Timeline kept from minute one; scribe named
- [ ] Volatile evidence captured before eradication (or the tradeoff recorded)
- [ ] Containment verified — not assumed — before recovery
- [ ] Post-incident review produced at least one detection or control change
- [ ] Notification obligations checked with compliance/legal, clock documented

## Common failure modes

The queue nobody works because everything is a P3 · "closed — FP" with no
reason, forever · reimaging at hour one and never learning the entry vector ·
declaring victory on the first foothold · coordinating the response in the
compromised Slack · a coverage spreadsheet full of detections that have never
fired once · post-incident reviews that produce apologies instead of
detections.

## Signature

<!-- SIGNATURE:BEGIN (generated by doctrine_signature - do not edit) -->
- **Roles:** `roles/incident-responder.md` · `roles/soc-analyst.md`
- **Skills:** `skills/security-operations.md` (self)
- **Tools:** —
- **Plugins:** the Doctrine plugin (shared)
- **Workflows:** the detect -> triage -> respond loop; escalates into HOTFIX
- **Hooks:** —
- **MCP servers:** —
- **Subagents:** —
<!-- SIGNATURE:END -->

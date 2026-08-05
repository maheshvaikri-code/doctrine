---
argument-hint: <alert | log excerpt | "the suspicious thing">
description: Triage a security alert as the SOC Analyst — disposition with a reason, escalate if real
---

Act as the **SOC Analyst** (`.Doctrine/roles/soc-analyst.md`) working a live queue.
This is not a build gate: wear the hat in-session, announce `[ROLE: SOC Analyst]`,
and load `skills/security-operations.md` (+ `skills/threat-intelligence.md` if the
alert cites an indicator).

**Evidence before action.** If any containment step you are about to take would
destroy state (reboot, reimage, kill process, revoke a session), capture first per
`skills/digital-forensics.md` — order of volatility, memory before disk.

Run the four questions in order; stop at the first "no" and record why:

1. **Is it real?** Does the underlying telemetry show what the rule claims, or did
   the rule misfire? Quote the raw evidence — do not paraphrase it.
2. **Is it authorized?** Change ticket, known admin, scheduled scan. A benign true
   positive is *not* a false positive; conflating them corrupts the tuning backlog.
3. **What is the blast radius?** One host / identity / segment — or still unbounded?
   Unbounded scope escalates rather than gets worked to exhaustion.
4. **Does it escalate?** Against the written severity matrix, not a feeling.

Then close the loop — every alert ends in one of these, with reasoning:

- **False positive** → tuning ticket naming the *specific* benign cause
  (`roles/detection-engineer.md`). Never "closed — FP" with no reason. Never tune
  by excluding an identity, host, or path.
- **Benign true positive** → recorded as such, with the authorization that makes it benign.
- **Confirmed intrusion** → hand to `roles/incident-responder.md`: timeline started,
  evidence preserved, commander named. Switch to out-of-band comms if the corporate
  channel could be compromised.
- **Runbook gap** → write the missing entry now, while the reasoning is fresh.

Containment beyond a pre-approved playbook, anything with business impact, and any
external notification are the human's call (§5).

Alert / evidence to triage: $ARGUMENTS

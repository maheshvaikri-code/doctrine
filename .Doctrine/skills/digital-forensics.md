# Skill: Digital Forensics & Evidence Handling

**Scope.** Acquiring, preserving, and analysing evidence so that the conclusion
survives challenge — by a regulator, an insurer, opposing counsel, or the
engineer who thinks you got it wrong. Invoked from
`skills/security-operations.md` during an incident; the analysis discipline
under `roles/incident-responder.md`.

**Why the ceremony.** Two different jobs wear the same word. *Triage forensics*
answers "what is happening, right now, so we can contain it." *Evidentiary
forensics* answers "what happened, provably, in a form that holds up later."
You rarely know at hour one which one you are doing — so acquire as if it is the
second, and analyse at the speed the first demands.

## Principles

- **Order of volatility.** Capture what disappears first: CPU/registers →
  memory → network state → running processes → disk → logs → archives. Pulling
  the plug to "preserve" a machine destroys everything above disk.
- **Never analyse the original.** Work on a verified copy. The original is
  sealed, hashed, and untouched. If there is exactly one copy and you are
  analysing it, you no longer have evidence — you have a working file.
- **Hash at acquisition, verify at every handoff.** An unhashed image cannot be
  shown to be unaltered later, and "trust me, we didn't change it" is precisely
  what an adversarial reviewer will not accept.
- **Document contemporaneously.** Who, what, when, where, why, with what tool
  and what version. Notes written after the fact are memory, not record — and
  they read that way under scrutiny.
- **The timeline is the deliverable.** Not the tooling, not the malware
  analysis — the ordered, sourced account of what happened when.
- **Say what you do not know.** "Unknown" and "insufficient evidence" are
  findings. A forensic report that fills gaps with plausible narrative is a
  fabrication with a serious face on it (§7 #1).

## Chain of custody

Every artifact carries an unbroken record from acquisition to conclusion:

| Field | Note |
|---|---|
| Identifier | Unique, non-reused |
| Acquired from | Host / account / system, precisely |
| Acquired by | A person, not a team |
| Acquired at | Timestamp **with timezone**, and the source of that clock |
| Method + tool version | Reproducibility depends on it |
| Hash at acquisition | Algorithm named |
| Every transfer | Who to whom, when, hash re-verified |
| Storage | Where, with what access control |

A gap anywhere in that chain is an opening for "this could have been altered,"
and it does not matter whether it was.

## Acquisition

- **Memory before disk**, whenever the host is still running and containment
  allows. Memory holds the injected code, the decrypted payload, the live
  connections, and the keys — almost none of which survive to disk.
- **Isolate rather than power off** where possible: network-isolate the host so
  it stops talking to the adversary while remaining live for capture. Powering
  off is a decision with a permanent cost.
- **Cloud and container estates need a different reflex.** Snapshot the volume,
  export the managed logs, and capture the *control-plane* record (who called
  which API, from where) — often the richest and most durable evidence
  available, and the first thing to age out of retention.
- **Ephemeral by design** (containers, serverless, autoscaling) means the
  artifact may vanish in minutes. Capture is a race; know in advance which
  telemetry is durable and which is not.

## Timeline

Build one ordered account from many sources, and be explicit about clocks:

- Normalise every timestamp to **UTC**, and record the original offset and the
  clock's source. Host clock drift is common and quietly ruins correlation.
- Attribute every entry to its source artifact. An unattributed timeline entry
  cannot be checked.
- Distinguish **observed** (the log says X) from **inferred** (therefore Y).
  Marking inference as observation is the most common way a competent forensic
  narrative becomes wrong.
- Note gaps explicitly — periods with no telemetry are part of the finding,
  and often the most important part.

## Analysis discipline

- Form hypotheses and try to **refute** them (`skills/debugging.md`'s instinct
  applies exactly). Confirmation bias in forensics produces confident, wrong
  attribution.
- Corroborate across independent sources before asserting. One log line is a
  lead; two independent sources agreeing is a finding.
- Keep malware analysis **contained** — a detonation environment that can reach
  production is a second incident waiting to happen.
- Record tool versions and command lines. "We ran the parser" is not
  reproducible; the exact invocation is.

## Do

- Seal and hash before analysing; work on copies only.
- Write notes as you go, timestamped, including dead ends.
- Involve legal/compliance early when the estate holds personal data — notification
  clocks and privilege questions start earlier than most engineers expect
  (`skills/privacy-compliance.md`, `roles/compliance-officer.md`).
- Preserve more than you think you need, within retention and privacy limits.
  Re-acquisition is usually impossible.
- State confidence levels explicitly in the report.

## Don't

- Don't reboot, reimage, or "clean up" before capture unless active harm makes
  waiting worse — and if you must, record that tradeoff as a decision.
- Don't browse the suspect host interactively as an admin; you overwrite
  timestamps and add your own noise to the evidence.
- Don't analyse the only copy.
- Don't present inference as observation, or fill a telemetry gap with a story.
- Don't attribute to a named actor in a report that will be read outside the
  team (`skills/threat-intelligence.md` — attribution is slower, weaker, and
  more consequential than it looks).

## Review checklist

- [ ] Order of volatility respected, or deviation recorded with its reason
- [ ] Every artifact hashed at acquisition; chain of custody unbroken
- [ ] Analysis performed on verified copies; originals sealed
- [ ] Timeline normalised to UTC with clock sources noted
- [ ] Observed vs inferred distinguished throughout; gaps stated
- [ ] Tool names, versions, and invocations recorded
- [ ] Legal/compliance engaged where personal data or notification duties apply

## Common failure modes

Pulling the plug and losing memory · analysing the original · the unhashed image
· timestamps in three timezones silently mis-correlated · inference presented as
fact · an interactive admin session all over the evidence · discovering the
control-plane logs aged out during the investigation · a confident actor
attribution that outruns what the evidence supports.

## Signature

<!-- SIGNATURE:BEGIN (generated by doctrine_signature - do not edit) -->
- **Roles:** `roles/incident-responder.md` · `roles/soc-analyst.md`
- **Skills:** `skills/digital-forensics.md` (self)
- **Tools:** —
- **Plugins:** the Doctrine plugin (shared)
- **Workflows:** acquisition -> chain of custody -> timeline -> report
- **Hooks:** —
- **MCP servers:** —
- **Subagents:** —
<!-- SIGNATURE:END -->

# Skill: Threat Hunting

**Scope.** Proactively searching an estate for adversary activity **that no
alert fired on** — hypothesis-driven, time-boxed, and productive whether or not
it finds anything. Operating context: `skills/security-operations.md`. Findings
become detections (`skills/detection-engineering.md`) or incidents
(`roles/incident-responder.md`).

**The premise.** Detections encode what you already knew to look for. Hunting
exists because that set is always incomplete — the adversary's job is to be
outside it. A SOC that only works its queue can only ever find what it already
knows how to find.

## Principles

- **Hypothesis first, always.** "If an adversary were doing X here, I would
  expect to see Y." Without it you are not hunting, you are browsing logs, and
  browsing has no stopping condition and no reportable result.
- **A hunt that finds nothing is a successful hunt** — *if* it refuted its
  hypothesis with enough coverage to mean something. "We looked and found
  nothing" is only valuable when you can say what you looked at and how well.
- **Time-box it.** A hunt is an experiment, not a vigil. Unbounded hunts
  quietly become someone's whole week with nothing written down.
- **The output is always an artifact.** A detection, an incident, a telemetry
  gap, or a documented refutation. A hunt that ends in a shrug had no method.
- **Hunt where the telemetry is real.** A hypothesis you cannot test because
  the logs don't exist is not a hunt — it is a *gap finding*, which is itself a
  legitimate and valuable result. Record it as one and move on.

## The loop

```
1. HYPOTHESIS   — from intel, from an incident, from an ATT&CK gap, from a hunch
                  about your own architecture's soft spots
2. SCOPE        — which data, which time window, which segment. Written down.
3. HUNT         — query, pivot, stack, cluster. Follow the anomaly, not the fear.
4. TRIAGE       — is the odd thing malicious, benign, or misconfiguration?
                  (Most of it is misconfiguration. That is still a finding.)
5. OUTCOME      — detection | incident | telemetry gap | refutation
6. FEED BACK    — anything found manually that could have been found
                  automatically becomes a detection. Every time.
```

Step 6 is the discipline that compounds. A hunt whose findings never become
detections means the same hunt must be run forever, by hand.

## Where hypotheses come from

- **Threat intel** — a TTP reported against your sector
  (`skills/threat-intelligence.md`).
- **ATT&CK coverage gaps** — the red cells from
  `skills/detection-engineering.md`'s coverage map. The map's honest reds are a
  hunt backlog.
- **Your own architecture** — where would *you* hide, given how this estate is
  actually built? Nobody knows the soft spots better than the people who built
  it.
- **A past incident** — the same adversary, or the same class, elsewhere. "We
  found it on one host" is a hypothesis about the other four thousand.
- **Anomaly of shape, not of signature** — rare parent/child process pairs,
  first-seen binaries, beacon-like periodicity, impossible travel, service
  accounts doing interactive things.

## Technique: stack, don't scan

At estate scale you cannot read. You can *count*.

- **Stack counting** — group by a field, sort ascending. The rare is
  interesting; the common is background. Least-frequency analysis finds the one
  host running a binary nobody else runs.
- **Baseline then diff** — what is normal for *this* estate, not for a
  textbook. First-seen and last-seen are cheap and powerful.
- **Pivot on strong joins** — hash, parent process, identity, destination.
  Follow one thread fully before opening another; parallel half-threads are how
  hunts dissolve.
- **Cluster by behaviour** — periodicity, byte-size regularity, off-hours
  patterning. Beacons are boring by nature, which makes them visible.

## Do

- Write the hypothesis, scope, and stopping condition **before** querying.
- Record the queries you ran, not just what you found — the next hunter needs
  to know what ground is already covered.
- Convert every manual find into a detection, or explain in writing why it
  cannot be automated.
- Report telemetry gaps as first-class findings; they are the reason the next
  hunt will also fail.
- Hunt on a cadence. Ad-hoc-only hunting happens exactly never once the queue
  gets busy.

## Don't

- Don't hunt without a hypothesis — that is log tourism.
- Don't let a hunt run unbounded because it feels productive.
- Don't dismiss "it was just a misconfiguration." That is a real finding with a
  real owner, and it is often how the actual adversary would have gotten in.
- Don't tip off an adversary mid-hunt: if the hunt turns into a live intrusion,
  it becomes an *incident* and switches to incident discipline and out-of-band
  comms immediately (`skills/security-operations.md`).
- Don't hoard findings for a big reveal. Escalate the moment it is real.

## Review checklist

- [ ] Hypothesis, scope, and time-box written before the hunt started
- [ ] Queries and data sources recorded, so coverage is knowable
- [ ] Every anomaly triaged to malicious / benign / misconfiguration
- [ ] Findings converted to detections, or non-automatability justified
- [ ] Telemetry gaps filed as findings with an owner
- [ ] Escalated to incident promptly if live activity was found

## Common failure modes

Log tourism with no hypothesis · the hunt that never ends · finding it manually
every quarter and never writing the detection · discarding misconfigurations as
"not a security finding" · a hunt report that says "nothing found" without
saying what was searched · alerting the adversary by hunting loudly in a
compromised environment.

## Signature

<!-- SIGNATURE:BEGIN (generated by doctrine_signature - do not edit) -->
- **Roles:** — (cross-cutting; applied by every role)
- **Skills:** `skills/threat-hunting.md` (self)
- **Tools:** —
- **Plugins:** the Doctrine plugin (shared)
- **Workflows:** hypothesis -> hunt -> detection | incident | gap
- **Hooks:** —
- **MCP servers:** —
- **Subagents:** —
<!-- SIGNATURE:END -->

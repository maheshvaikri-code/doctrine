# Skill: Threat Intelligence

**Scope.** Turning knowledge of adversaries into things the SOC can act on —
indicators, techniques, priorities. Feeds `skills/detection-engineering.md`
(what to build), `skills/threat-hunting.md` (what to look for), and severity
judgement in `skills/security-operations.md`.

**The test for every piece of intel: what would we do differently?** Intel that
changes no detection, no hunt, no priority, and no control is not intelligence —
it is news. Consuming it feels productive and costs real attention.

## Principles

- **Relevance beats volume.** A feed of a million indicators for sectors you are
  not in, technologies you do not run, and actors who have never targeted your
  region is a cost, not an asset. Filter to *your* attack surface first.
- **Indicators expire; techniques persist.** The pyramid of pain is the right
  mental model — hashes and IPs are trivially rotated, tooling and behavioural
  patterns are expensive for an adversary to change. Build toward the top;
  it hurts them more and rots less.
- **Confidence is part of the claim.** Every assessment carries a confidence
  level and its basis. Intel repeated without provenance becomes fact by
  laundering — it circulates, gains authority from repetition, and nobody can
  trace it back to check.
- **Attribution is slow, political, and rarely operational.** Knowing *which*
  actor changes almost nothing about what you must do in the next hour. Treat
  public attribution as a decision with legal and diplomatic weight, made by
  people with that authority — never a technical conclusion asserted casually.
- **Intel ages.** An indicator with no expiry is a future false positive, and a
  TTP report from three years ago may describe tooling long since abandoned.

## The pyramid of pain, operationally

| Level | Adversary cost to change | Use it for |
|---|---|---|
| Hash | Trivial | Blocklists, retro-hunting; expect decay in days |
| IP / domain | Easy | Short-lived blocking, pivot points |
| Network / host artifact | Annoying | Durable-ish detections |
| Tool | Hard | Strong detections; survives campaign changes |
| **TTP** | **Very hard** | **The detections worth investing in** |

Spend detection-engineering effort proportional to the pain you inflict. Cheap
indicators are still worth ingesting — automate them, expire them, and do not
mistake that automation for coverage.

## The lifecycle

```
requirements → collection → processing → analysis → dissemination → feedback
   ↑                                                                   │
   └───────────────────────────────────────────────────────────────────┘
```

**Requirements first.** Without them, collection becomes hoarding. State what
the organisation needs to know — which actors plausibly target this sector,
which techniques matter given how this estate is actually built, what would
change a decision. Then collect against *that*.

**Feedback closes it.** Did the intel produce a detection that fired? A hunt
that found something? If a source has never once changed an action, cut it.

## Consuming intel

- **Score sources**, don't trust them uniformly. Track: was it timely, was it
  accurate, was it actionable, was it relevant to us? A source that has never
  produced an action is costing you attention.
- **Deduplicate and expire.** Indicators need TTLs. An IOC list that only ever
  grows becomes a false-positive engine and eventually gets ignored wholesale.
- **Map to ATT&CK** so intel lands in the same vocabulary as coverage and hunts.
  Without a shared taxonomy, intel and detection teams talk past each other.
- **Beware circular reporting.** Three vendors citing the same original source
  is one source. Provenance, not repetition, is what makes a claim strong.

## Producing intel (internal)

Your own incidents are the highest-relevance intel you will ever have — they
are, by definition, about an adversary who actually targeted you.

- Extract TTPs from every incident, not just indicators.
- Write assessments with explicit confidence and explicit evidence.
- Share within the constraints legal and compliance set (sector ISACs, trusted
  groups) — and never share customer data, PII, or anything under privilege
  without an approval on record.

## Do

- Start from intelligence requirements; discard what doesn't serve them.
- Attach confidence, source, and expiry to every indicator and assessment.
- Convert TTP intel into detections and hunts — that is the point of it.
- Track whether each source has ever changed an action; prune what hasn't.
- Distinguish *observed in our estate* from *reported elsewhere*. They warrant
  very different responses.

## Don't

- Don't ingest everything because it is free — attention is the real cost.
- Don't let indicators live forever without review.
- Don't repeat an assessment without its provenance and confidence.
- Don't attribute publicly, or act on attribution alone; that is a §5
  decision with legal weight, not a technical call.
- Don't confuse a vendor's threat report with a change in *your* risk until
  you have checked it against your actual attack surface.

## Review checklist

- [ ] Intelligence requirements written and current
- [ ] Every indicator carries source, confidence, and expiry
- [ ] Intel mapped to ATT&CK and joined to coverage/hunt backlogs
- [ ] Source scoring reviewed; unproductive sources cut
- [ ] Internal incident TTPs extracted and fed back
- [ ] Any external sharing cleared with legal/compliance

## Common failure modes

The million-indicator feed nobody filtered · IOCs with no expiry quietly
generating false positives · circular reporting mistaken for corroboration ·
intel that never becomes a detection · confident attribution built on one
vendor blog · treating a threat report about a technology you do not run as a
reason to act · sharing incident detail externally without approval.

## Signature

<!-- SIGNATURE:BEGIN (generated by doctrine_signature - do not edit) -->
- **Roles:** `roles/detection-engineer.md` · `roles/soc-analyst.md`
- **Skills:** `skills/threat-intelligence.md` (self)
- **Tools:** —
- **Plugins:** the Doctrine plugin (shared)
- **Workflows:** requirements -> collection -> analysis -> dissemination -> feedback
- **Hooks:** —
- **MCP servers:** —
- **Subagents:** —
<!-- SIGNATURE:END -->

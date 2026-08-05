# Skill: Detection Engineering

**Scope.** Building, testing, tuning, and retiring the detections a SOC runs
on — detection-as-code. The rules themselves, their coverage, their
false-positive budget, and the pipeline that ships them. Loaded by
`roles/detection-engineer.md`; the operating context is
`skills/security-operations.md`.

**A detection is code.** It has a source of truth, review, tests, a deploy
path, versioning, and a rollback. A rule pasted into a SIEM console by hand,
with no test and no history of who changed it or why, is the security
equivalent of editing production by SSH.

## Principles

- **Every detection carries a hypothesis.** "An adversary doing X leaves trace
  Y in log Z." Without the sentence, nobody can judge whether the rule works,
  and nobody can tune it without guessing at intent.
- **Untested coverage is not coverage.** A rule that has never fired in a
  controlled test is a claim. Emulate the technique, watch it fire, keep the
  evidence — that is the difference between a coverage map and a coverage
  *spreadsheet*.
- **False positives are a budget, spent from analyst attention.** Every rule
  has a cost per week in triage minutes. Rules that cannot justify their cost
  get tuned or retired — the third option, "leave it noisy," silently spends
  the budget on nothing.
- **Detect behaviours, not artifacts, where you can.** Hashes and domains
  rotate in hours; the *technique* (`skills/threat-intelligence.md`: the
  pyramid of pain) survives. Artifact detections are cheap and brittle; keep
  them, but know which kind you are buying.
- **The log you don't collect defeats every rule you write.** Detection
  engineering starts at the telemetry inventory, not at the rule editor.

## Detection-as-code pipeline

```
hypothesis → rule (Sigma / KQL / SPL / EQL / YARA) → unit test against
  known-bad + known-good samples → peer review → staged deploy (shadow /
  alert-only) → production → measured FP rate → tune | retire
```

- **Source of truth is the repo**, never the console. The console is a deploy
  target.
- **Shadow mode first** for anything with a plausible FP surface: it fires into
  a side channel, nobody is paged, and you measure the real rate against real
  traffic before it can wake anyone.
- Rules ship through the same gates as any other code — G3 build, G4 review,
  G5 verification. `standards/git-conventions.md` applies; a detection change
  is a commit with a why.

## Writing a rule

Every detection carries, as structured metadata beside the logic:

| Field | Why it exists |
|---|---|
| Hypothesis | What adversary behaviour this claims to catch |
| ATT&CK technique(s) | Coverage mapping, and the shared vocabulary |
| Data source(s) | Which telemetry it needs — breaks loudly if that stops flowing |
| Severity | Feeds triage priority, from the written matrix |
| Known FP causes | What benign thing looks like this — the triage shortcut |
| Response guidance | What the analyst should do first (link the runbook) |
| Test evidence | The emulation that made it fire, and when |

A rule without "known FP causes" makes every analyst rediscover them
independently, at 3am, one at a time.

## Testing

- **Positive test:** emulate the technique (Atomic Red Team-style, a purple-team
  exercise, or a recorded sample) and confirm the rule fires.
- **Negative test:** run it against a corpus of normal activity and count what
  it catches. This is where the FP rate comes from — measured, not estimated.
- **Regression:** a rule that has fired truly once keeps its sample; changes are
  re-run against it. Tuning that silently breaks the original catch is the most
  expensive mistake in this discipline, and the easiest to make.
- **Data-source health:** a test that the *telemetry* still arrives, separate
  from the rule. Silent log-source death is indistinguishable from peace.

## Tuning — narrowing without blinding

Tune by **adding specificity**, not by broad exclusion. Excluding a whole host,
user, or process name because it is noisy today creates a permanent blind spot
exactly where an adversary would most like to live — service accounts, admin
jump boxes, build agents. If an exclusion must be broad, it gets an expiry and
a review date, like any other security exception (`standards/governance.md`).

## Coverage

Map to MITRE ATT&CK, honestly:

- **Green** — detection exists, tested, fires, FP rate known.
- **Amber** — detection exists, untested or noisy.
- **Red** — no detection, or no telemetry to build one on.

Report the red honestly. A coverage map that shows all-green because untested
rules count as covered is worse than no map: it converts an unknown into a
false assurance, which is the fabrication §7 #1 forbids, wearing a chart.

## Do

- Version rules in the repo; deploy from it; diff what production actually runs
  against what the repo says (drift is real and silent).
- Give every rule an owner and a review date. Unowned detections rot into noise.
- Retire deliberately, with a note. A deleted rule with no record invites its
  own reinvention six months later.
- Test the *telemetry* as well as the rule.
- Prefer techniques over indicators when both are available.

## Don't

- Don't hand-edit rules in the console — the drift is undetectable and the
  history is gone.
- Don't ship a rule you have never seen fire.
- Don't tune by blanket exclusion of an identity, host, or path.
- Don't count untested rules as coverage.
- Don't let a noisy rule stay noisy because deleting it feels like losing
  ground. Noise *is* losing ground.

## Review checklist

- [ ] Hypothesis stated; ATT&CK technique(s) mapped
- [ ] Positive test recorded (it fired) + negative test (measured FP rate)
- [ ] Known FP causes and response guidance written down
- [ ] Data-source dependency declared and health-checked
- [ ] Deployed from the repo, not the console; production diffed against source
- [ ] Owner and review date set; exclusions carry expiry

## Common failure modes

Rules that have never fired counted as coverage · tuning by excluding the
service account an adversary would use · a SIEM whose console and repo have
silently diverged · detections orphaned by a log source that stopped flowing
months ago · alert volume treated as productivity · the noisy rule everyone
mentally filters and nobody deletes.

## Signature

<!-- SIGNATURE:BEGIN (generated by doctrine_signature - do not edit) -->
- **Roles:** `roles/detection-engineer.md`
- **Skills:** `skills/detection-engineering.md` (self)
- **Tools:** —
- **Plugins:** the Doctrine plugin (shared)
- **Workflows:** detection-as-code: rule -> test -> shadow -> production (G3->G5)
- **Hooks:** —
- **MCP servers:** —
- **Subagents:** —
<!-- SIGNATURE:END -->

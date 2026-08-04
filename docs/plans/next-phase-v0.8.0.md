# Plan — Next Phase (v0.8.0 candidate)
<!-- G2 artifact. Owner: Chief Architect. Written 2026-08-03, after v0.7.0. -->

## Where v0.7.0 left things

The doctrine is now enforceable at two boundaries — the tool call and the
promotion — and observable across repos. Three things it deliberately did not
do, and one it could not:

- Enforcement binds only runtimes that honour a pre-execution hook.
- Attestation has nothing behind it until signing keys exist here.
- Policy still travels by reinstall; there is no distribution mechanism.
- **G4/G5 were author self-reviews.** That is the debt at the top of this plan,
  because everything below inherits its trustworthiness from it.

Sequencing rule: **P1 makes v0.7.0 trustworthy, P2 makes it honest, P3 makes it
organizational, P4 raises the evidence bar.** Do not start P3 before P1 lands —
distributing policy you have not independently reviewed multiplies a mistake
across every repo.

---

## P1 — Make v0.7.0 trustworthy (do first)

### P1.1 Independent verification of the v0.7.0 diff · Class M — **DONE 2026-08-03**

Ran. It overturned the release: REQUEST-CHANGES, a security **VETO** on five
proven findings, and a QA **FAIL**. Three blockers and nine majors, all fixed
with regression tests reproducing the verifiers' own payloads; see the
CHANGELOG `[Unreleased]` section and the appended verdicts in
`docs/reviews/` and `docs/qa/`.

Two lessons worth carrying forward, both structural:

1. **The author's self-review approved what three independent passes vetoed.**
   Every finding was reachable in one or two tool calls. This is now encoded:
   verifier roles are dispatched, not worn (`02-role-protocol.md`).
2. **A gate that fails on its own plumbing is a lockout, not a guard.** The
   hook resolved its script relatively; from a subdirectory python exited 2 —
   the hook contract's *block* code — and the guard froze the session that
   built it, including its own repair. Fail closed on the action you judge,
   never on your own wiring.

**Rounds 2 and 3 then vetoed the fixes**, each time because the previous round
had patched the reported payloads rather than the class. Round 3 forced the
real resolution: the Bash rule is reclassified as a tripwire, and the durable
guarantee moved to `doctrine_gold gate`, which re-hashes evidence and so does
not depend on intercepting whoever wrote it. Full account:
`docs/retro/2026-08-04-four-rounds-of-verification.md`.

**Third lesson, the expensive one:** when a bug class recurs *after* you fixed
it, the mechanism is wrong, not the coverage. Enumeration is a smell whenever
the domain is unbounded.

**Still open:** round 4 runs against commit `2885d29`. Nothing here is signed
off until a fresh context says so.

### P1.1c Doctrine edits earned by rounds 1–3 · Class S each

1. `skills/debugging.md` — "fix the whole bug class" needs its harder half: if
   the class recurs after you fixed it, the *mechanism* is wrong, not the
   coverage.
2. `skills/ai-slop.md` — name "an assertion that cannot fail" as a smell, with
   the hook test that asserted `returncode == 0` as the worked example.
3. `standards/dos-and-donts.md` — a corrected claim must be swept repo-wide;
   the first correction of the "reviewer physically cannot edit" claim reached
   one file in five.
4. `skills/tooling.md` — a gate must fail closed on the action it judges and
   never on its own plumbing (the relative-path lockout).

### P1.1b Original scope (kept for reference)
The gate the last release could not run. Dispatch fresh-context
`code-reviewer`, `security-reviewer`, and `qa-engineer` subagents against
`v0.6.46..v0.7.0`, each blind to the author's narrative.
- **Deliverable:** three independent artifacts; findings fixed or waived in
  writing. If they land clean, the disclosure in
  `docs/reviews/enterprise-control-plane.md` is retired by evidence, not by
  assertion.
- **Watch for:** the guard's pattern set (precision *and* recall), the drain
  fix under a client that never sends its body, `check_protected_in_command`
  false negatives (path spelled differently than the pattern: `./docs/...`,
  quoted, or via a variable).
- **Human:** none.

### P1.2 Roll the fleet to 0.7.0 · Class M
The tool to see drift exists; the drift is still there.
- Point `doctrine_fleet status --root <portfolio>` at every governed repo,
  capture the table as the before-state.
- Update each with `doctrine_install --target <path> --force`, then
  `doctrine_verify` in each. Force is required — the consistency-carrier guard
  refuses partial updates by design.
- **Deliverable:** a fleet table before and after, both pasted, plus a
  `.doctrine-state/fleet.json` so the view is one command from now on.
- **Human:** the list of repo paths. My notes say six repos were on v0.6.29;
  that note is old and unverified — the fleet run replaces it with fact.
- **Risk:** a `--force` reinstall overwrites Doctrine-managed files. The
  preservation contract covers `docs/`, `.doctrine-state/`, `memory/`,
  `sessions/`; run one repo first and diff before doing the rest.

### P1.3 Make attestation mean something · Class S (mostly human)
`--require-signature` currently refuses everything, because no key is
configured. That is honest but inert.
- **Human decision:** GPG or SSH signing, and which identity.
- Configure `user.signingkey` + `commit.gpgsign`/`tag.gpgsign`, re-cut v0.7.0
  as a signed tag (a correction is a new tag: v0.7.1), then add
  `--require-signature` to the gold-check step in the CI templates.
- **Deliverable:** one real signed tag whose `doctrine_gold check
  --require-signature` exits 0 — the end-to-end path v0.7.0's QA had to leave
  untested.

---

## P2 — Make the enforcement honest everywhere

### P2.1 A second runtime adapter for the guard · Class M
Today the gate is Claude-only in practice; the doctrine claims it for
"runtimes with an equivalent contract" without proving one.
- Wire the guard into one non-Claude runtime that supports pre-execution
  interception, or — if none in the estate does — write the degradation
  explicitly into each adapter overlay in `.Doctrine/adapters/`, so a Cursor
  or Copilot user reads "this repo's rules are advisory in your tool" rather
  than assuming cover.
- **Deliverable:** either a working second adapter or an honest per-adapter
  capability table. Both are acceptable; silence is not.

### P2.2 A real secret scanner at G5 · Class M
The guard is a fast inline floor with known false negatives (no
credential-shaped name, or a value containing spaces).
- Evaluate `gitleaks` against `standards/dependency-policy.md`; wire it as a
  G5 step and a pre-commit hook, keeping the guard as the point-of-action
  layer. Two layers, different failure modes.
- **Human:** §5 approval for a new external dependency.

### P2.3 Close or kill verifier write-isolation · Class M
v0.7.0 dropped this rule because no trustworthy role signal exists, and a rule
that cannot know the role would have been security theater.
- **Option A:** a real signal — `/role` writes a signed role marker the guard
  reads; verifier roles then cannot Write/Edit even when the runtime allows it.
- **Option B:** declare it permanently out of scope for the guard, since
  subagent tool restrictions already enforce it where subagents are used, and
  say so in `02-role-protocol.md`.
- **Deliverable:** a decision recorded in an ADR either way. An open "we should
  someday" is the worst of the three.

---

## P3 — The organizational plane

### P3.1 Policy distribution · Class L
Policy currently travels by reinstall, which means N repos need N deliberate
acts and drift is the default.
- Design a versioned policy pack (guard rules + protected paths + CI pins)
  that a repo *pins* rather than copies, plus `doctrine_fleet apply --dry-run`
  to show exactly what would change across the fleet before anything does.
- **Constraint:** must not become remote code execution by another name. A
  pinned, signed, human-approved pack — never "fetch and run latest".
- **Gate:** full G0→G7; this is the piece that turns a per-repo law into an
  org control plane, and it is the one most able to do harm at scale.

### P3.2 Scheduled drift watch · Class S
A CI job (or a scheduled agent) running `doctrine_fleet status --json`,
failing on drift and filing the table as an artifact. The tool already exits 1
for exactly this.

### P3.3 Gate ROI measurement · Class M
`doctrine_metrics` exists and is barely used. Measure findings per gate, cost
per task class, and time-to-green, then **delete the ceremony that does not
pay**. A doctrine that only ever adds gates is a doctrine nobody follows.
- **Deliverable:** one retro that removes something.

---

## P4 — Raise the evidence bar

### P4.1 Real-browser G5 for the control room · Class M
The open thread the state plane has carried for several sessions: five UI
states, keyboard, focus, responsive, reduced-motion, screen-reader — none
executed, because no browser backend is available in this environment.
- **Blocker:** a Playwright-capable environment. Until then the WorkHawk
  control room stays honestly unverified rather than quietly assumed.

### P4.2 Attestation for the state chain · Class M
Extend v0.7.0's tag-signature model from gold records to state checkpoints,
and anchor the chain head somewhere outside the repo. Today a repo-write
adversary can still recompute the state chain wholesale — the same weakness
attestation just fixed for promotion.

---

## Doctrine edits proposed by the v0.7.0 retro · Class S each

1. `skills/tooling.md` — a policy/enforcement tool is not done until it has
   governed its own authoring session.
2. `skills/testing.md` — freeze the tree during the run that produces cited
   evidence; a suite that reads source from disk is non-deterministic under
   concurrent edits.
3. `standards/dos-and-donts.md` — record which non-negotiables are mechanically
   enforceable and which are not, so the doctrine never claims cover it lacks.

---

## Decisions needed from the human

| # | Decision | Blocks |
|---|---|---|
| 1 | Push `v0.7.0` to `origin`? (external action, §5) | nothing local |
| 2 | Signing key: GPG or SSH, which identity | P1.3, and every later attestation claim |
| 3 | The fleet's repo paths | P1.2, P3.2 |
| 4 | `gitleaks` as a dependency | P2.2 |
| 5 | P2.3: real role signal (A) or formally out of scope (B) | P2.3 |

## Recommended first move

**P1.1 then P1.2.** Independent review of what just shipped, then the fleet
roll-forward — in that order, because rolling an unreviewed release across
every repo is how one mistake becomes six.

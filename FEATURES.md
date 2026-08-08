# FEATURES.md — session toggles

**This repo's autonomy and behaviour switches.** Loaded **once per session**
(`CLAUDE.md` imports it). Edit it, then run **`/features`** to re-read it
without restarting — an `@` import resolves only at session start, so a mid-session
edit is invisible until you refresh.

Toggles are **`on` / `off` only**. There is deliberately no allowlist of
permitted commands: a list of blessed strings goes stale, grows forever, and
gives a false sense of precision. A switch you can read in one line is honest
about what it does.

| Feature | State | What it changes |
|---|---|---|
| `autonomous-verification` | **on** | The guard answers **`allow`** instead of abstaining on: an ordinary file write, and a Bash command **every segment of which is a provably read-only verb with no output redirect** (`ls`, `cat`, `grep`, `git status`, `git log`, a pipeline of those…). On a repo whose brief declares `Delivery profile: solobuilder`, the Bash grant is instead **unconditional** — any command, not only provably read-only ones (see below). Run this repo's own fmt/lint/type/test/build and paste the real output. |
| `prune-on-force` | **on** | `--force` reinstall deletes corpus files removed upstream (backed up first). `off` = copy-only, stale files persist. |
| `drift-banner` | **on** | Warn every turn when the corpus on disk changed since this session started. |
| `state-plane` | **on** | Keep hash-chained checkpoints and hydrate them at session start. |
| `orchestration-ceremony` | **on** | Multi-agent dispatch (`03-parallel-execution.md`) and multi-iteration loops (`skills/loop-engineering.md`) produce their full paperwork: the mandatory G4/G5 fresh-context verifier panel, work-package brief docs, loop-journal lines, formal `docs/` review/QA artifacts. `off` = self-review instead of a dispatched panel, skip the paperwork — the same relaxation `Delivery profile: solobuilder` already gets, available here on any repo or profile. Does not touch the collision guard or the loop stop-rules — see below. |

## The one condition on autonomy

`autonomous-verification` grants **running and reporting**, nothing else. It
does not touch the permanent floor:

- **No secret ever reaches output.** If a command would print an API key,
  token, password, or `.env` content, redact it or do not paste it. The
  `PreToolUse` guard still denies writes containing credentials (§7 #2) — this
  toggle cannot and does not widen that.
- **§5 still stops the agent.** Publishing, deploying, spending, deleting data,
  force-push, history rewrite, new paid services — human decision, every time,
  toggle or no toggle.
- **Verification only.** "Run the gates" is not "run anything". A command that
  mutates the world outside this repo is not verification.
- **The Bash allow is narrow on purpose, on every profile except one.** It is
  not "this command is safe" — shell is Turing-complete and no static
  analysis of it ever will be complete (§7). It is the decidable claim "every
  verb here is drawn from a closed allowlist of readers, and no write
  redirect is present." An unrecognised verb, a pipe into a writer, `sed -i`,
  a nested shell, or a bare `>` anywhere still falls straight through to your
  own judgment — same as before this toggle existed.
- **Solo Builder is the one deliberate exception, chosen with the tradeoff
  shown, not inferred.** On a repo whose brief declares
  `Delivery profile: solobuilder` (or the legacy `personal`), this toggle
  grants **every** Bash command — including the ones this guard cannot
  classify at all — once every rule above it has already declined. That IS
  the "this command is safe" claim the previous bullet says is undecidable;
  it is granted anyway, scoped to this one profile, because a solo builder
  owns the whole blast radius of their own repo. It does **not** reach
  further than that: secrets, protected paths, control surface, §5, and
  test-weakening are unconditional and already ran by the time this fires —
  a solo-builder repo cannot force-push, publish, or leak a credential any
  more than any other profile can. What it loses is the tripwire itself: an
  unrecognised or disguised command now runs with no check of any kind. Every
  other profile — enterprise, startup, no profile at all — keeps the narrow
  grant above, unchanged.

Everything else in a gate's output is fine as it comes — full test output,
stack traces, compiler errors, timings. Truncating real evidence to look tidy
is the fabrication §7 #1 forbids.

## What `orchestration-ceremony` moves, and what never does

Swarm dispatch, verifier councils, and disciplined looping are Doctrine's job
(`03-parallel-execution.md`, `skills/loop-engineering.md`) — but unlike the
`PreToolUse` guard's Write/Edit/Bash decisions, none of that is code-enforced.
There is no hook that can intercept "how many subagents got dispatched" or
"how many loop iterations ran" the way the guard intercepts a tool call. Every
rule in those two files is prose the agent follows because the doctrine says
to — which means this toggle does not relax a code gate; it changes which
parts of that prose are binding.

**`off` removes — paperwork, not protection:**

- The **mandatory** G4/G5 fresh-context verifier panel becomes optional;
  self-review is allowed instead (same relaxation `Delivery profile:
  solobuilder` already carries, here available to any profile) — but the
  artifact **must open by disclosing it's a self-review**, per
  `02-role-protocol.md`. Skipping the panel is granted; presenting the
  result as a passed panel is not — that's a fabricated verdict under §7 #1
  whether or not this toggle is involved.
- Work-package brief documents before a fan-out.
- Loop-journal lines (`skills/loop-engineering.md`'s resume-point format).
- Formal `docs/reviews/`, `docs/qa/` artifact filing.

**Stays on regardless of the toggle — these are safety rules, not ceremony,
because they exist to stop file corruption and unbounded burn, not to
produce an artifact:**

- `03-parallel-execution.md` §1's fan-out limits: width ≤ 4 concurrent
  agents, no two packages editing the same file, contracts frozen before
  parallel work starts. This is what keeps concurrent workers from
  corrupting each other's output — it has nothing to do with who reads the
  result afterward.
- `skills/loop-engineering.md`'s execution caps: the iteration budget, the
  thrash detector, the token-jam rule, the flaky-test rule. These stop a
  loop from burning unbounded time and tokens on a hypothesis that already
  failed — that risk is identical whether or not anyone later reads a
  journal about it.
- Non-Negotiables §7 and the §5 escalation list, as always: no toggle in this
  file has ever reached those, and this one is no different.
- The Merge Council (`standards/merge-and-promotion.md`), where that
  standard applies. It is a stricter, separate mechanism layered on top of
  ordinary G4/G5, not a variant of it — this toggle's reach stops at
  `03-parallel-execution.md` and `skills/loop-engineering.md`.

## Turning one off

Set the cell to `off` and run `/features`. Off is a legitimate choice, not a
failure state — a repo that wants copy-only installs, or no checkpoints, is
configured, not broken.

Machine-readable form, if a tool needs it: a feature is **on** unless this
table says `off`. Tools that honour a toggle read it through
`tools/doctrine_features.py`; everything else here is read by the agent, like
the rest of the corpus.

**One exception, and it runs the other way.** `autonomous-verification` is the
only toggle that *widens* what happens without asking, so it is **opt-in**: if
this file is missing or unreadable, it is treated as **off**, not on. Absence
of the file is absence of consent. Every other toggle defaults **on**, so a
repo installed before that toggle existed keeps behaving exactly as it did.

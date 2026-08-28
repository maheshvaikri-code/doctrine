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
| `autonomous-verification` | **on** | The guard answers **`allow`** instead of abstaining on an ordinary file write (Write/Edit only — the guard no longer runs on Bash at all; see ADR-014). Run this repo's own fmt/lint/type/test/build and paste the real output. |
| `prune-on-force` | **on** | `--force` reinstall deletes corpus files removed upstream (backed up first). `off` = copy-only, stale files persist. |
| `drift-banner` | **on** | Warn every turn when the corpus on disk changed since this session started. |
| `state-plane` | **on** | Hydrate the state plane automatically at session start (`hydrate --if-present`, the SessionStart hook). `off` = that hook is a silent no-op. It does **not** disable the state plane: `checkpoint`, `verify` and an explicit `hydrate` are deliberate acts and keep working, so a chain already on disk stays readable and verifiable. |
| `orchestration-ceremony` | **off** | Multi-agent dispatch (`03-parallel-execution.md`) and multi-iteration loops (`skills/loop-engineering.md`) produce their full paperwork: work-package brief docs, loop-journal lines, formal `docs/` review/QA artifacts. `off` = skip the paperwork. Does **not** make the G4/G5 verifier panel optional — dispatching fresh-context `code-reviewer`/`security-reviewer`/`qa-engineer` costs no human friction (autonomous, no approval needed) and stays mandatory regardless; only its formal write-up is skippable. Does not touch the collision guard or the loop stop-rules either — see below. |

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
- **Shell commands are not governed by this guard at all** (ADR-014). `Bash`
  was removed from the `PreToolUse` matcher, so the hook does not fire on it:
  no inspection, no prompt from Doctrine, no latency. That is a deliberate
  retirement of the arm §7 already called "a tripwire, not a boundary" —
  four independent review rounds each found a new bypass spelling, and it
  produced false positives that denied ordinary reads. **What governs your
  shell is now your own tooling**: the harness's `permissions.deny`/`ask`
  lists (which a hook could never override anyway), and — for anything whose
  blast radius warrants it — a real boundary one layer down, per
  `skills/sandboxing.md`. Doctrine's remaining claim over Bash is prose:
  §5 and §7 still bind the agent; nothing mechanically enforces them there.
- **Do not "get the old behaviour back" by re-adding `Bash` to the matcher.**
  It does not restore the old behaviour — it is *strictly weaker than either*
  the old wiring or the current one, and a G5 audit proved it by execution.
  With `Bash` matched and this toggle on, the guard returns `allow` for
  anything outside its ~30 literal patterns, and a hook `allow` **suppresses
  the host's own permission prompt** — so `rm -rf docs/releases/gold`,
  `echo '' > tools/doctrine_guard.py` and `echo '{}' > .claude/settings.json`
  all run with no prompt from anyone. Today, with `Bash` unmatched, the host
  prompts for those according to your own settings. Re-adding `Bash` is only
  sensible together with `autonomous-verification: off`, and even then it
  buys you four literal-pattern rules, not path protection.
- **One consequence to know, because it reaches back into the sound arm.** A
  shell command is unchecked, and one thing a shell command can write is this
  guard's own policy. `.doctrine-state/guard.json` holding a non-blanket
  `allow` (say `tools/*`) exempts those paths from the path **and** secret
  rules — so the Write/Edit arm holds only until something rewrites its
  policy, with no prompt in that chain. Doctrine cannot close this from
  inside a repo the agent can write to. **And the obvious fix is mostly
  theatre, so know what you are getting:** permission rules match per tool,
  and `Bash(...)` patterns match command TEXT, not paths — no rule means
  "any command that writes this path". `Edit(...)` rules do reach the file
  tools plus a recognised subset of file commands (`cat`, `sed`, `head`,
  `tail`) — but they do nothing about `echo x > path` or a subprocess write,
  and Doctrine deliberately does **not** ship them: an `ask` rule always
  prompts (auto mode cannot clear it, no hook can override it), so shipping
  them reintroduced the Bash-level prompting that removing the Bash arm
  existed to end. Add them to your own settings if you want that trade; it
  is not Doctrine's to impose. The only complete
  control is an isolation tier (`skills/sandboxing.md`), whose
  `filesystem.denyWrite` is kernel-enforced — **and which is unavailable on
  native Windows**, where closing this means running under WSL2 or a
  container, not editing a config. Full chain: `05-packaging.md`.

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

**`off` removes — paperwork, not the review itself:**

- Work-package brief documents before a fan-out.
- Loop-journal lines (`skills/loop-engineering.md`'s resume-point format).
- Formal `docs/reviews/`, `docs/qa/` artifact filing — the panel's findings
  still get read and acted on; they just aren't written to a permanent file.

**Stays on regardless of the toggle:**

- **The G4/G5 fresh-context verifier panel dispatch itself**
  (`03-parallel-execution.md` §4). This was the toggle's first draft's
  actual mistake, corrected directly: dispatching `code-reviewer` /
  `security-reviewer` / `qa-engineer` to fresh context costs nothing in
  human friction — it's a tool call the agent makes without asking anyone,
  the definition of autonomous — so relaxing it bought no autonomy back and
  only cost the one thing `02-role-protocol.md` §"Switching hats is not
  separation of duties" exists to prevent: an author judging its own work.
  This toggle is **not** a door to self-review. The only two doors remain
  what `02-role-protocol.md` has always named — subagents technically
  unavailable, or a declared `Delivery profile: solobuilder` — and both
  still require the artifact to open with that disclosure.
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

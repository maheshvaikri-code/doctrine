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
| `autonomous-verification` | **on** | The guard answers **`allow`** instead of abstaining on: an ordinary file write, and a Bash command **every segment of which is a provably read-only verb with no output redirect** (`ls`, `cat`, `grep`, `git status`, `git log`, a pipeline of those…). Run this repo's own fmt/lint/type/test/build and paste the real output. |
| `prune-on-force` | **on** | `--force` reinstall deletes corpus files removed upstream (backed up first). `off` = copy-only, stale files persist. |
| `drift-banner` | **on** | Warn every turn when the corpus on disk changed since this session started. |
| `state-plane` | **on** | Keep hash-chained checkpoints and hydrate them at session start. |

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
- **The Bash allow is narrow on purpose, and stays narrow.** It is not "this
  command is safe" — shell is Turing-complete and no static analysis of it
  ever will be complete (§7). It is the decidable claim "every verb here is
  drawn from a closed allowlist of readers, and no write redirect is
  present." An unrecognised verb, a pipe into a writer, `sed -i`, a nested
  shell, or a bare `>` anywhere still falls straight through to your own
  judgment — same as before this toggle existed.

Everything else in a gate's output is fine as it comes — full test output,
stack traces, compiler errors, timings. Truncating real evidence to look tidy
is the fabrication §7 #1 forbids.

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

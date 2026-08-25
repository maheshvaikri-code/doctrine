# DoctrineOS — the agent is the user, and what that decides

**Supersedes** the stack reasoning in `00-THESIS-AND-PLAN.md` Part 2, which argued from speed.
**Date:** 2026-08-25 · **Status:** G1 revision

---

## The correction that starts this

The Phase-1 spike was run to answer "is Go faster than Python here?" It could not: the machine was running **38 Python and 45 Node processes**, and a Go static binary doing trivial work took **4,872 ms at its floor**. Every startup number I reported earlier — Python 1,875 ms, node 391 ms — was measured under that same contamination, partly of my own making.

**So speed is struck from the argument entirely.** Not "Go wins on speed" and not "Go loses on speed" — *unmeasured, and no decision may rest on it.*

Which turns out not to matter, because speed was never the real criterion.

---

## The criteria, derived from who actually uses this

The user is an agent. Often an autonomous, long-horizon one, in a container it did not build, on a repo it has never seen. That produces seven requirements a human-facing tool does not have.

| # | Requirement | Why an agent needs it and a human does not |
|---|---|---|
| **A1** | **Present without asking** | A human hits a missing runtime and installs it. An agent hits it and **autonomy ends at that line**. Every runtime prerequisite is a place the chain breaks. |
| **A2** | **Non-interactive, always** | Any prompt hangs an agent forever. No TTY, no confirmations, no pagers. |
| **A3** | **Machine-parseable output** | An agent parses; it cannot "just look at the error". Output must be structured, stable, and versioned. |
| **A4** | **Self-describing** | An agent cannot browse docs mid-task. The tool must explain itself: `--help`, `explain`, and errors that state what to do next. |
| **A5** | **Idempotent** | Long-horizon agents retry. Running install twice, or a gate twice, must be safe. |
| **A6** | **State inside the repo** | A fresh container each session means `~/.config` is gone. Anything the next session needs must be committed. |
| **A7** | **Deterministic** | Same input, same answer, every time — or an agent cannot reason about, cache, or trust it. |

Note what is absent: performance. A 50 ms difference is invisible to an agent that just spent 8 seconds thinking. **A1 and A6 are where autonomy actually breaks.**

---

## The finding that matters more than the language

Measured on a real v1 install:

```
254 files installed
230  corpus      -> byte-identical in every repo
  2  repo-owned  -> docs/ and .doctrine-state/
```

**90% of what v1 installs is duplication.** And the consequence is already documented, in your own notes: *15 installs, drifted across v0.6.19 – v0.6.46 against a v0.7.0 source.* Fifteen repos × 230 files is roughly 3,450 copies expected to stay in sync. They did not. They spread across ~28 versions.

The `doctrine_fleet` view exists to *manage* that drift. **A tool whose job is to observe a problem the architecture creates is a symptom, not a feature.**

For a long-horizon agent this is worse than untidy. An agent that governs six repos is reasoning against six *different* laws, none of which announces its version. That violates A7 outright.

---

## The model: thin repo, pinned corpus

```
repo/
  doctrine.toml        ~20 lines: version pin, packs, profile, overrides
  docs/adr/…           artifacts        <- committed. the product.
  docs/reviews/…       evidence         <- committed.
  .doctrine-state/     memory + chain   <- committed. (A6)
```

Everything else — corpus and runtime — lives once per machine, version-pinned by `doctrine.toml`, resolved by the binary.

What each property buys, against the criteria:

- **Drift ends** (A7). One corpus per machine; each repo pins a version. Six repos on three versions is now a fact the file *states*, not one the fleet tool has to discover.
- **The repo carries only what must be in it** (A6). Artifacts and state are the product and are committed. The library is not.
- **Upgrades are one operation**, not N `--force` reinstalls — the operation that this session proved can go wrong (a `--force` shipped the source machine's own `settings.local.json` into consumers once already).
- **Review surface collapses.** A pull request adding DoctrineOS is 20 lines a human can read, not 254 files nobody will.

**Offline / air-gapped fallback, because A1 is absolute:** `doctrine.toml` pins a version *and a hash*. If the corpus is not cached and there is no network, the binary runs in **vendored mode** — corpus committed into the repo as today. Degraded, honest, and it never blocks the agent. The default is thin; the fallback is v1's model.

---

## Now the stack, scored against A1–A7

| | Python | Node | **Go / Rust static** |
|---|---|---|---|
| **A1 present without asking** | macOS/Linux usually; **Windows no**; slim containers no; version skew 3.9↔3.13 | wherever the agent's own host runs — **but not in a Python or Go container** | **no runtime at all**; runs in `scratch`, alpine, distroless |
| **A2 non-interactive** | fine | fine | fine |
| **A3 parseable output** | fine | fine | fine |
| **A4 self-describing** | fine | fine | fine |
| **A5 idempotent** | design choice | design choice | design choice |
| **A6 state in repo** | design choice | design choice | design choice |
| **A7 deterministic** | interpreter + stdlib version drift | node + dependency-tree drift | **one file, one hash, one behaviour** |

A2–A6 are design decisions, identical whatever the language. **A1 and A7 are decided by the stack, and both point the same way.**

The decisive argument is not speed and never was:

> **A Node shop, a Rust shop, and a scratch container should not need Python installed to run gates that have nothing to do with their stack.** v1 charges exactly that tax, and for an agent it is not a tax — it is a wall.

**Go over Rust:** trivial cross-compilation to six targets from one CI job, faster iteration for a solo maintainer, stdlib covers the whole surface (`json`, `sha256`, `os/exec`, `filepath`). Rust's advantages here are marginal; its cost in build time is not.

**The honest cost, unchanged:** a compiled governance tool is less inspectable by the agent it governs. Mitigation is source-first — reproducible builds, `go install` as a first-class path, and the source in the same repo. The binary is a convenience; the source is the truth.

**One real portability hazard already found:** Go's regexp is RE2 and has **no backreferences**. Python's `SECRET_ASSIGNMENT` uses `(['\"])([^'\"\n]{12,})\1` — a matched-quote backreference. Porting that wrong would *silently weaken a credential rule*. This is exactly what Phase 2's differential oracle exists to catch, and it is the strongest argument for keeping v1's Python suite as the reference implementation rather than deleting it.

---

## What the spike actually established

**Valid, load-independent:** the Go port returns **identical decisions** to the Python guard on every case tested — `allow/allow`, `deny/deny`, `deny/deny`. Behavioural equivalence is provable and was proved.

**Invalid:** every timing number in this session.

**Therefore:** the Go decision proceeds — on **A1 (no runtime prerequisite)** and **A7 (one hash, one behaviour)**, both structural and verified. Speed is not cited, and should not be cited again until measured on a quiet machine.

---

## What changes in the plan

| Phase | Was | Now |
|---|---|---|
| 1 | prove Go is faster | **done differently** — proved behavioural equivalence; speed struck from the argument |
| 2 | port the moat | unchanged, and now clearly justified: differential oracle against v1's Python |
| 3 | pack the library | **corpus moves to machine-level, version-pinned** — not copied per repo |
| 4 | kernel corpus | unchanged |
| 5 | first screen | now includes `doctrine.toml` as *the* install artifact — 20 lines, not 254 files |
| 6 | cut over | unchanged |

**New work this creates:** a resolver (pin → cached corpus), the vendored-mode fallback, and a migration path from v1's 254-file installs. None of it is large; all of it is A1/A6/A7 work rather than performance work.

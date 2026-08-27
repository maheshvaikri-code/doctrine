# 05 — Porting by Differential Oracle

How the Go implementation is held to the Python one, and what that method
caught that reading the code did not.

## The problem with porting a verifier

A verifier is judged by what it **refuses**. That makes it uniquely easy to
port badly, because the failure mode is silent: a port that refuses less than
its reference still passes every happy-path test, still prints `verify OK`, and
still looks exactly like a working verifier. Nothing goes red. The tool simply
becomes weaker, and reports success while doing it.

That is the specific defect DoctrineOS exists to prevent, so it cannot be the
defect DoctrineOS ships.

## The method

Run **both** implementations across the input space and diff the results.
Three oracles, each aimed at a different layer:

| Oracle | What it compares | Cases |
| --- | --- | --- |
| `differential.py` | guard decisions on tool payloads | 24 |
| `canon_diff.py` | canonical bytes, byte-for-byte | 15 |
| `tamper_diff.py` | chain findings on a mutated real chain | 13 |

Two rules make these worth more than their case counts suggest.

**1. Compare findings, not verdicts.** An oracle that only asks "did both say
FAIL?" is far weaker than it looks, and this one proved it. With `seq` stored
as the string `"30"`, both implementations refused the record — perfect verdict
agreement — while Go printed `seq 0 != expected 30`. Go's `.(float64)` type
assertion had failed silently to zero, so the message pointed at a number that
appears nowhere in the file. The verdict was right and the explanation was
wrong, which sends a reader after a defect that does not exist. Comparing the
finding **text** caught it; comparing verdicts never would.

**2. A mutation must be able to pass.** A test that fails no matter what is not
a test. The three schema cases are run against `preschema.exe` — the identical
source with only the schema call excised — and the schema-only cases must come
back **OK** from it. The first time this control ran it immediately rejected
one of my own cases: I had retyped `seq`, which the seq check catches
independently, so the case was labelled SCHEMA-ONLY while proving nothing about
the schema. It now retypes `session_id`, a field no other check reads.

## What the method caught

Every item here survived me reading the code and believing it correct.

- **The schema rule was missing entirely.** Python validates each checkpoint
  against `checkpoint.schema.json`; the first Go port did not. All nine tamper
  cases still agreed, because every mutation I had chosen broke a hash — a hash
  break alone is enough to refuse. Nine-for-nine was coincidence, not coverage.
- **`seq 0 != expected 30`** — the coerced-zero message above.
- **Enum and const messages diverged.** Python uses `repr`:
  `'TAMPERED' not in ['clean', 'dirty']`. Go's `%v` gave
  `TAMPERED not in [clean dirty]`. Same refusal, two different descriptions of
  it.
- **`jsonEqual` compared `fmt.Sprintf("%v", …)`**, so the number `1` and the
  string `"1"` were equal. That does not merely mis-format a message — it
  **loosens the schema**, accepting values the schema forbids.
- **Map iteration made findings nondeterministic.** Go randomises map order by
  design, so a checkpoint with two bad fields named a different one between
  runs of identical input. Evidence that changes when nothing changed is not
  evidence. Keys are now walked in sorted order, which for canonical files
  (written `sort_keys=True`) is also Python's document order — so the port
  reproduces Python's choice rather than merely being stable.

- **A missing schema was reported as a finding.** `VERIFY FAILED (1)` with the
  absent file listed alongside real chain findings — telling a reader their
  evidence had been tampered with when the actual problem was an incomplete
  install. A finding says *your chain is bad*; an error says *I could not
  check*. `verifyFindings` now returns them separately, and `verify` exits 2
  for cannot-run versus 1 for a bad chain, matching the Python CLI.

## What the oracles could not catch

Two divergences were found by **reading the reference**, because no case in the
harness reached them. Worth stating plainly: an oracle proves agreement on the
cases you thought to write, and nothing about the ones you did not.

- **`minLength`/`maxLength` counted bytes, not characters.** Python's `len()`
  on a `str` counts code points; Go's `len()` on a string counts bytes. They
  agree only while the input is ASCII — and every case in the harness was
  ASCII. `"café"` is 4 to Python and 5 to Go, so the two disagreed about the
  same file, in opposite directions depending on which bound was checked
  (Go too permissive on `minLength`, too strict on `maxLength`). Now counts
  runes, with a test.
- **`integer` accepts `30.0` in Go, rejects it in Python** — a *known, bounded*
  divergence, left in place deliberately. Python's JSON gives `int` for `30`
  and `float` for `30.0`; Go decodes both to `float64(30)`. Telling them apart
  needs `UseNumber()` and literal-text inspection, which would also disturb the
  canonical-bytes path. The record is still refused either way — Go re-encodes
  `float64(30)` as `30`, which does not match the stored `30.0`, so the
  canonical-bytes check fires instead. Both reject; only the stated reason
  differs. Recorded in the code rather than left to be rediscovered.

Two harness bugs are worth recording as well, because both made the tools look
better than they were:

- `Path.write_text` opens in **text mode**, so every `\n` became `\r\n` on
  Windows. Mutations meant to leave bytes canonical were also tripping the
  canonical-bytes check — each case proved less than its label claimed.
- An early run of `tamper_diff.py` scored 2/9 because the harness never copied
  `.Doctrine/state-plane/schemas/`, so Python died before reaching a verdict.
  A harness bug, not a port defect — but indistinguishable from one until read.

## Current state

```text
Go suite                  13/13
guard differential        24/24  decisions agree
canonical bytes           15/15  byte-identical
chain findings            13/13  verdicts AND finding text identical
schema-only control        3/3   pass pre-schema binary, fail current
missing schema             both exit 2, same message (cannot-run, not a finding)
determinism                1 distinct output across 5 runs, two bad fields
```

The v1 Python suite could **not** be run to completion here. An earlier version
of this note called that a *hang* in
`test_doctrine_dashboard.TestHttpBoundary.test_rejects_unapproved_browser_origin`.
That was wrong, and the correction is worth more than the original claim.

Run in isolation, the test **passes in 50 seconds**. It had merely been the
last line printed when I stopped waiting — "stalled" was inferred from a
bounded wait, which is not evidence of a stall. Instrumenting the phases put
41s of those 50 in `_make_repo` (six `git` subprocesses), 0.025s in the server
and 0.048s in the request. Timing each git call showed even
`git config user.name` taking 8.5s, which no git workload explains. The
decisive test was the cheapest possible process:

```text
cmd /c exit    (in TEMP)      min= 5.763s  med= 6.485s
python -c pass (in TEMP)      min= 5.601s  med= 7.601s
git --version  (in repo)      min= 5.379s  med= 6.496s
```

**Process creation on that host costs ~6 seconds.** Not git, not the temp
directory, not the test code. Windows Defender real-time protection is off and
`Get-MpPreference` errors — the signature of a third-party product having taken
over — and `root\SecurityCenter2` reports **McAfee WPS** alongside Defender,
with 632 processes live (28 stale `python`, 25 stale `node`).

The suite has 364 tests over 73 subprocess call sites, many inside `setUp`. At
~6s a spawn that is comfortably the ~55 minutes observed, with only 3.5s of CPU
burned — blocked in process creation, not computing.

Two things follow. First, **no test code was changed**: the cause is
environmental, and editing tests until a symptom disappears is precisely the
symptom-patching `skills/debugging.md` forbids. Building the repo fixture once
per class instead of once per test would divide the spawn count, and is a fair
optimisation on its own merits — but it would not fix this, and adopting it
here would disguise a machine-level problem as a test-design one. Second, the
same pathology explains the invalidated performance numbers earlier in this
work; any timing taken on that host measures McAfee, not the code.

The remedy is AV exclusions for the working tree and TEMP. That is a change to
the machine's security posture, so it is the human's call, not the agent's.

## What this still does not prove

The chain is **tamper-evident, not tamper-proof**. It catches a record edited
after it was committed. It cannot catch a record forged and committed in one
step, because no prior state exists to diff against — which is why a
release-bound merge still needs a human reading the diff, not only a gate.

Nor does an oracle prove equivalence. It proves agreement **on the cases run**.
Every case here was chosen by the same person who wrote both sides, which is
the weakest part of the method and worth saying plainly. What it does buy is
that each disagreement found was real, and none of them were visible by reading.

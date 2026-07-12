# QA + Security Report — state-tooling (doctrine_state.py + doctrine_lint.py)
<!-- G5 artifact. File as docs/qa/state-tooling.md -->

> **RE-TEST 2026-07-12 (commit f86a02a): all findings remediated and re-verified by execution — final verdict PASS. See the Re-test section at the end of this report.** The sections below document the original FAIL pass against build 08c9bc94/7eb661b.

**QA Engineer** (fresh-context verifier) · **Security Reviewer:** same pass ·
**Date:** 2026-07-12
**Build under test:** working tree is not a git repo — identified by content hash:
`tools/doctrine_state.py sha256 08c9bc945e6fe2d837cacb71e3b216535f03b97ff09549b1a170bd91768c6232`
`tools/doctrine_lint.py  sha256 26e127bacdb635e0eab4f3b13dde3351b3add111b32059f2ec2cafd98521c2d1`
**Environment:** Windows 11, Python 3.12.7, git 2.50.1.windows.1. All state-plane
exercises ran in throwaway git repos under the session scratchpad; the doctrine
repo itself was not modified except for this report.

## Acceptance criteria verification

| # | Criterion (docs/brief.md) | How executed | Evidence (real output) | Pass |
|---|-----------|--------------|------------------------|------|
| 1a | Round-trip on fresh temp repo: init → checkpoint → verify OK | Fresh `git init` repo + schemas; full CLI sequence | `checkpoint 0 written at 1954d2922cdd (8115d091a0da); distillate c1966a648c50` · `verify OK: 1 checkpoint(s), chain intact, state_index hashes match` (exit 0) | YES |
| 1b | Tampered chain → verify fails | 9 tamper scenarios (T1-T9 below) | e.g. `VERIFY FAILED (1): - 3-5703d4b1de76.json: broken chain — prev_sha256 does not match predecessor's canonical bytes` (exit 1) | YES |
| 1c | Prune merges dead_ends forward | `checkpoint --keep 1` after 5 distillates; separately `prune --keep 1` then checkpoint | keep=1: `pruned 5 distillate(s)`; survivor carries deduped list incl. dead_ends from all pruned distillates. Manual prune: `merged negatives staged in pending-dead-ends.json`, consumed by next checkpoint, pending file gone | YES |
| 1d | `hydrate --check` compiles twice to identical bundle hashes | CLI `--check` + two real hydrates diffed | `hydrate --check OK: bundle_sha256 53ca91e7417b stable` (exit 0); diff of bundle bodies (header stripped) empty: BODIES IDENTICAL; headers differ only in `generated_at` | YES |
| 2 | Examples validate via shipped validator and are byte-canonical | `doctrine_lint` on real corpus (check 8) + seeded de-canonicalization on a corpus copy | real corpus: `doctrine_lint: corpus clean` (exit 0); seeded trailing space → `examples/checkpoint.example.json: not canonical bytes` (exit 1) | YES |
| 3 | `doctrine_lint` exits 0 on current corpus, nonzero on seeded broken reference (covered by test) | Ran on real corpus; seeded a ref to `skills/nonexistent-skill.md` in a corpus copy; test exists (tests/test_doctrine_lint.py TestBrokenRefCaught) | clean: exit 0; seeded: `doctrine_lint: 1 finding(s): - .Doctrine.md: broken reference` exit 1 | YES |
| 4 | All tests pass locally; CI workflow runs both | `python -m unittest discover -s tests` (twice); read .github/workflows/doctrine.yml | `Ran 21 tests in 2.879s / OK` (exit 0). Workflow runs lint then suite on ubuntu-latest, Python 3.12. Note: CI is Linux-only while the brief constraint is "Windows + POSIX" — Bug #2 is invisible to this CI | YES* |

*Criterion 4 passes as written, but see Bugs — the demo paths all pass while the
designed rejection path corrupts state (Bug #1), which sits inside criterion 1's
checkpoint semantics.

## Adversarial & edge matrix

| Input/scenario | Expected | Observed | Pass |
|----------------|----------|----------|------|
| 13 learned items (cap 12) | reject, nothing written | `validation failed: $.learned: 13 items exceeds maxItems 12` exit 2; no new checkpoint/distillate | YES |
| 12 learned items (limit) | accepted | `checkpoint 1 written` exit 0 | YES |
| claim 281 chars (cap 280) | reject | `$.learned[0].claim: longer than 280` exit 2 | YES |
| claim 280 chars (limit) | accepted | `checkpoint 2 written` exit 0 | YES |
| unknown field in control | reject cleanly | `$.control: unknown field 'mood' rejected (additionalProperties: false)` exit 2 — but it still appended a decision line first, see Bug #1 | NO |
| 9 active_intents (cap 8) | reject cleanly | `$.control.active_intents: 9 items exceeds maxItems 8` exit 2 — same Bug #1 side effect | NO |
| empty active_intents | valid; decisions slice scoped | checkpoint + verify OK; hydrate shows ALL decisions, not "active intents only" (finding L2) | PARTIAL |
| unicode claims (emoji, CJK, accented) | canonical UTF-8 round-trip | on-disk bytes are raw UTF-8 (od shows 303 251 for e-acute), LF-only, single trailing NL; bundle renders correctly | YES |
| 2nd checkpoint after git commit (at_commit moves) | chain links across commits | seq 0-2 at 1954d2922cdd, seq 3 at 50ad57f047ac, prev links intact, verify OK | YES |
| T1 tamper mid-chain (canonical forge of seq 2) | verify fails | `3-...: broken chain` exit 1 | YES |
| T2 non-canonical bytes (trailing space) | verify fails | `1-...: not canonical bytes` + downstream broken chain, exit 1 | YES |
| T3 delete latest distillate | verify fails | `state_index.latest_distillate_sha256 desync` exit 1 | YES |
| T4 forged DECISIONS.ndjson line | verify fails | `state_index.decisions_sha256 desync` exit 1 | YES |
| T5 tamper indexed intent file | verify fails | `intent 't-100' hash desync` exit 1 | YES |
| T6 delete indexed intent file | verify fails | `intent 't-100' indexed but missing` exit 1 | YES |
| T7 checkpoint.json != latest history copy | verify fails | `checkpoint.json != latest history copy` exit 1 | YES |
| T8 delete checkpoint.json, history intact | verify fails | `checkpoint.json missing while history exists` exit 1 | YES |
| T9 delete middle checkpoint (seq gap) | verify fails | `4-...: seq 4 != expected 3` + broken chain, exit 1 | YES |
| restore after each tamper | verify OK again | `verify OK: 6 checkpoint(s)` exit 0 | YES |
| keep=1 checkpoint | 1 survivor, dead_ends merged+deduped | `pruned 5 distillate(s)`; survivor holds deduped negatives from all pruned; verify OK | YES |
| prune --keep 0 / --keep -3 | fail-safe | refuses to delete (`nothing to prune`), exit 0 — message text is false ("1 <= keep 0"), finding L4 | YES |
| hydrate with missing intent in active_intents | flagged, no crash | `- ghost-42: MISSING intent file` in bundle; exit 0 | YES |
| stale artifacts after HEAD moves | STALE prefixes + header stale[] | `STALE@1954d2922cdd **t-100**`, `STALE@50ad57f047ac (distillate seq 4)`, header `"stale":["distillate","intent:t-100"]` — control block NOT flagged (finding L3) | PARTIAL |
| huge intent (120 ACs, ~11KB) | trimmed at budget, recorded, deterministic | `trimmed: intents`, header `"trimmed":["intents"]`, `hydrate --check OK ... stable` | YES |
| proposal missing required fields | clean error | `proposal missing 'control'` exit 2 | YES |
| proposal not JSON / file missing | clean nonzero error | raw JSONDecodeError / FileNotFoundError tracebacks, exit 1 (finding L1) | PARTIAL |
| proposal is a JSON array | clean error | `proposal missing 'session_id'` exit 2 | YES |
| not a git repo | clean error | `git failed: fatal: not a git repository` exit 2 | YES |
| effects: confirmed/pending/compensated/malformed lines | unresolved = pending + malformed = 2 | `unresolved effects: 2` in status and bundle | YES |
| status/prune under piped cp1252 stdout (Windows default) | works | prune CRASHES with UnicodeEncodeError traceback (Bug #2); status emits mojibake middle-dot byte | NO |
| init twice | idempotent | second run exit 0, no damage | YES |
| empty dir: status / verify / hydrate | graceful | `no state plane` 0 / `nothing to verify` 0 / `no checkpoint.json — run checkpoint first` 1 | YES |
| Windows case-insensitive FS: .doctrine/ vs .Doctrine/ | distinct dirs per spec | merged into one; `git ls-files` records `.Doctrine/state/checkpoint.json` — Bug #3 | NO |

## Regression

Suite: `python -m unittest discover -s tests` (run twice, plain + -v) in
D:\Doctrine\Doctrine-System:

```
..........
Ran 21 tests in 2.879s

OK
```

Lint on the real corpus: `python tools/doctrine_lint.py` →
`doctrine_lint: corpus clean`, exit 0. Flakes: none observed across repeated runs.

## Bugs found

| # | Repro steps (minimal) | Severity | Fixed @ | Re-verified | Regression test |
|---|----------------------|----------|---------|-------------|-----------------|
| 1 | (1) fresh repo, `init`; checkpoint a proposal whose distillate has a `decision_ref` claim → `verify` OK. (2) Same proposal with one unknown field added to `control` → `checkpoint` exits 2 (rejected). (3) `verify` → `VERIFY FAILED: state_index.decisions_sha256 desync`; DECISIONS.ndjson holds a phantom line for a checkpoint that never existed. Cause: `cmd_checkpoint` appends decisions (tools/doctrine_state.py:323-334) BEFORE checkpoint validation (line 354), contradicting the `# write phase (all validations passed)` comment and STATE.md's Dispose-then-Write ordering. The append-only log has no tool-supported repair, and the next valid checkpoint launders the phantom entry into the indexed record. | High | — | — | missing |
| 2 | On Windows with piped/redirected stdout (cp1252 default): `python tools\doctrine_state.py --root <repo> prune` when nothing to prune → unhandled `UnicodeEncodeError: 'charmap' codec can't encode character '≤'` (line 616 prints a less-than-or-equal sign), traceback, exit 1. `status` (line 640, middle dot) doesn't crash but emits a non-UTF-8 byte to UTF-8 consumers. Workaround: PYTHONUTF8=1. Brief constraint is "Windows + POSIX"; CI is ubuntu-only so it never sees this. | Medium | — | — | missing |
| 3 | On a case-insensitive filesystem (Windows/macOS default), in a repo containing `.Doctrine/` (the corpus): `init` + `checkpoint`, then `git add -A && git commit`. `git ls-files` records state as `.Doctrine/state/checkpoint.json` (merged into the existing capital-D dir). A clone on a case-sensitive FS materializes state under `.Doctrine/state/` while the tool reads `.doctrine/state/` → committed state is invisible after a Windows→Linux clone, violating STATE.md's "State that doesn't survive a clone isn't state." Partly spec-inherited (spec prescribes lowercase `.doctrine/` alongside uppercase `.Doctrine/`), but the tool neither detects nor warns. | Medium | — | — | missing |
| L1 | `checkpoint --proposal <malformed-or-missing-file>` → raw JSONDecodeError / FileNotFoundError traceback, exit 1, instead of the clean exit-2 error style used elsewhere. | Low | — | — | missing |
| L2 | With `active_intents: []`, the hydration Decisions slice includes ALL decisions; HYDRATION.md's table says "entries tagged to active intents only". | Low | — | — | missing |
| L3 | Control block never receives a STALE@ flag when checkpoint.json at_commit is behind HEAD, though STATE.md's staleness table says control is flagged and HYDRATION.md says "any source artifact behind HEAD". Distillate/intents/graph are flagged correctly. | Low | — | — | missing |
| L4 | `prune --keep 0` prints `nothing to prune (1 <= keep 0)` — statement is false (1 > 0); behavior itself is fail-safe (refuses to delete all). | Low | — | — | n/a |
| L5 | Budget overflow is a flat character clip; HYDRATION.md's Degrade-to column specifies structured fallbacks (e.g. intents → "titles + acceptance criteria only"). Trim is recorded and deterministic, so degraded bundles are honest but cruder than spec. | Low | — | — | n/a |

## Security sweep (per skills/security.md)

- Secrets scan: grep for password/secret/api-key/token over tools and tests — only false positives (LLM token-budget accounting, doctrine_state.py:40/41/440/441/605). Clean.
- Injection review: `subprocess.run(["git", *args], ...)` — list argv, no shell=True anywhere (grep for shell=True/eval/exec/pickle/os.system → none found). Proposal content never reaches a shell.
- Dep audit: AST import walk — doctrine_state: argparse, datetime, hashlib, json, pathlib, re, subprocess, sys; doctrine_lint: json, pathlib, re, sys + doctrine_state. Stdlib-only constraint holds; nothing to pip-audit.
- Dangerous constructs: file deletion limited to distillates/ names matching `^\d+-`; local/.gitignore written fail-safe (`*` + `!.gitignore`). Info: intent ids from control.active_intents are interpolated into paths unsanitized (`intent/{id}.intent.json`) — a hostile id like `../../x` reads outside the plane at hydrate; local-tool threat model, informational only.
- Bounds/fail-closed: every schema cap tested at limit and limit+1 — rejects at +1, accepts at limit; unknown fields rejected; verify fails closed on every desync tried (9/9). Exception: Bug #1 shows the checkpoint write path is NOT atomic with respect to validation — a fail-open seam in an otherwise fail-closed design.

**Security verdict:** SIGN-OFF with the Bug #1 atomicity note routed to G3 (integrity, not confidentiality) · human override: n/a

**QA verdict:** FAIL → returned to G3 with findings. Blocking: Bug #1
(a schema-rejected proposal — the validator's designed everyday path — corrupts the
append-only decisions log and leaves `verify` failing with no tool-supported
recovery). Should-fix before ship: Bug #2 (crash on a supported platform's default
piped stdout), Bug #3 (state does not survive a Windows-to-Linux clone; needs at
least detection or documentation). L1-L5 at author's discretion. Everything else —
chain integrity, tamper detection (9/9 scenarios), canonicalization, unicode,
determinism, budgets/trim/stale flags, prune-merge semantics, lint positive and
negative paths, the 21-test suite — held up under the full adversarial matrix.

---

# Re-test — remediation commit f86a02a (2026-07-12)

**Build under test:** commit `f86a02a71a682b13dd45bc987f611d6dfe7a6765`
("fix(tools): remediate all G4/G5 findings from the verifier fan-out");
`tools/doctrine_state.py` sha256 `5c7bbe4fc07b67f86b3130e3e5eec459a15b783da6bcec02127d9c634bd91e79`
(`doctrine_lint.py` unchanged). Spec amended: STATE.md 0.2.0 — state root is now
`.doctrine-state/`; checkpoint schema gains `intent_id` pattern + `propertyNames`;
CI workflow gains `permissions: contents: read` + `timeout-minutes`; `.gitignore`
updated. All re-tests executed in fresh scratch git repos.

## Finding-by-finding re-verification

| Finding | Re-test executed | Evidence (real output) | Status |
|---------|------------------|------------------------|--------|
| #1 High — rejected proposal corrupted decisions log | Exact original repro: good checkpoint w/ decision_ref → verify OK; re-submit with unknown control field; also the 9-intents vector | rejection: `error: $.control: unknown field 'oops' rejected` exit 2; `verify OK` exit 0 after BOTH rejections; DECISIONS.ndjson sha256 `ab3dd0145c0b...` byte-identical before/after, still 1 line; no stray checkpoint/distillate files | FIXED |
| #2 Medium — prune crash / status mojibake under cp1252 pipe | prune (nothing to prune) and status piped with `stdout enc: cp1252`, no PYTHONUTF8/PYTHONIOENCODING | `nothing to prune (1 distillate(s) <= keep 5)` exit 0; `distillates: 1 (pipe) unresolved effects: 0` exit 0 — ASCII only, no traceback, no mojibake | FIXED |
| #3 Medium — case-collision, state lost on POSIX clone | init + checkpoint + `git add -A && git commit` in a repo containing `.Doctrine/`; inspect `git ls-files` | all state recorded as `.doctrine-state/...`; zero paths under `.Doctrine/state/`; spec amendment in STATE.md 0.2.0 documents the rename | FIXED |
| L1 — tracebacks on malformed/missing proposal | not-JSON file; nonexistent file | `error: proposal nj.json: unparseable (Expecting value: ...)` exit 2; `error: proposal nope.json: [WinError 2] ...` exit 2 — no tracebacks | FIXED |
| L2 — decisions slice ignored empty active_intents | hydrate with `active_intents: []` | Decisions section reads `(no active intents - decisions omitted)` | FIXED |
| L3 — control block never STALE-flagged | checkpoint, then `git commit` moves HEAD, hydrate | Control line prefixed `STALE@911dfb8e4727`; header `"stale":["control","distillate","intent:t-100"]` | FIXED |
| L4 — prune keep=0 false message | `prune --keep 0`, `checkpoint --keep 0` | both: `error: --keep must be >= 1` exit 2 | FIXED |
| L5 — flat clip instead of degrade-to forms | distillate maxed at every schema cap (12 learned x 280 + 8 dead_ends + 6 threads + 6 actions; full form > 6400 chars) | `trimmed: distillate` in bundle + header; degraded section keeps all 8 dead_ends + 6 open_threads, drops learned (0 lines) and next_actions (0 lines) — exactly HYDRATION.md's "dead_ends + open_threads only"; `hydrate --check OK ... stable` on the degraded body | FIXED |

## New hardening since the first pass — verified by execution

| Behavior | Executed | Observed |
|----------|----------|----------|
| hydrate refuses unverified chain | tamper seq-1 history copy, run hydrate | `refusing to hydrate: chain verification failed (1 finding(s); run verify)` exit 1 |
| status warns on broken chain | same tampered plane | `WARNING: chain verification fails (1 finding(s)) - run verify. Status below is UNVERIFIED.` |
| secret-like distillate content rejected | AWS AKIA key in claim; password assignment; ghp_ token in dead_end | all three: `error: distillate text matches a secret pattern (...)` exit 2, nothing written |
| deep JSON bounded | 3000-deep nested array as proposal | `error: proposal deep.json: unparseable (maximum recursion depth exceeded ...)` exit 2, no traceback |
| oversized state file bounded | 6 MB proposal | `error: ... 6000017 bytes exceeds the 5000000-byte state-file bound` exit 2 |
| path traversal via intent ids | active_intents `../../evil` and `..` | `error: unsafe intent id in control: '../../evil'` exit 2; plane unmodified, verify still OK |
| unsafe intent filename on disk | `bad name!.intent.json` dropped into intent/ | `error: unsafe intent filename: bad name!.intent.json` exit 2 |
| history wipe detected | delete checkpoints/*.json, keep checkpoint.json | `checkpoint.json exists but checkpoints/ history is empty - history wiped or never copied` exit 1 |
| stray file in checkpoints/ | drop evil.txt into checkpoints/ | `stray file in checkpoints/: evil.txt` exit 1 (reported, no crash) |
| graph re-hashed at verify | index graph.json at checkpoint, then modify it; then delete it | `state_index.graph hash desync (graph.json changed since checkpoint)` exit 1; `state_index.graph.sha256 set but graph.json missing` exit 1 |
| checkpoint prints STATE.md step-4 command | every checkpoint | `remember (STATE.md step 4): git add .doctrine-state && git commit -m "state: checkpoint N"` |

## Regression sweep on the new build (all re-executed)

Happy path init → checkpoint → verify → status → hydrate --check → hydrate: all
green in a fresh scratch repo. Caps at limit+1 still reject (`13 items exceeds
maxItems 12`, `longer than 280` — exit 2); at-limit accepted (12x280-char claims,
8/6/6 arrays written at max). Unicode (emoji/CJK/accents) round-trips canonically
and hydrates. Tamper battery re-run: mid-chain forge, deleted distillate, forged
decision line, diverged checkpoint.json — all detected, exit 1; restored plane
verifies OK. keep=1 checkpoint pruned 4 distillates, merged dead_ends forward
with the documented cap-8 oldest-first drop note. Effects counting (confirmed /
pending / malformed) still 2 unresolved. Determinism: two hydrates diff to
BODIES IDENTICAL; --check stable including on stale-flagged and degraded
bundles. Empty-state commands degrade gracefully.

Suite and lint on the real repo:

```
Ran 38 tests in 9.053s

OK
(suite exit=0)

doctrine_lint: corpus clean
(lint exit=0)
```

Regression tests for the findings exist in tests/test_doctrine_state.py:
test_rejected_proposal_leaves_no_trace (#1), test_ascii_only_terminal_output
(#2), test_keep_below_one_rejected (L4), test_decisions_omitted_without_
active_intents (L2), test_degrade_keeps_dead_ends_drops_learned (L5),
test_refuses_broken_chain, test_secretlike_claim_rejected,
test_deep_json_bounded, test_traversal_intent_rejected_at_checkpoint,
test_property_names_traversal_rejected, test_history_wipe_detected,
test_stray_file_reported_not_crash, test_invalid_proposal_rejected_nothing_
written. Bug #3's fix is structural (STATE_DIRNAME + spec 0.2.0) with no
explicit collision test — acceptable; noted for completeness.

## Residual observations (non-blocking, informational)

- A plane initialized by the pre-fix build under `.doctrine/state/` is silently
  invisible to the new tool (no legacy-layout detection/migration hint). Only
  affects planes created during the window the old build existed.
- CI remains ubuntu-only; the cp1252 class of bug is now covered by
  test_ascii_only_terminal_output rather than a Windows CI runner. Acceptable.

**Security verdict (re-test):** SIGN-OFF — the Bug #1 atomicity seam is closed
(decisions hashed prospectively, written only after both validations); traversal,
secrets, and resource bounds all fail closed under adversarial input.

**QA verdict (re-test): PASS.** Every original finding re-verified fixed by its
exact reproduction steps; every claimed new hardening behavior demonstrated by
execution; full adversarial matrix re-run green on commit f86a02a; 38/38 tests,
corpus lint clean.

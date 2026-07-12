# QA + Security Report — state-tooling (doctrine_state.py + doctrine_lint.py)
<!-- G5 artifact. File as docs/qa/state-tooling.md -->

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

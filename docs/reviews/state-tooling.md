# Code Review — state-tooling @ uncommitted (on top of 8a396e2)
<!-- G4 artifact. File as docs/reviews/<task>.md -->

**Reviewer role:** Code Reviewer · **Date:** 2026-07-12
**Reviewed against:** `docs/brief.md` + `docs/plans/state-tooling.md`; specs
`.Doctrine/state-plane/STATE.md`, `.Doctrine/state-plane/hydration/HYDRATION.md`,
schemas in `.Doctrine/state-plane/schemas/`; standards
`.Doctrine/standards/coding-standards.md` + `languages/python.md` + `dos-and-donts.md`.
**Diff:** `tools/doctrine_state.py`, `tools/doctrine_lint.py`,
`tests/test_doctrine_state.py`, `tests/test_doctrine_lint.py`, `Makefile`,
`.github/workflows/doctrine.yml` (new); `.Doctrine/README.md`,
`.Doctrine/roles/fde.md`, `state-plane/examples/*.json` (modified).

**Executed** (Windows 11, Python 3.12.7, repo root):

```
$ python tools/doctrine_lint.py
doctrine_lint: corpus clean
exit=0

$ python -m unittest discover -s tests -v
... 21 tests ...
Ran 21 tests in 3.398s
OK
```

Plus eight targeted edge-case probes (temp git repos, driving the module
API and CLI directly). Key real outputs, abridged:

```
P1 invalid control + decision_ref claim:
  SchemaError raised (proposal rejected): $.control.ponytail_mode: 'INVALID' not in [...]
  decisions file exists after rejected proposal: True
  decisions content: {"at_commit":"3535...","claim":"phantom decision",...}
  valid checkpoint after: 0
  verify: 0            <-- phantom entry permanently baked in, verify blind

P2 cmd_prune on empty plane, stdout piped (cp1252):
  UnicodeEncodeError: 'charmap' codec cannot encode character U+2264
  in position 20  (doctrine_state.py:616, the "N <= keep" message)

P3 delete all files in checkpoints/, keep checkpoint.json:
  nothing to verify: no checkpoints
  verify exit code after full history wipe: 0

P4 stray notes.json in checkpoints/:
  verify CRASHED: ValueError invalid literal for int() with base 10: 'notes.json'

P5 Windows case-insensitive FS:
  dir entries matching '.doctrine' (case-insensitive): ['.Doctrine']
  state plane physically lives under: ['...\.Doctrine\state']
  (git in the temp repo records .Doctrine/state/checkpoint.json)

P6 graph.json present but no built_at_commit field:
  state_index.graph: {'built_at_commit': 'cc3fe7820f1c...', ...}  == HEAD (fabricated)

P8 tamper graphify-out/graph.json after checkpoint:
  verify after graph tamper: 0

H1 REPO.md invariants 120 lines (over the 800-token budget):
  invariant section chars: 3136; last invariant line present: False
  trimmed[] records it: []

H2/H3 distillate overflow (max-length schema fields):
  learned claims survive: 12/12 - dead_ends survive: 1/8 - open_threads: dropped
  trimmed: ['distillate']
  control behind HEAD: stale[] = ['distillate'] (control not flagged);
  header at_commit = commit of the checkpoint, not HEAD

P-order dead-end cap (cap=8, 2 new + 5 old-pruned + 5 newer-pruned):
  kept: NEW-0 NEW-1 OLD-0..OLD-4 NEWER-0   (drops the NEWEST pruned first;
  message and docstring claim "oldest first")

CLI failure path:
  python tools/doctrine_state.py checkpoint --proposal does-not-exist.json
  -> raw FileNotFoundError traceback (documented exit code 2 not produced)
```

## Findings

| # | Sev | Location | Finding | Suggested fix | Resolution |
|---|-----|----------|---------|---------------|------------|
| 1 | [BLOCKER] | tools/doctrine_state.py:323-334 vs :354 | Decision entries are appended to `DECISIONS.ndjson` (permanent, append-only, "never rewritten") *before* the checkpoint/control block is validated. A proposal with a valid distillate carrying `decision_ref` claims but an invalid `control` is rejected — yet its decisions persist forever; the next valid checkpoint hashes the polluted log and `verify` passes (probe P1). Violates STATE.md step 2 (validator checks **both** schema instances before write). | Validate both instances first; move all disk mutations, including NDJSON appends, into the write phase after both `validate()` calls succeed. Regression test: invalid control + decision_ref claim leaves the decisions file untouched. | fixed@f86a02a |
| 2 | [MAJOR] | tools/doctrine_state.py:378-384 | `verify` exits 0 ("nothing to verify") when `checkpoints/` is emptied while `checkpoint.json` exists (probe P3). Full-history wipe is exactly the tamper class `verify` exists to catch; brief AC says "tampered chain → verify fails". | Fail when `checkpoint.json` exists with no history. | fixed@f86a02a |
| 3 | [MAJOR] | tools/doctrine_state.py:407-426 | `verify` re-hashes decisions, distillate, intents — but never `graphify-out/graph.json`, though `state_index.graph.sha256` names it. STATE.md: "re-hashing the files named in `state_index`". Tampered graph → verify OK (probe P8). | When `state_index.graph.sha256` is present, re-hash the graph file (missing file = failure too). | fixed@f86a02a |
| 4 | [MAJOR] | tools/doctrine_state.py:440-444, 519-540, 546-557, 560-574 | HYDRATION.md degrade rules are not implemented — every section is blunt tail-truncation via `_clip`. On distillate overflow the clip keeps `learned` 12/12 and drops dead_ends 7/8 plus all open_threads (probe H2) — the exact **inverse** of the degrade-to spec ("dead_ends + open_threads only"; dead_ends is "the anti-thought-drift payload"). Decisions ("ids + one-line titles"), graph ("god nodes + EXTRACTED edges"), effects ("count + most-recent entry" — currently only ever a count) degrades also absent. Plan step 3 promised degrade tests; none exist. | Implement per-section degrade-to forms, truncating only after degrading; add an overflow test per section. | fixed@f86a02a |
| 5 | [MAJOR] | tools/doctrine_state.py:487 | Section 1 (invariants) is a never-trimmed section, yet `_clip` truncates it at the 800-token budget and the clipped flag is discarded (`text, _ = _clip(...)`) — silently cut and absent from `trimmed[]` (probe H1: last line gone, `trimmed == []`). Violates both "earlier sections are never trimmed" and "Every trim is recorded in the bundle header". | Never clip sections 1-2; oversized sources deserve a loud warning, not a silent cut. At minimum record the trim. | fixed@f86a02a |
| 6 | [MAJOR] | tools/doctrine_state.py:168 (`.doctrine`); spec STATE.md layout | On case-insensitive filesystems (Windows, default macOS) `.doctrine/` collides with the corpus dir `.Doctrine/`: probe P5 shows the state plane physically created under `.Doctrine\state\`, and git records `.Doctrine/state/checkpoint.json`. A plane initialized and committed on Windows is invisible to the tool on a Linux clone (`.doctrine/state` absent there). Partly spec-level naming — needs a human decision (rename one dir, or detect/normalize in `Plane.__init__`). | Short-term: detect an existing `.Doctrine` sibling and refuse/warn on init; long-term: non-colliding names in STATE.md. Escalate to the human. | fixed@f86a02a (spec 0.2.0) |
| 7 | [MAJOR] | tools/doctrine_state.py:616 | The "nothing to prune (N ≤ keep K)" message contains U+2264; on stock Windows any piped/redirected invocation gets cp1252 stdout and **crashes with UnicodeEncodeError** (probe P2 — the probe process died on it). Brief constraint: Windows + POSIX. | ASCII-only CLI messages, or reconfigure stdout/stderr with errors="replace" at entry; audit remaining non-ASCII output. | fixed@f86a02a |
| 8 | [MAJOR] | tools/doctrine_state.py:247-257 | `_graph_index` fabricates freshness: a `graph.json` without `built_at_commit` (or with undecodable content — errors swallowed) is stamped `built_at_commit = <current HEAD>` (probe P6). Defeats STATE.md failure-mode defense #2 ("stale-as-fresh") for the one artifact whose staleness rule is `built_at_commit != HEAD`, and writes invented provenance into a hash-chained artifact. The schema permits null. | Use null when absent/unreadable; treat unknown build commit as stale at hydration; warn instead of swallowing decode errors. | fixed@f86a02a |
| 9 | [MINOR] | tools/doctrine_state.py:378-381 vs :219-221 | `verify` globs `checkpoints/*.json` then parses the filename seq with int() — a stray non-seq file (e.g. `notes.json`) crashes it with a raw ValueError (probe P4). `_distillate_files` filters filenames with a digit-prefix regex; verify does not. | Apply the same filename filter; flag unexpected files as findings rather than crashing. | fixed@f86a02a |
| 10 | [MINOR] | tools/doctrine_state.py:300-301, 613-616 | `--keep` unvalidated: `checkpoint --keep 0` silently behaves as keep=1; `prune --keep 0` prunes nothing and prints the false claim "N ≤ keep 0"; negatives accepted (checkpoint keep=-3 prunes everything; prune keep=-1 no-ops). No tests. | Reject keep < 1 at argparse; test the boundary. | fixed@f86a02a |
| 11 | [MINOR] | tools/doctrine_state.py:260-278, 311-312 | Dead-end cap drop order contradicts its own documentation: docstring and runtime note say oldest dropped first, but pruned files are iterated oldest-first into the merged list, so the **newest** pruned negatives drop at the cap (probe: kept OLD-0..4, dropped NEWER-1..4). Also `except json.JSONDecodeError: continue` silently discards a corrupt pruned distillate, so "hard-won negatives outlive the prune" fails without a word. | Order merged candidates by recency; warn when a pruned distillate fails to parse. | fixed@f86a02a |
| 12 | [MINOR] | tools/doctrine_state.py:283, 296, 389, 472 | Failure paths unhandled at the CLI boundary: missing `--proposal` file → raw FileNotFoundError traceback (confirmed); corrupt JSON in state files → JSONDecodeError traceback in verify/hydrate/status; running in a repo without `.Doctrine/state-plane/schemas/` (i.e. any *target* repo per STATE.md layout) → FileNotFoundError. Documented exit code 2 not produced. | Catch OSError/JSONDecodeError in `main()`, one-line error, exit 2. Decide and document where target repos get schemas (embed as fallback?). | partial@f86a02a (residual: R-1 below) |
| 13 | [MINOR] | tools/doctrine_state.py:490-497, 595-600 | Staleness gaps: a checkpoint `at_commit` behind HEAD gets no STALE marker and no `stale[]` entry for the control section (probe H3), though STATE.md flags any control reference behind HEAD; the bundle header `at_commit` is the checkpoint commit, not generation HEAD. The intent-staleness rule ("references paths absent at HEAD") is reduced to an at_commit compare. | Flag control staleness; carry HEAD in the header. | partial@f86a02a (residual NIT: R-2) |
| 14 | [MINOR] | tools/doctrine_state.py:584-593 | `hydrate --check` compiles twice **in one process**. PYTHONHASHSEED is fixed per process, so cross-process nondeterminism (set-iteration order reaching output — the classic cause) cannot be caught. Today no set ordering feeds output text, so the pass is honest, but the gate is weaker than HYDRATION.md intends. | Second compile in a subprocess, or hash across two CLI invocations in the test. | disposition@f86a02a (documented, claim verified) |
| 15 | [MINOR] | tools/doctrine_state.py:54, 61, 81; workflow | languages/python.md: public functions must be fully hinted — `canonical_bytes(obj)`, `canonical_line(obj)`, `validate(...)` are unhinted and form the exported surface (imported by doctrine_lint and tests). coding-standards.md: formatting "enforced in CI" — no ruff/format step (ruff as dev-time CI tooling would not violate the stdlib-only *runtime* constraint). | Add hints; add ruff to CI. | OPEN (claimed fixed; is not - R-3) |
| 16 | [MINOR] | tools/doctrine_state.py (checkpoint); STATE.md step 4 | Protocol step 4 (git commit "state: checkpoint N", or charter-routed staged-for-human) is silently unimplemented — no flag, no output noting the un-committed state. dos-and-donts.md: narrowed scope is reported scope. | Implement a --commit/staged behavior or state the omission in docs and checkpoint output. | disposition@f86a02a (CLI prints the command) |
| 17 | [NIT] | tools/doctrine_lint.py:138-139; tools/doctrine_state.py:134-136, 685 | CLI asymmetry (doctrine_state: `--root` flag + argparse; doctrine_lint: bare positional, no --help); the items-keyword check sits inside the per-item loop; unreachable `return 2` fallthrough in `main`. | Author's call. | open (author's call) |
| 18 | [NIT] | .github/workflows/doctrine.yml | Actions pinned by major tag, not SHA; no least-privilege `permissions:` block. Security-reviewer's lane — noting for the fan-out. | Pin by SHA; add permissions. | partial@f86a02a (permissions+timeout; SHA-pin deferred, recorded) |
| 19 | [NIT] | tests/test_doctrine_state.py:79-82, 216-217 | `test_stable` compares two serializations in one process (same class as finding 14); `cmd_hydrate` stderr leaks into test output. | Author's call. | partial@f86a02a (degrade/determinism tests added; stderr leak remains) |

Severity meanings: see `.Doctrine/roles/code-reviewer.md`.

## Scope check

Diff matches plan slices 1-4 (tools, tests, Makefile, CI) plus slice 5
(examples re-canonicalized — verified byte-canonical by the shipped lint).
Two corpus edits ride along to make lint pass: `.Doctrine/README.md` count
sync (10→14 subagents — mechanical, correct) and `.Doctrine/roles/fde.md`
gaining a **Mission.** paragraph — that one is new doctrine *content*, not a
mechanical fix; fine, but the author should acknowledge it as scope.

Acceptance criteria: all met on the happy path, verified by execution —
init→checkpoint→verify round-trip OK; tampered chain fails verify;
prune merges dead_ends forward; hydrate --check stable; examples validate
and are byte-canonical (lint clean); lint exits 0 on the corpus and 1 on a
seeded broken reference (test passes); CI runs both. The findings above live
almost entirely in **failure paths, degrade behavior, and Windows
robustness** — exactly where a state-integrity tool earns its keep.

## Verdict

- [ ] Pass (0 BLOCKER, MAJORs resolved/waived)
- [x] **Return to build — REQUEST-CHANGES.** 1 BLOCKER (permanent
  decisions-log pollution from rejected proposals), 7 MAJORs (verify blind
  to history wipe and to graph tamper; degrade rules inverted vs spec;
  never-trim section silently cut; `.doctrine`/`.Doctrine` case collision on
  Windows — needs a human call; UnicodeEncodeError crash on Windows pipes;
  fabricated graph freshness). Happy-path acceptance criteria all pass; the
  chain/canonicalization core is solid and well-tested. Fix findings 1-8,
  re-run this review's probes, and this approves quickly.

---

# Re-review @ f86a02a — 2026-07-12

**Reviewer role:** Code Reviewer (fresh pass over the remediated tree).
**Executed** (all real output, this session):

```
$ python tools/doctrine_lint.py
doctrine_lint: corpus clean          (exit 0)

$ python -m unittest discover -s tests -v
Ran 38 tests in 8.947s
OK                                   (was 21; 17 regression tests added)
```

Every original probe re-run against the new code:

```
R1 rejected control + decision_ref claim:
  rejected: $.control.ponytail_mode: 'INVALID' not in [...]
  decisions exists: False | distillates: []          -> finding 1 FIXED
R2 full history wipe:
  VERIFY FAILED (1): checkpoint.json exists but checkpoints/ history is
  empty - history wiped or never copied  (exit 1); hydrate refuses (exit 1)
R3/R4 graph:
  graph index: {'built_at_commit': None, ...}        -> no fabrication
  VERIFY FAILED (1): state_index.graph hash desync   (exit 1)
R5 stray notes.json in checkpoints/:
  VERIFY FAILED (1): stray file in checkpoints/: notes.json  (no crash)
R6 case collision:
  root entries: ['.Doctrine', '.doctrine-state']; .Doctrine/state absent
R7 keep: checkpoint/prune keep=0 and keep=-1 all rejected ("--keep must
  be >= 1", clean error exit 2)
R8 dead-end cap: kept NEW-0 NEW-1 NEWER-0..4 OLD-0, dropped 4 oldest
  -> newest-preferential, message now truthful
R9 unicode distillate (accents/CJK/emoji): verify 0, hydrate --check 0

cp1252 pipe (the old crash environment): init/checkpoint/verify/status/
hydrate/prune/--help all clean, exits 0; failure paths print
"error: ..." and exit 2 (no tracebacks for proposal-missing, keep<1)

H1 invariants 200 lines (14,319 chars >> 3,200-char budget):
  last line present: True, trimmed: [] -> never trimmed, and
  hydrate --check still deterministic (exit 0)
Degrade (test_degrade_keeps_dead_ends_drops_learned, executed in suite):
  overflow keeps Dead ends + Open threads, drops Learned -> spec-conformant
Control staleness (test_control_stale_flagged, executed): stale[] contains
  "control", STALE@ prefix in body
```

Spec/schema amendments verified consistent: STATE.md 0.2.0 amendment note,
HYDRATION.md, 01-workflow.md, state-plane/README.md, `.gitignore` all say
`.doctrine-state/`; checkpoint schema gains `$defs.intent_id` +
`propertyNames` (validator supports it; traversal ids rejected at schema
AND runtime — both covered by tests I ran).

## Residual findings

| # | Sev | Location | Finding | Suggested fix |
|---|-----|----------|---------|---------------|
| R-1 | [MINOR] | tools/doctrine_state.py:289 (also 698, 701) | Residual of finding 12: a non-UTF-8 `effects/*.effects.ndjson` file crashes checkpoint/hydrate/status with a raw UnicodeDecodeError traceback (probe: hydrate CRASHED UnicodeDecodeError 0xff). Effects files are external-writer inputs and are NOT hashed in state_index, so verify-first does not shield this path. Decisions `read_text`/`json.loads` in build_bundle_body are similarly unguarded but are shielded by the verify-first sha check in practice. | Route these reads through the same load_json/StateError hardening (per-line: malformed = unresolved entry, like the JSONDecodeError branch already does). |
| R-2 | [NIT] | tools/doctrine_state.py:766-771 | Residual of finding 13: bundle header `at_commit` is still the checkpoint's commit, not generation HEAD (control STALE flag now compensates); intent staleness is an at_commit compare, not the spec's "references paths absent at HEAD". | Author's call. |
| R-3 | [MINOR] | tools/doctrine_state.py:79, 85, 98, 119; CI | Finding 15 was reported fixed but is not: `canonical_bytes(obj)`, `canonical_line(obj)`, `validate(instance, schema, root=None, path="$")` remain unhinted (they are the exported surface, imported by doctrine_lint and the tests); `load_json` lacks a return hint; no ruff/format step exists in the workflow or Makefile. Flagging the claim-vs-reality gap per the honesty rules; the code itself is MINOR. | Add the hints; add a ruff step to CI. |

Also noted, no action demanded: decisions are now written via a full-file
`write_bytes` of existing+new bytes (content-equivalent to append; the
"append-only" property holds at the content level); `--help` prints one
em-dash from the docstring (cp1252-encodable, exits 0 under cp1252 — the
"ASCII-only terminal output" claim technically excludes it).

## Scope check (re-review)

Remediation commit touches exactly the finding surface plus the spec
amendment it requires (STATE.md/HYDRATION/01-workflow/README/.gitignore/
checkpoint schema) and security/QA-driven hardening (intent-id traversal
defense, secret scan, JSON bounds, git timeout) belonging to the sibling
reports. `tools/doctrine_lint.py` untouched (its NITs stand as author's
call). One hygiene note: `tests/__pycache__/` and `tools/__pycache__/`
are untracked in the working tree — worth a `.gitignore` entry.

## Final verdict

- [x] **Pass — APPROVE-WITH-NITS.** The BLOCKER and all 7 MAJORs are
  fixed, each verified by re-executing the original failing probe and by
  a regression test that I ran (38/38 green; corpus lint clean).
  Remaining: R-1 [MINOR] (non-UTF-8 effects file -> raw traceback),
  R-3 [MINOR] (finding 15 reported fixed but not: public-surface type
  hints + ruff still absent), R-2 and assorted NITs. None block; land
  R-1/R-3 as immediate follow-ups, and correct the remediation record
  for finding 15.

---

# Delta review — v0.3.0 session wiring @ working tree on f2ee5d5 — 2026-07-12

**Reviewer role:** Code Reviewer (fresh pass). **Scope:** uncommitted delta
per `docs/plans/state-tooling.md` slices 7-10: `hydrate --if-present` +
`--emit-agents` (tools/doctrine_state.py), `.claude/settings.json`
SessionStart hook, `CLAUDE.md` bundle import, `.claude/commands/checkpoint.md`,
04-agent-adapters "State-plane wiring", HYDRATION.md CLI section, 5 new tests.

**Executed** (real output):

```
$ python tools/doctrine_lint.py        -> doctrine_lint: corpus clean (0)
$ python -m ruff check tools tests     -> All checks passed! (0)   [ruff 0.8.6]
$ python -m unittest discover -s tests -> Ran 43 tests ... OK
```

Prior residuals confirmed fixed at HEAD (b5b8717): R-1 effects reads now go
through `read_ndjson_text` hardening; R-3 hints present
(`canonical_bytes(obj: object)`, `validate(instance: object, schema: dict,
...)`) and ruff wired into Makefile + CI, executed clean above.

Emit-path probes (temp git repos, real output):

```
E1 marker block at EOF, no trailing newline:
   replaced cleanly, single marker pair, byte-idempotent    -> PASS
E2 CRLF AGENTS.md:
   CRLF preserved in user content: False; no CRLF left      -> whole file
   rewritten LF outside the markers (one-time churn)
E3 empty AGENTS.md: emits, idempotent, but file starts b'\n\n<!--...'
E4 swapped markers (END before BEGIN):
   rc 0, output has 2 BEGIN + 2 END, layout mangled          -> silent
   corruption (the lone-marker guard exists; the order case slips past)
E5 duplicate marker pairs: rc 0, second (stale) block survives forever
E6 bundle body containing the literal END marker (a 280-char learned
   claim fits it comfortably):
   first emit: END count 2; re-emit: END count 3, file grew 785 -> 976
   bytes                                                    -> silent,
   COMPOUNDING corruption on every re-emit
E7 6.4 KB block into a 2-byte AGENTS.md: emits, stable       -> PASS
```

## Findings (delta)

| # | Sev | Location | Finding | Suggested fix | Resolution |
|---|-----|----------|---------|---------------|------------|
| D-1 | [MAJOR] | tools/doctrine_state.py:785-810 (emit_agents_block) | Marker integrity is not validated. (a) A bundle body containing the literal `<!-- doctrine:state:end -->` string - e.g. a learned claim written by a session that worked on this very feature - injects an early END into the block; every subsequent emit splits at the first END and re-appends, silently compounding garbage into a committed file (probe E6: END 2 -> 3, 785 -> 976 bytes, exit 0 throughout). (b) Swapped markers (END before BEGIN) pass both `in`-checks and corrupt the layout with duplicated markers, exit 0 (E4), while the lone-marker case correctly raises StateError - the guard intent exists but misses these. (c) Duplicate marker pairs leave a permanently stale second block (E5). | Enforce exactly one BEGIN and one END with BEGIN before END, else StateError (same treatment as the lone-marker case); refuse or neutralize marker strings in the body before emitting (a SECRET_RES-style scan at checkpoint time, or escape on emit). Regression tests for all three. | fixed@working-tree (re-check below) |
| D-2 | [MINOR] | tools/doctrine_state.py:796 (read_text) + :807 (write_bytes) | A CRLF AGENTS.md is rewritten whole-file to LF on first emit (E2): `read_text` does universal-newline translation, `write_bytes` writes the translated text. The adapter contract (HYDRATION.md, quoted in the docstring) says the compiler owns the content *between the markers*; this mutates every line of a user-owned file. One-time churn, content preserved. | Splice on bytes, or detect and preserve the file's dominant line ending outside the block. | fixed@working-tree |
| D-3 | [NIT] | tools/doctrine_state.py:805 | Empty AGENTS.md: `"".rstrip("\n") + "\n\n" + block` emits a file starting with two blank lines (E3). Author's call. | `text.rstrip("\n")` -> conditional separator when text is empty. | fixed@working-tree |
| D-4 | [NIT] | tools/doctrine_state.py:815-835 | `hydrate --check --emit-agents` silently ignores the emit (`--check` returns first). Document or reject the combination. | Author's call. | fixed@working-tree |
| D-5 | [NIT] | .claude/settings.json | Hook invokes bare `python` - same convention as the Makefile; fine wherever the tool runs at all, noting for Windows py-launcher-only setups. | Author's call. | fixed@working-tree (doc note) |

## Scope and docs check (delta)

Diff matches plan slices 7-10 exactly; no unrelated edits. The four
`emit_agents_block` code branches and `--if-present` are covered by the 5
new tests (replace/append/skip/lone-marker/quiet-empty), all run by me;
the D-1 edge cases are not covered (regression tests belong with the fix).
Docs are honest: the CLAUDE.md-import ordering caveat and the deliberate
absence of a Stop-hook auto-checkpoint are both documented with rationale
in 04-agent-adapters.md (the "mechanical hook cannot write an honest
distillate" reasoning is exactly right). `/checkpoint` command matches the
STATE.md protocol and the schema caps it quotes. HYDRATION.md "Implemented"
claim verified against the CLI. The claim that a missing bundle import
no-ops on fresh clones is a documented adapter assumption I could not
execute-verify from here - it is stated, not hidden, which is the standard.

## Delta verdict

- [ ] Pass
- [x] **Return to build - REQUEST-CHANGES (delta only).** One MAJOR:
  marker integrity in `emit_agents_block` (D-1) - silent, compounding
  corruption of a committed adapter file from realistic state content,
  demonstrated by probe. The fix is small (order/count check + marker scan
  on the body) and the rest of the delta is clean: happy paths solid,
  byte-idempotency verified three ways, EOF/large-file edges pass,
  hooks/docs/tests match the plan slice. Fix D-1 (D-2 ideally with it),
  add the regression tests, and this approves on re-check.

---

# Delta re-check @ working tree (v0.3.0 remediation) — 2026-07-12

**Executed** (real output):

```
$ python tools/doctrine_lint.py        -> doctrine_lint: corpus clean (0)
$ python -m ruff check tools tests     -> All checks passed! (0)
$ python -m unittest discover -s tests -> Ran 49 tests ... OK
$ python tools/doctrine_state.py verify           (this repo's live plane)
verify OK: 2 checkpoint(s), chain intact, state_index hashes match
$ python tools/doctrine_state.py hydrate --check
hydrate --check OK: bundle_sha256 070c601046c6 stable
```

Every delta probe re-run against the fixed `emit_agents_block`:

```
E2' CRLF AGENTS.md: outside content preserved byte-exactly (CRLF kept),
    first emit idempotent, replace round-trip after a new checkpoint
    keeps CRLF outside + exactly one marker pair          -> D-2 FIXED
E4' swapped markers (END before BEGIN):
    StateError "marker integrity: expected exactly one begin/end pair in
    order"; file byte-untouched                           -> FIXED
E5' duplicate pairs: same StateError; file byte-untouched -> FIXED
E6' marker tokens in distillate text, four variants ("<!--", "-->",
    full END marker, bare "doctrine:state:end"): ALL rejected at
    checkpoint time (MARKER_RES), nothing written         -> FIXED
E6'' marker smuggled via an intent file (not distillate-scanned):
    emit backstop raises StateError, AGENTS.md byte-untouched, and plain
    `hydrate` (no emit) still succeeds                    -> FIXED
E3' empty AND whitespace-only AGENTS.md: block alone, no leading blanks
E1'/E7' regressions: EOF-no-newline replace + 6 KB block both still
    clean and idempotent
D-4' `--check --emit-agents`: explicit "ignored with --check" note
```

New regression tests cover each variant (swapped, duplicate, checkpoint
marker scan, emit backstop, CRLF preservation, empty-file, ignored-note);
I ran them in the 49-green suite. `04-agent-adapters.md` carries the
interpreter-name note (D-5). Rejection paths all leave the target file
byte-untouched - verified explicitly in the probes.

Accepted-cost notes (no action demanded): MARKER_RES also rejects benign
ASCII arrows (`A --> B`) in distillate text - fail-closed with a clear
message, consistent with the secret-scan posture; a marker-bearing
invariant/graph source makes `--emit-agents` (only) persistently error
until rephrased - same posture, plain hydrate unaffected (E6'' verified).

## Final delta verdict

- [x] **Pass - APPROVE.** All five delta findings (D-1 MAJOR through
  D-5 NIT) verified fixed by re-executing the original failing probes;
  no regressions across the earlier probe set; 49/49 tests, corpus lint,
  and ruff all clean; this repo's own live state plane verifies and
  hydrates deterministically. v0.3.0 session wiring is good to land.

---

# Delta review — v0.4.0 enterprise merge/promotion @ d5eab56 — 2026-07-12

**Reviewer role:** Code Reviewer (fresh pass). **Scope:** plan slices 11-14:
`standards/merge-and-promotion.md`, `templates/merge-verdict.md`,
`schemas/gold-build.schema.json`, `tools/doctrine_gold.py`,
`tests/test_doctrine_gold.py`, routing/workflow/README wiring.

**Executed** (real output):

```
$ python tools/doctrine_lint.py        -> doctrine_lint: corpus clean (0)
$ python -m ruff check tools tests     -> All checks passed! (0)
$ python -m unittest discover -s tests -> Ran 61 tests ... OK
```

Probes (temp git repos, real output, abridged):

```
G1 mtime chain ordering, clone-equalized mtimes:
   true order:  v1.9.0, v1.10.0, v1.11.0
   post-clone:  v1.10.0, v1.11.0, v1.9.0   (lexicographic tiebreak)
   _latest_gold picks v1.9.0 (true latest v1.11.0); the next promotion
   v1.12.0 CHAINS TO v1.9.0 - wrong predecessor - and check exits 0
G2 forged genesis (prev null) alongside older records:
   fresh mtimes: check exit 1 (detected)
   clone-equalized mtimes: check exit 0 (UNDETECTED)
G3 lightweight (non-annotated) tag: record succeeds rc 0
   (permission matrix says "annotated tags only")
G4 backslash artifact path: refused before write; absolute-with-drive
   path: rejected by relpath pattern (colon)
G5 duplicate artifact entries: accepted rc 0; soak result fail/degraded:
   rejected by schema (only "pass" recordable - by design)
G6 record tampered to artifacts:"not-a-list":
   check CRASHED: TypeError string indices must be integers
G7 record tag "--all": git argv executes rev-list first, then schema
   refuses the tag; nothing written (gold dir absent). check --tag
   "../secret": escaped path read, fails cleanly exit 1
G8 record with rebuilt worktree artifact under an older tag: rc 0,
   hashes the CURRENT disk bytes; no HEAD!=tag or dirty-worktree warning
```

## Findings (delta v0.4.0)

| # | Sev | Location | Finding | Suggested fix | Resolution |
|---|-----|----------|---------|---------------|------------|
| GD-1 | [MAJOR] | tools/doctrine_gold.py:66-70 (_gold_records mtime sort), :185-194 (chain check) | Chain ordering and genesis detection depend on file mtime, which an ordinary `git clone` equalizes (git does not preserve mtimes). Probe G1: post-clone, `_latest_gold` returns v1.9.0 instead of v1.11.0 and the next promotion chains to the wrong predecessor - the rollback ladder is silently mis-ordered with zero tampering involved; `check` passes because it only requires `prev_gold_sha256` to match ANY record on disk, not the true predecessor, and cannot see forks or wrong order. Probe G2: a forged genesis record (prev null) is detected with fresh mtimes but passes post-clone. The standard says "the chain IS the rollback ladder"; the ladder must not depend on filesystem timestamps. | Derive order from the chain itself: build the prev_sha256 -> record map, require exactly one genesis, unique predecessors (no forks), one head; `_latest_gold` = the chain head; `check` verifies the record's position by walking links. Use mtime for nothing. Regression tests with equalized mtimes. | fixed@0c18652 (re-check below) |
| GD-2 | [MINOR] | tools/doctrine_gold.py:161-171 | `check` on a shape-tampered record (e.g. `artifacts` replaced with a string) crashes with a raw TypeError traceback (probe G6) instead of the clean "CHECK FAILED" contract. Exit code is still nonzero via the traceback, so pipelines refuse - but the tool's own exit-code contract (0/1/2, ASCII errors) is broken. | After a schema finding, skip structural checks (or guard types per field) and report findings cleanly. | fixed@0c18652 |
| GD-3 | [MINOR] | tools/doctrine_gold.py:61-63 | "Annotated tags only" (permission matrix row 3) is unenforced: `git rev-list -n 1` resolves lightweight tags happily and `record` succeeds on one (probe G3). | One guard: `git cat-file -t <tag>` must equal `tag`; else StateError naming the policy. | fixed@0c18652 |
| GD-4 | [MINOR] | tools/doctrine_gold.py:87 (record), :140 (check) | The tag string is used in git argv and in path composition BEFORE format validation: `record` with tag `--all` executes `git rev-list -n 1 --all` (read-only, but attacker-influenced argv); `check --tag ../secret` composes an escaping path and reads an arbitrary .json before failing (probe G7 - both end in refusal, nothing written). | Validate the tag against `^v[0-9]+\.[0-9]+\.[0-9]+$` at entry of both commands; prefer `refs/tags/<tag>` in git calls. | fixed@0c18652 |
| GD-5 | [NIT] | tools/doctrine_gold.py:100-106 | `record` hashes artifacts from the current worktree with no warning when HEAD != the tag's commit or the worktree is dirty (probe G8) - a stale/rebuilt dist/ can be bound to an older tag. The ladder assigns artifact provenance to CI, so this is a missing guardrail, not a broken one. | Warn (or require --force) when HEAD != tag commit or `git status --porcelain` is non-empty. | fixed@0c18652 |
| GD-6 | [NIT] | schemas/gold-build.schema.json relpath; tools/doctrine_gold.py:101-106 | Duplicate artifact paths are accepted into one record (probe G5); the relpath pattern permits a POSIX-absolute leading "/" (machine-specific path recorded; `check` on other clones would fail artifact-missing, so it degrades loudly). | Dedupe artifact paths at record time; anchor the pattern against a leading "/". | fixed@0c18652 |

## What holds (verified by executing the 12 shipped tests + probes)

Happy path record->check round-trip; artifact tamper and moved-tag
detection; record tamper caught via the NEXT record's pre-tamper hash;
missing verdict/sign-off refusals leave nothing on disk (G7 confirms no
gold dir after refusal); records immutable (second record for the same
tag refused); empty human-approval statement refused at schema; path
escapes refused; soak "pass"-only enum enforced by design; ASCII output;
exit codes clean on the refusal paths. Standard/template/schema wiring is
coherent (template carries its gate tag; routing row and G6 note added;
plan slices 11-14 recorded; README counts lint-clean). The OPT-IN framing
is explicit, with the "don't let the profile creep into Class S/M"
guardrail - good scope hygiene.

## Delta verdict (v0.4.0)

- [ ] Pass
- [x] **Return to build - REQUEST-CHANGES (delta only).** One MAJOR:
  GD-1 - the rollback ladder's ordering rests on file mtimes that a
  plain clone destroys; wrong-predecessor chains and forged genesis
  records then pass `check` silently. This is the same failure class the
  state-plane verify fixes addressed: an integrity tool whose core
  property fails under normal operation. The fix is contained (walk the
  hash chain instead of trusting timestamps) and everything else - 61
  green tests, refusal paths, tamper detection, schema discipline - is
  in good shape. GD-2..GD-4 should ride along; GD-5/GD-6 author's call.

---

# Delta re-check — v0.4.0 remediation @ 0c18652 — 2026-07-12

**Executed** (real output):

```
$ python tools/doctrine_lint.py        -> doctrine_lint: corpus clean (0)
$ python -m ruff check tools tests     -> All checks passed! (0)
$ python -m unittest discover -s tests -> Ran 70 tests ... OK
```

Every original probe re-run against the reworked `doctrine_gold.py`:

```
R-G1 clone-equalized mtimes:
   chain order (from prev-hash links): v1.9.0 -> v1.10.0 -> v1.11.0
   next promotion v1.12.0 chained to v1.11.0 (the TRUE head); check 0
                                                        -> GD-1 FIXED
R-G2 forged genesis alongside older records, clone-equalized mtimes:
   "gold chain topology: 2 genesis record(s), expected exactly 1"
   check exit 1 for the forged record AND for the legit records - the
   whole ladder fails loudly until repaired (correct fail-closed
   posture)                                             -> GD-1 FIXED
R-G3 lightweight tag: refused ("is commit, not an annotated tag")
                                                        -> GD-3 FIXED
R-G4/G6: duplicate artifact paths refused; "/abs/path.whl",
   "a/../b.whl", backslash path all refused (schema lookahead pattern +
   runtime guard); soak result "fail" still schema-refused
                                                        -> GD-6 FIXED
R-G6b record tampered to artifacts:"not-a-list":
   clean "CHECK FAILED ... schema: $.artifacts: expected array", exit 1,
   no traceback (schema validated FIRST, then stop)     -> GD-2 FIXED
R-G7 tags "--all" and "../secret": StateError from require_tag_format
   in BOTH commands before any git argv or path composition; nothing
   written (no gold dir)                                -> GD-4 FIXED
R-G8: HEAD-not-at-tag warning AND dirty-worktree warning both emitted
   at record time                                       -> GD-5 FIXED
```

Bonus hardening (this commit, verified by probe + the shipped tests):
verdict and sign-offs are now content-pinned (`hashedref` = path+sha256)
- editing a sign-off after promotion fails `check` with "content changed
after promotion"; an empty/whitespace-only verdict file is refused at
record time ("existence is not evidence"). Chain topology errors also
name forks explicitly (two records claiming one predecessor). All nine
new regression tests ran in the 70-green suite.

Notes, no action demanded: the `hashedref` schema change is a breaking
record-format change while `gold_version` stays "1" - acceptable since no
released gold records predate it (remediated within the same review
cycle); the relpath lookahead `(?!.*\.\.)` also rejects benign filenames
containing ".." (e.g. `release..notes.md`) - fail-closed, consistent with
the marker/secret-scan posture.

## Final delta verdict (v0.4.0)

- [x] **Pass - APPROVE.** All six findings (GD-1 MAJOR through GD-6 NIT)
  verified fixed by re-executing the original failing probes: chain
  order now derives solely from prev_gold_sha256 links (single genesis,
  no forks, reachability enforced) and survives clone-equalized mtimes;
  tamper and forgery fail loudly; refusal paths are clean and write
  nothing. 70/70 tests, corpus lint, and ruff all green. The enterprise
  merge/promotion profile is good to land.

---

# Delta review — v0.5.0 packaging/distribution @ 73d6f80 — 2026-07-12

**Reviewer role:** Code Reviewer (fresh pass). **Scope:** installer
(`tools/doctrine_install.py`), MCP server (`tools/doctrine_mcp.py`),
Claude Code plugin (`plugin/` + `.claude-plugin/marketplace.json`),
lint parity checks, `.Doctrine/05-packaging.md`, `pyproject.toml`,
`tests/test_doctrine_packaging.py`.

**Executed** (real output):

```
$ python tools/doctrine_lint.py        -> doctrine_lint: corpus clean (0)
$ python -m ruff check tools tests     -> All checks passed! (0)
$ python -m unittest discover -s tests -> Ran 79 tests ... OK
$ pip wheel --no-deps .                -> doctrineos-0.5.0-py3-none-any.whl
  (5 modules; console_scripts doctrine-{state,lint,gold,mcp,install}
   all resolve to real main() functions; 0 doctrine-law files inside)
plugin.json claims "19 roles, 30 skills": verified 19 + 30 on disk.
Hook one-liner executed under POSIX sh, real cmd.exe (batch + direct),
and PowerShell: all exit 0, hydrate runs; existence guard no-ops in a
repo without the tool.
```

Probes (real output, abridged):

```
FRESH TARGET (installer, then its own printed next step):
  install --tool claude -> 134 files; git init; state init
  python -m unittest discover -s tests
    -> FAILED (failures=1, errors=1)
       ERROR test_current_corpus_passes  (lint crashes: FileNotFoundError
             CHANGELOG.md - raw traceback)
       FAIL  TestMcpServer.test_handshake_list_and_calls (state_status
             on a fresh plane prints "no state plane", test asserts
             "checkpoint seq")
  with a CHANGELOG present: doctrine_lint -> 7 finding(s), 6x
    "plugin parity: ... missing" - plugin/ and .claude-plugin/ are
    source-repo-only and are not installed -> lint fails in EVERY
    consumer repo, so make verify and the --ci workflow are red forever
MCP:
  M1 non-dict JSON lines ([], "str", 123, null): server DIES,
     AttributeError traceback, exit 1
  M2 tools/call with string params or string arguments: server DIES
  M3 state_checkpoint with missing proposal_json -> error says
     "unknown tool: state_checkpoint" (KeyError conflation)
  M4 initialize with protocolVersion "9999-12-31" -> server echoes
     "9999-12-31" (no negotiation)
  M5 unicode tag + 2MB proposal_json: clean isError, server survives
INSTALLER:
  I1 target inside a copied source subtree: rc 0 and the tree GROWS
     unboundedly per rerun (261 -> 392 -> 523 files, consumer nested
     3 deep after 3 runs) - the source==target guard misses containment
  I2 CRLF CLAUDE.md: whole file rewritten to LF by append_lines
     (no-trailing-newline case handled correctly)
```

## Findings (delta v0.5.0)

| # | Sev | Location | Finding | Suggested fix | Resolution |
|---|-----|----------|---------|---------------|------------|
| PD-1 | [MAJOR] | tools/doctrine_lint.py:106 (check_version), :121-159 (check_plugin_parity); tests/test_doctrine_packaging.py:127-132; tools/doctrine_install.py:173-174 | The installed target's out-of-box experience is broken three ways: (a) `doctrine_lint` crashes with a raw FileNotFoundError when the target has no CHANGELOG.md; (b) with one present, `check_plugin_parity` fails every consumer repo because `plugin/` and `.claude-plugin/` are source-repo artifacts the installer does not (and should not) ship; (c) the copied test suite is red (lint corpus test errors; the MCP test asserts "checkpoint seq" against a plane with no checkpoints). Net: the installer's own printed next step (`make verify`) and the `--ci` workflow fail in every fresh install. | Make the lint consumer-aware (skip plugin-parity and CHANGELOG checks when the artifacts are absent, or ship a consumer profile flag in the copied Makefile/workflow); check_version treats a missing CHANGELOG as a finding, not a crash; the MCP test accepts the fresh-plane message; add an install-into-temp-repo smoke test that runs the target's verify. | open |
| PD-2 | [MAJOR] | tools/doctrine_mcp.py:136-167 (handle), :170-186 (serve) | The server's stated contract is "never crashes on a bad call", yet any non-dict JSON line - including a JSON-RPC batch array, which older MCP protocol revisions used - kills the process with an AttributeError (probe M1), as does `tools/call` with a non-dict `params` or `arguments` (M2). One malformed line ends the session for the connected agent. | Type-guard message/params/arguments (`isinstance(..., dict)`) returning -32600 invalid request; belt-and-braces: wrap `handle()` in try/except returning -32603 internal error. Regression tests per shape. | open |
| PD-3 | [MINOR] | tools/doctrine_mcp.py:154-159, :139-144 | (a) A missing required tool argument surfaces as "unknown tool: state_checkpoint" - the `except KeyError` around `call_tool` conflates dispatch misses with `args["proposal_json"]` (M3). (b) `initialize` echoes whatever protocolVersion the client sent, including "9999-12-31" (M4) - no negotiation; combined with PD-2, honestly claiming an old batch-capable revision while crashing on batches. | Distinguish the KeyErrors (validate required args explicitly, -32602 with the real message); return the requested version only when supported, else PROTOCOL_VERSION. | open |
| PD-4 | [MINOR] | tools/doctrine_install.py:114-115 | The source==target guard misses containment: a target inside a copied source subtree installs rc 0 and each rerun nests another copy (probe I1: 261 -> 392 -> 523 files) - the advertised idempotency silently fails. | Refuse when target is inside source or source inside target (resolve() + parents check, same as safe_repo_path). | open |
| PD-5 | [MINOR] | tools/doctrine_install.py:92-104 (append_lines) | CRLF CLAUDE.md/.gitignore/brief are rewritten whole-file to LF on append (probe I2) - the same outside-content mutation class fixed for `emit_agents_block` in the v0.3.0 delta (D-2), regressed in the installer. | Byte-splice, or detect and preserve the file's newline style (the emit_agents_block fix is the in-repo pattern to copy). | open |
| PD-6 | [MINOR] | pyproject.toml:7; plugin/.claude-plugin/plugin.json:3; tools/doctrine_mcp.py:34; .Doctrine.md:1 | The delta's own versioning rule (05-packaging.md: manifests bump "with the .Doctrine.md header in the same commit") is already violated: manifests + SERVER_INFO say 0.5.0 while .Doctrine.md says v0.4.0 - and nothing enforces it (corpus lint only checks .Doctrine.md vs CHANGELOG). | Add manifest-version sync (pyproject, plugin.json, marketplace, SERVER_INFO) to doctrine_lint; align the versions at G6. | open |
| PD-7 | [NIT] | pyproject.toml; repo root; doctrine_lint parity messages | Wheel contains zero law files, so a pipx-installed `doctrine-install` has nothing to install without --source at a checkout (the error message is clear; 05-packaging.md does not say it). No LICENSE file at the root while pyproject declares MIT - matters at the human-gated publish step. Parity findings print backslash paths on Windows ("plugin\agents"). | Document the wheel limitation (or package the law as data files); add LICENSE; as_posix() the finding paths. | open |

## What holds (verified by execution)

In the source repo everything is green: 79/79 tests, corpus lint, ruff.
The installer's normal-use semantics all verified via the shipped tests
plus probes: byte-exact copies, skip-if-identical, differing files listed
and exit 1 without --force, CLAUDE.md/.gitignore/brief appended never
replaced, existing AGENTS.md untouched, unknown tools and source==target
refused, --enterprise seeds the brief, no-trailing-newline appends safe.
The MCP server's happy paths are solid and were exercised over a REAL
stdio subprocess (shipped test + my probes): handshake, tools/list, calls
with isError semantics, unknown tool/method errors, unicode arguments,
and a 2 MB proposal bounded by the state-file cap - stdout stayed
protocol-only throughout. The plugin hook one-liner ran correctly under
POSIX sh, real cmd.exe, and PowerShell, and its existence guard no-ops
cleanly outside doctrine repos. Plugin/agents byte-parity is lint-enforced
and currently exact; manifest counts ("19 roles, 30 skills") verified
against the corpus. The wheel builds clean and every console script
resolves. 05-packaging.md's install matrix matches what the code does.

## Delta verdict (v0.5.0)

- [ ] Pass
- [x] **Return to build - REQUEST-CHANGES (delta only).** Two MAJORs,
  both on the delta's core promises: PD-1 - the installed repo's own
  verify gate (the installer's printed next step, and the --ci workflow)
  fails in every fresh target because source-repo-only lint checks and
  test assumptions ship to consumers; PD-2 - the MCP server dies on a
  single malformed JSON line despite its "never crashes" contract.
  Both fixes are contained. PD-3..PD-6 should ride along; PD-7 is
  author's call. The rest of the delta is well-built and the probe
  surface (hooks, wheel, parity, unicode, big inputs) is clean.

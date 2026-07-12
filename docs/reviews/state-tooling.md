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
| 1 | [BLOCKER] | tools/doctrine_state.py:323-334 vs :354 | Decision entries are appended to `DECISIONS.ndjson` (permanent, append-only, "never rewritten") *before* the checkpoint/control block is validated. A proposal with a valid distillate carrying `decision_ref` claims but an invalid `control` is rejected — yet its decisions persist forever; the next valid checkpoint hashes the polluted log and `verify` passes (probe P1). Violates STATE.md step 2 (validator checks **both** schema instances before write). | Validate both instances first; move all disk mutations, including NDJSON appends, into the write phase after both `validate()` calls succeed. Regression test: invalid control + decision_ref claim leaves the decisions file untouched. | open |
| 2 | [MAJOR] | tools/doctrine_state.py:378-384 | `verify` exits 0 ("nothing to verify") when `checkpoints/` is emptied while `checkpoint.json` exists (probe P3). Full-history wipe is exactly the tamper class `verify` exists to catch; brief AC says "tampered chain → verify fails". | Fail when `checkpoint.json` exists with no history. | open |
| 3 | [MAJOR] | tools/doctrine_state.py:407-426 | `verify` re-hashes decisions, distillate, intents — but never `graphify-out/graph.json`, though `state_index.graph.sha256` names it. STATE.md: "re-hashing the files named in `state_index`". Tampered graph → verify OK (probe P8). | When `state_index.graph.sha256` is present, re-hash the graph file (missing file = failure too). | open |
| 4 | [MAJOR] | tools/doctrine_state.py:440-444, 519-540, 546-557, 560-574 | HYDRATION.md degrade rules are not implemented — every section is blunt tail-truncation via `_clip`. On distillate overflow the clip keeps `learned` 12/12 and drops dead_ends 7/8 plus all open_threads (probe H2) — the exact **inverse** of the degrade-to spec ("dead_ends + open_threads only"; dead_ends is "the anti-thought-drift payload"). Decisions ("ids + one-line titles"), graph ("god nodes + EXTRACTED edges"), effects ("count + most-recent entry" — currently only ever a count) degrades also absent. Plan step 3 promised degrade tests; none exist. | Implement per-section degrade-to forms, truncating only after degrading; add an overflow test per section. | open |
| 5 | [MAJOR] | tools/doctrine_state.py:487 | Section 1 (invariants) is a never-trimmed section, yet `_clip` truncates it at the 800-token budget and the clipped flag is discarded (`text, _ = _clip(...)`) — silently cut and absent from `trimmed[]` (probe H1: last line gone, `trimmed == []`). Violates both "earlier sections are never trimmed" and "Every trim is recorded in the bundle header". | Never clip sections 1-2; oversized sources deserve a loud warning, not a silent cut. At minimum record the trim. | open |
| 6 | [MAJOR] | tools/doctrine_state.py:168 (`.doctrine`); spec STATE.md layout | On case-insensitive filesystems (Windows, default macOS) `.doctrine/` collides with the corpus dir `.Doctrine/`: probe P5 shows the state plane physically created under `.Doctrine\state\`, and git records `.Doctrine/state/checkpoint.json`. A plane initialized and committed on Windows is invisible to the tool on a Linux clone (`.doctrine/state` absent there). Partly spec-level naming — needs a human decision (rename one dir, or detect/normalize in `Plane.__init__`). | Short-term: detect an existing `.Doctrine` sibling and refuse/warn on init; long-term: non-colliding names in STATE.md. Escalate to the human. | open |
| 7 | [MAJOR] | tools/doctrine_state.py:616 | The "nothing to prune (N ≤ keep K)" message contains U+2264; on stock Windows any piped/redirected invocation gets cp1252 stdout and **crashes with UnicodeEncodeError** (probe P2 — the probe process died on it). Brief constraint: Windows + POSIX. | ASCII-only CLI messages, or reconfigure stdout/stderr with errors="replace" at entry; audit remaining non-ASCII output. | open |
| 8 | [MAJOR] | tools/doctrine_state.py:247-257 | `_graph_index` fabricates freshness: a `graph.json` without `built_at_commit` (or with undecodable content — errors swallowed) is stamped `built_at_commit = <current HEAD>` (probe P6). Defeats STATE.md failure-mode defense #2 ("stale-as-fresh") for the one artifact whose staleness rule is `built_at_commit != HEAD`, and writes invented provenance into a hash-chained artifact. The schema permits null. | Use null when absent/unreadable; treat unknown build commit as stale at hydration; warn instead of swallowing decode errors. | open |
| 9 | [MINOR] | tools/doctrine_state.py:378-381 vs :219-221 | `verify` globs `checkpoints/*.json` then parses the filename seq with int() — a stray non-seq file (e.g. `notes.json`) crashes it with a raw ValueError (probe P4). `_distillate_files` filters filenames with a digit-prefix regex; verify does not. | Apply the same filename filter; flag unexpected files as findings rather than crashing. | open |
| 10 | [MINOR] | tools/doctrine_state.py:300-301, 613-616 | `--keep` unvalidated: `checkpoint --keep 0` silently behaves as keep=1; `prune --keep 0` prunes nothing and prints the false claim "N ≤ keep 0"; negatives accepted (checkpoint keep=-3 prunes everything; prune keep=-1 no-ops). No tests. | Reject keep < 1 at argparse; test the boundary. | open |
| 11 | [MINOR] | tools/doctrine_state.py:260-278, 311-312 | Dead-end cap drop order contradicts its own documentation: docstring and runtime note say oldest dropped first, but pruned files are iterated oldest-first into the merged list, so the **newest** pruned negatives drop at the cap (probe: kept OLD-0..4, dropped NEWER-1..4). Also `except json.JSONDecodeError: continue` silently discards a corrupt pruned distillate, so "hard-won negatives outlive the prune" fails without a word. | Order merged candidates by recency; warn when a pruned distillate fails to parse. | open |
| 12 | [MINOR] | tools/doctrine_state.py:283, 296, 389, 472 | Failure paths unhandled at the CLI boundary: missing `--proposal` file → raw FileNotFoundError traceback (confirmed); corrupt JSON in state files → JSONDecodeError traceback in verify/hydrate/status; running in a repo without `.Doctrine/state-plane/schemas/` (i.e. any *target* repo per STATE.md layout) → FileNotFoundError. Documented exit code 2 not produced. | Catch OSError/JSONDecodeError in `main()`, one-line error, exit 2. Decide and document where target repos get schemas (embed as fallback?). | open |
| 13 | [MINOR] | tools/doctrine_state.py:490-497, 595-600 | Staleness gaps: a checkpoint `at_commit` behind HEAD gets no STALE marker and no `stale[]` entry for the control section (probe H3), though STATE.md flags any control reference behind HEAD; the bundle header `at_commit` is the checkpoint commit, not generation HEAD. The intent-staleness rule ("references paths absent at HEAD") is reduced to an at_commit compare. | Flag control staleness; carry HEAD in the header. | open |
| 14 | [MINOR] | tools/doctrine_state.py:584-593 | `hydrate --check` compiles twice **in one process**. PYTHONHASHSEED is fixed per process, so cross-process nondeterminism (set-iteration order reaching output — the classic cause) cannot be caught. Today no set ordering feeds output text, so the pass is honest, but the gate is weaker than HYDRATION.md intends. | Second compile in a subprocess, or hash across two CLI invocations in the test. | open |
| 15 | [MINOR] | tools/doctrine_state.py:54, 61, 81; workflow | languages/python.md: public functions must be fully hinted — `canonical_bytes(obj)`, `canonical_line(obj)`, `validate(...)` are unhinted and form the exported surface (imported by doctrine_lint and tests). coding-standards.md: formatting "enforced in CI" — no ruff/format step (ruff as dev-time CI tooling would not violate the stdlib-only *runtime* constraint). | Add hints; add ruff to CI. | open |
| 16 | [MINOR] | tools/doctrine_state.py (checkpoint); STATE.md step 4 | Protocol step 4 (git commit "state: checkpoint N", or charter-routed staged-for-human) is silently unimplemented — no flag, no output noting the un-committed state. dos-and-donts.md: narrowed scope is reported scope. | Implement a --commit/staged behavior or state the omission in docs and checkpoint output. | open |
| 17 | [NIT] | tools/doctrine_lint.py:138-139; tools/doctrine_state.py:134-136, 685 | CLI asymmetry (doctrine_state: `--root` flag + argparse; doctrine_lint: bare positional, no --help); the items-keyword check sits inside the per-item loop; unreachable `return 2` fallthrough in `main`. | Author's call. | open |
| 18 | [NIT] | .github/workflows/doctrine.yml | Actions pinned by major tag, not SHA; no least-privilege `permissions:` block. Security-reviewer's lane — noting for the fan-out. | Pin by SHA; add permissions. | open |
| 19 | [NIT] | tests/test_doctrine_state.py:79-82, 216-217 | `test_stable` compares two serializations in one process (same class as finding 14); `cmd_hydrate` stderr leaks into test output. | Author's call. | open |

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

# Retrospective — state-tooling (v0.2.0) · 2026-07-12
<!-- G7 artifact. Filed per templates/retrospective.md. Author: Project Reviewer. -->

## Facts (no interpretation yet)

**Shipped:** `tools/doctrine_state.py` (state-plane CLI: init / checkpoint /
verify / hydrate / prune / status), `tools/doctrine_lint.py` (8-check corpus
gate), 38 unit tests, Makefile, GitHub Actions workflow; state-plane spec
amended to 0.2.0 (state root `.doctrine-state/`, `$defs/intent_id` traversal
defense, examples re-canonicalized). Tagged `v0.2.0` at `8d9a560`.

**Duration / gates walked:** one day (2026-07-12), full Class-L arc
G0→G7 — the first complete dogfood of the doctrine's own pipeline on real
code. Commits: `2e19c85` (G3 build, 21 tests green) → `5382362` (G4/G5
reports) → `e353bb9` (remediation + 17 regression tests) → `8d9a560`
(re-review residuals, changelog, tag) → `c89259d` (state checkpoint 0).

**Defects escaped past each gate:**
- **G3 → G4/G5:** 26 distinct defects/findings (36 raw rows across the three
  verifier reports, deduplicated) escaped the builder's own 21-test suite.
  Round-1 verdicts: code review **REQUEST-CHANGES** (1 BLOCKER, 7 MAJOR,
  8 MINOR, 3 NIT — `docs/reviews/state-tooling.md`), security **VETO**
  (2 blockers incl. a reproduced path-traversal exploit —
  `docs/qa/state-tooling-security.md`), QA **FAIL** (state-corrupting
  ordering bug + 7 — `docs/qa/state-tooling.md`).
- **Round 2 (re-review of `e353bb9`):** 3 residuals (R-1 raw traceback on
  non-UTF-8 effects file; R-2 header at_commit NIT; R-3 finding-15
  "claimed fixed but is not"). R-1 and R-3 landed at `8d9a560` before the
  tag; R-2 dispositioned author's-call in writing.
- **Past release:** none known as of this retro.

**Verified this session at HEAD (`c89259d`), real output:**
```
$ python tools/doctrine_lint.py
doctrine_lint: corpus clean        (exit 0)
$ python -m unittest discover -s tests
Ran 38 tests in 10.141s / OK
$ python -m ruff check tools tests
All checks passed!
```

**In flight, not part of v0.2.0:** an uncommitted diff to
`.github/workflows/doctrine.yml` adds a `windows-latest` matrix leg and
SHA-pins both actions — it implements the H-2 accept-with-reason condition
and two of the checkpoint-0 distillate `next_actions`. Noting it here so
the deferral does not silently become permanent.

## What worked (keep doing)

- **The fresh-context verifier fan-out.** Three verifiers (code reviewer,
  security reviewer, QA), no author narrative, judging only what was on
  disk, found 26 distinct defects in code that carried 21 green tests —
  including a reproduced exploit (`../TOPSECRET.intent.json` content
  exfiltrated into the hydration bundle) and a state-corruption BLOCKER on
  the tool's *everyday* rejection path. Separation of duties worked
  mechanically, not rhetorically.
- **Regression test per finding.** 17 tests added at `e353bb9`, each named
  for its finding (`test_rejected_proposal_leaves_no_trace`,
  `test_traversal_intent_rejected_at_checkpoint`, ...). Suite 21→38; all
  still green at HEAD, re-executed this session.
- **Re-review by the original exploit.** Every round-2 verification re-ran
  the exact round-1 probe (DECISIONS.ndjson byte-hash before/after a
  rejection; the traversal repro against all three defense layers). This
  discipline is what caught R-3 — a finding *reported* fixed that was not.
  Re-reading a diff would have missed it; re-executing did not.
- **Executable acceptance criteria.** Every AC in `docs/brief.md` was a
  command with an observable result, so G4, G5, and the re-test could all
  verify by running, not by reading.
- **Escalating spec defects instead of patching around them.** The
  `.doctrine/`-vs-`.Doctrine/` case collision was routed to a human
  decision and became spec 0.2.0 (`.doctrine-state/`), not a tool-side hack.
- **The lint gate paid for itself on first run** — it caught real corpus
  drift (README claimed 10 subagents; the filesystem had 14).

## What failed or hurt

- **The builder's 21-test suite validated the builder's model, not the
  artifact.** Every escape lived in failure paths, adversarial input,
  degrade behavior, or platform behavior; zero in the happy path. The
  code-review scope check said it precisely: the findings sit "exactly
  where a state-integrity tool earns its keep."
- **Rejection-path tests asserted exit codes, not absence of side
  effects.** The BLOCKER (decisions-log corruption) lived exactly in that
  gap: the rejection tests passed while the rejection mutated disk.
- **No build-time threat sketch.** skills/security.md's "threat-sketch each
  L-class feature" was first executed at G5 by the security reviewer —
  where it immediately produced both veto findings. Three lines at G2 were
  skipped and bought a full remediation round.
- **CI was green on the wrong platform.** Ubuntu-only CI against a brief
  that says "Windows + POSIX"; the cp1252 pipe crash (QA Bug #2) was
  structurally invisible to it.
- **A remediation claim overshot reality.** Finding 15 (type hints + ruff)
  was recorded fixed at `e353bb9` and was not (R-3). Caught by re-review,
  corrected at `8d9a560` — but it is a near-miss on the cardinal honesty
  rules and earned its own amendment below.
- **The spec seeded three of the defects.** Schema with no charset on
  intent ids; shipped examples violating their own canonicalization rule;
  the `.doctrine/` naming. The tool faithfully implemented spec bugs —
  implementing a spec is also reviewing it.
- Hygiene: `__pycache__/` committed in the G3 build commit (purged at
  `e353bb9`, `.gitignore` fixed at `8d9a560`).

## Root causes (5-whys on every escaped defect)

### Defect A — decisions-log append-before-validate corruption
(review #1 BLOCKER = QA Bug #1: a schema-rejected proposal permanently
pollutes `DECISIONS.ndjson`; the next valid checkpoint hashes the polluted
log and `verify` goes blind to it.)

1. **Why did a rejected proposal corrupt the log?** `cmd_checkpoint`
   appended decision lines (doctrine_state.py:323-334) *before* validating
   the checkpoint/control instance (line 354); rejection exited after the
   append, and append-only logs have no tool-supported repair.
2. **Why was the append placed before validation?** The checkpoint's
   `state_index.decisions_sha256` must hash the post-append file. Appending
   to disk and re-hashing the file was the path of least resistance versus
   computing the prospective bytes in memory. The code even carried a
   `# write phase (all validations passed)` comment — the author believed
   the ordering was right because *one* of the two validations (distillate)
   had already run.
3. **Why didn't the 21-test suite catch it?** The rejection tests asserted
   the exit code and that no checkpoint/distillate file appeared — none
   asserted the decisions log unchanged, and none used the cross-product
   input that triggers the bug (valid distillate carrying `decision_ref`
   claims + invalid control).
4. **Why were the rejection assertions that narrow?** Same-context testing:
   the tests checked the failure modes the author had imagined ("rejection
   happens") rather than the invariant STATE.md actually states (validator
   checks both instances before write, therefore a rejection leaves zero
   mutations). Nothing in the doctrine required a no-side-effects assertion
   per rejection path.
5. **Why did no such requirement exist?** Doctrine gap: skills/testing.md
   demands failure-path tests but never says what a failure-path test must
   *assert*; and no rule anywhere states transactional write discipline for
   append-only / hash-chained artifacts.

**Root:** doctrine gap (amendments 1, 2) compounded by author-context
blindness (mitigated only by the fresh-context fan-out — keep it).

### Defect B — path traversal via intent ids
(security P-1, reproduced: `../TOPSECRET` in `active_intents` read a file
outside the plane into the hydration bundle destined for agent context.)

1. **Why did the hostile id escape the plane?** Intent ids were
   interpolated into `intent/{id}.intent.json` with no charset constraint
   and no `resolve()` + prefix-check, in both hydrate and verify.
2. **Why was there no validation on the ids?** The builder treated schema
   validation as the entire input boundary, and the spec's schema
   constrained `active_intents` items as bare strings — the tool faithfully
   inherited the spec's gap. Ids were modeled as opaque labels, not as
   path components.
3. **Why were they modeled as labels?** The implicit threat model was
   "local tool, operator-authored proposal." Committed state artifacts —
   deliverable by a malicious PR and auto-read by the SessionStart hydrate
   hook per HYDRATION.md — were never enumerated as an attacker entry
   point by the builder.
4. **Why didn't the 21 tests probe it?** Every test intent id was
   well-formed (`t-100`...). The suite diligently tested the caps the
   author knew about (maxItems/maxLength at limit and limit+1) but no
   injection class — you cannot write a test for a threat you have not
   enumerated.
5. **Why was no threat enumerated at build time?** skills/security.md
   positions "path: canonicalize + prefix-check" inside the *G5* standing
   audit, and the threat sketch is an ungated "Do." Nothing at G2/G3 forces
   the builder to enumerate entry points before code exists.

**Root:** doctrine gap (amendments 3, 4): identifier-that-becomes-a-path
was not a named trust boundary, and threat modeling was review-time
ceremony instead of a gated plan artifact.

### Shared meta-root — how do 21 green tests miss 26 defects?
A test suite written by the context that wrote the code verifies the
author's model of the code; model and code share blind spots by
construction. The escapes clustered precisely in the unimagined classes:
cross-products of valid+invalid input, adversarial identifiers, encoding
of the *terminal* rather than the files, a filesystem that folds case.
The fan-out is currently the only mechanism attacking this class; the
amendments below move part of the attack earlier (named invariants,
gated threat sketch, side-effect assertions) without pretending author
self-testing can replace independent verification.

## Doctrine & tooling amendments (concrete, or it didn't happen)

| # | Amendment | Target file / CI check | Class-S change filed? |
|---|-----------|------------------------|-----------------------|
| 1 | New bullet under **Do**: "Treat multi-artifact writes as transactions: for append-only or hash-chained artifacts, compute the new content and its hashes prospectively in memory and touch disk only after **all** validation has passed. A rejected input leaves zero mutations." | `.Doctrine/skills/backend.md` | proposed — not yet filed |
| 2 | Extend the failure-path **Do** (and checklist): "A failure-path test asserts the *absence of side effects* — no files written or mutated, no partial state — not just the error code. Include cross-products of valid+invalid input parts and adversarial classes (traversal sequences, deep/huge documents), not only schema limits." | `.Doctrine/skills/testing.md` | proposed — not yet filed |
| 3 | Extend audit item 2 (Injection), path clause: "any identifier interpolated into a filesystem path — including ids from your own config/state artifacts — is an injection surface: constrain to an explicit charset at parse **and** `resolve()`+prefix-check at use." | `.Doctrine/skills/security.md` | proposed — not yet filed |
| 4 | Add a required **## Threat sketch** section (assets / entry points / worst plausible abuse — three lines) to the plan template, mandatory for Class L; G2 does not exit without it. | `.Doctrine/templates/implementation-plan.md` | proposed — not yet filed |
| 5 | New bullet under **Errors**: "CLI/terminal output stays ASCII-safe (or reconfigure stdout/stderr with `errors='replace'` at entry): Windows pipes default to cp1252 and *crash* on stray Unicode punctuation even when all file I/O is correctly UTF-8." | `.Doctrine/standards/languages/python.md` | proposed — not yet filed |
| 6 | Generalize the OS-matrix rule out of the Rust bullet: "If the brief names an OS as a constraint, CI runs a matrix leg on it; a unit test emulating the environment is a stopgap, not a substitute." (The in-flight workflow diff adding `windows-latest` implements this for this repo.) | `.Doctrine/skills/cicd.md` | proposed — not yet filed |
| 7 | New repo-layout bullet: "New top-level directories (especially dotted ones) must differ from existing ones by more than letter case — case-insensitive filesystems (Windows, default macOS) silently merge `.doctrine/` into `.Doctrine/`, and git records the merged path." | `.Doctrine/skills/repo-devops.md` | proposed — not yet filed |
| 8 | New §7 rule: "A remediation report marks a finding fixed only with the re-executed original probe/command referenced per finding; 'fixed' from memory of intent is a §1 honesty violation." (Evidence: finding 15 claimed fixed at e353bb9, disproven by re-review R-3.) | `.Doctrine/standards/dos-and-donts.md` | proposed — not yet filed |

All eight are Class-S doctrine edits; none is filed by this retro (the
Project Reviewer does not edit doctrine). Route each through the normal
S-class path with this file as the evidence link.

## Honest negative findings worth remembering

Recorded so they are not re-tried from optimism (sources: session
distillate `.doctrine-state/distillates/0-81916913af14.json` dead_ends +
the G4/G5 reports):

- **`json.dumps` with default separators is not canonical-safe:** it emits
  a trailing space before every newline under `indent=`. The pack's own
  shipped examples carried this violation of its own no-trailing-whitespace
  rule for two releases. Use explicit `separators`.
- **`list[:-(keep-1)]` to select prune victims:** `[:-0]` is the empty
  slice, so `keep=1` pruned nothing. Compute cut indexes explicitly.
- **`.doctrine/` as a state root alongside `.Doctrine/`:** dead on arrival
  on case-insensitive filesystems — the dirs merge, git records the merged
  path, and the state is invisible after a Windows-to-Linux clone. Renamed
  `.doctrine-state/` (spec 0.2.0).
- **`hydrate --check` double-compiling in one process** cannot catch
  cross-process nondeterminism (PYTHONHASHSEED is fixed per process) — the
  gate looked stronger than it was. Documented as a disposition; the honest
  form is a second compile in a subprocess.
- **Test count is not a robustness signal.** "21 green tests" preceded 26
  escaped defects. Cite *which failure classes the suite attacks*, never
  the count.
- **"CI green" on the wrong platform is not green.** Ubuntu-only CI passed
  while the tool crashed on a supported platform's default pipe encoding.
- **Marking a finding fixed from intent instead of execution** (finding 15
  → R-3): survived one remediation commit and one report; did not survive
  a re-review that re-executes. Only the re-executed probe counts.
- **Guessing GitHub Actions SHAs offline is worse than tag pins** — a wrong
  or nonexistent SHA bricks the workflow. Deferred with recorded rationale
  (H-2 accept-with-reason); conversion now in flight with real SHAs.

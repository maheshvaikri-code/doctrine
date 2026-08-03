# QA Report — Enterprise Control Plane (v0.7.0)
<!-- G5 artifact. QA Engineer + Security Reviewer (see independence caveat). -->

**Under test:** the five work packages in `docs/plans/enterprise-control-plane.md`.
**Method:** execute, don't inspect. Every claim below is a command that ran on
this machine; the output is pasted, not summarized.

## Independence caveat

Same disclosure as G4: this session could not dispatch fresh-context verifier
subagents, so QA was executed by the author. Adversarial *execution* is real
here — the reproductions, the pre-fix/post-fix comparison, and the frozen-tree
runs are genuine evidence — but adversarial *imagination* is not independent.
Run `/qa` from a fresh session before release.

## 1. The full gate suite, on a frozen tree

The tree was frozen for this run: no file was edited while it executed. (Two
earlier runs were discarded precisely because they were not — a suite that
reads source from disk is non-deterministic under concurrent edits, and
reporting either result would have been false evidence.)

```
HEAD=9f42611  tree-frozen: no edits during this run
=== lint: PASS

=== ruff: C:\Program Files\Python312\python.exe -m ruff check tools tests
=== ruff: PASS

=== tests: C:\Program Files\Python312\python.exe -m unittest discover -s tests
=== tests: PASS

=== state: C:\Program Files\Python312\python.exe tools/doctrine_state.py verify
=== state: PASS

VERIFY OK: 4 gate(s) green
```

## 2. The flake, closed

Acceptance criterion: the bridge suite stops failing intermittently.
Baseline before the fix: **3 failures in 8 full-suite runs** (~1 in 6), with
the same error each time:

```
ConnectionAbortedError: [WinError 10053] An established connection was
aborted by the software in your host machine
```

Deterministic reproduction (headers, pause, late body), before the fix:

```
{'ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine': 10}
```

Same reproduction, after the fix:

```
{'HTTP/1.0 415 Unsupported Media Type': 10}
```

The reproduction was then run against the **pre-fix module** as a regression
test, and failed with the original error — the test earns its place:

```
FAIL: test_early_rejection_answers_a_late_arriving_body
  File "tests\test_doctrine_dashboard.py", line 366
    chunk = sock.recv(4096)
ConnectionAbortedError: [WinError 10053] ...
Ran 1 test in 0.762s
FAILED (errors=1)
```

Five consecutive full-suite runs on the frozen tree:

```
Ran 253 tests in 45.718s
OK
Ran 253 tests in 47.094s
OK
Ran 253 tests in 46.646s
OK
Ran 253 tests in 46.724s
OK
Ran 253 tests in 47.309s
OK
```

**Verdict: PASS.** 0 failures in 5 runs against a 3-in-8 baseline. Five runs
cannot prove the absence of a rare race, but the mechanism is removed at its
cause and the reproduction that provoked it is now a permanent guard.

## 3. The guard, exercised against this repository

Not a unit test — the real CLI, real payloads, run in this repo:

```
secret in a new file   -> DENY: Doctrine non-negotiable #2 (never commit secrets): this content contains what looks like GitHub ...
gold record edit       -> DENY: Doctrine: 'docs/releases/gold/v1.0.0.json' is protected - gold records are immutable (a correcti...
force push             -> ASK: Doctrine section 5: this is force-push - an irreversible or external action the human decides, n...
skip a test            -> ASK: Doctrine non-negotiable #4 (never skip or weaken a failing test to go green): this edit adds a s...
ordinary edit          -> (silent: normal permission flow)
ordinary command       -> (silent: normal permission flow)
```

Both halves matter: the four rules fire, and ordinary work passes untouched.

**Live evidence beyond the harness.** The guard was wired into this repo's own
`.claude/settings.json` during construction, so it judged its author. It
denied two real edits — writing its own test file, and writing the G4 review —
and both denials were false positives in its secret pattern (findings 4 and 5
in the review). It also correctly refused a convenient test fixture that
looked like a live credential; the fixture was assembled from fragments rather
than the policy widened.

Failure-path coverage (30 guard tests): unparseable payload denies; empty
payload stays silent; a malformed policy file is ignored rather than obeyed; a
policy of the wrong shape is ignored; a path outside the repo does not crash;
read-only tools are never judged; reading a protected file is always allowed.

## 4. Attestation

- Unsigned tag → recorded honestly as `{"signed": false, "signer": null,
  "key": null}` rather than omitted.
- `record --require-signature` on an unsigned tag → refuses, and **writes
  nothing** (asserted: the gold directory does not exist afterwards).
- `check --require-signature` → exit 1 where plain `check` exits 0.
- A record claiming a signature whose tag no longer verifies → exit 1.
- A record with `attestation` deleted (the v0.6.x shape) → still valid.
- Parser fixtures: GPG status lines, git's ssh-signing text, and three
  malformed/hostile inputs that must never be read as signed.

**Untested, stated plainly:** no signing key is configured on this machine, so
the *end-to-end signed* path has never executed. Signature parsing is tested
against git's output shapes only. The parser fails closed by construction, so
the untested direction can under-report a signature but cannot invent one.

## 5. Fleet view

16 tests cover current / behind / ahead / modified / incomplete drift,
state posture, dirty worktrees, release distance, gold counts, discovery,
config, JSON output, and malformed input. The load-bearing one hashes every
file in the inspected repo before and after a `status` call and asserts the
digest is unchanged — read-only is a property, not a promise.

Run against the real repository:

```
source: D:/Doctrine/Doctrine-System (v0.7.0)
REPO             DOCTRINE  DRIFT    STATE   WORKTREE  RELEASE
---------------  --------  -------  ------  --------  -----------
Doctrine-System  0.7.0     current  seq 28  dirty     v0.6.46 +49
```

## 6. CI parity

Each provider's file lands at its canonical path and contains the gate
sequence (`test_ci_wiring_lands_at_each_providers_canonical_path`); an unknown
provider is refused before any write
(`test_an_unknown_ci_provider_is_refused_before_any_write`).

**Untested, stated plainly:** the GitLab and Azure pipelines have never
executed on their platforms — no such runner is available here. They are
verified as content and placement, not as green pipelines.

## Verdict

**PASS with two stated gaps** (end-to-end signed promotion; CI templates
unexecuted on their platforms) and one process caveat (QA was not
independent). No acceptance criterion in the brief is unmet. Nothing was
weakened to go green.

Not signed off for release: the annotated tag is §5, awaiting the human.

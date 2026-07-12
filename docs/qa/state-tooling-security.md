# Security Review - Doctrine State Tooling (v0.2.0)

Reviewer: Security Reviewer (fresh-context verifier)
Date: 2026-07-12
Scope: tools/doctrine_state.py, tools/doctrine_lint.py, tests/test_doctrine_state.py,
tests/test_doctrine_lint.py, Makefile, .github/workflows/doctrine.yml
Brief: docs/brief.md | Plan: docs/plans/state-tooling.md
Role card: .Doctrine/roles/security-reviewer.md | Loads: skills/security.md, standards/dependency-policy.md

Threat sketch (assets / entry points / worst abuse):
- Assets: the committed state plane (checkpoint chain, distillates, decisions.ndjson),
  the hydration bundle injected into an agent context, the CI GITHUB_TOKEN.
- Entry points: the --proposal file (operator), and every committed state-plane
  artifact read back by verify/hydrate/status (attacker path = malicious commit/PR,
  auto-delivered by the SessionStart auto-hydrate hook described in HYDRATION.md).
- Worst plausible abuse: crafted checkpoint content steers filesystem reads into the
  agent context (disclosure + prompt-injection); CI token abused by a fork PR.

Evidence base: full suite run (21 passed), lint clean, plus five targeted
reproductions below. All commands run on Python 3.12.7 / git 2.50.1 / Windows 11.

---

## 6-point audit sweep

### 1. Secrets
- Static scan of all six in-scope files for key/token/private-key/bearer/AWS/Slack
  shapes: 0 hits.
- No outgoing git history to scan (repo root is not a git repo in this environment).
- Error output: main() prints [git failed: exc.stderr] - git stderr only, carries no
  application secret. Acceptable.
- GUIDANCE RISK (finding S-1): per STATE.md [everything except local/ is committed],
  the distillate and decisions.ndjson artifacts are committed. The distillate schema
  bounds field lengths but never scans claim/evidence/dead_end/next_action/open_thread
  text for secrets. A model that writes a secret into a claim commits it to permanent
  history, and hydrate re-embeds it into agent context.
- Result: clean for hardcoded secrets; S-1 is a guidance/process gap.

### 2. Input boundaries / injection
- Command injection: git is invoked as an exec-array subprocess.run([git, star-args],
  cwd=repo) with shell unset and only hardcoded literal verbs (rev-parse/HEAD,
  status/--porcelain). No string-built commands. PASS.
- Windows cwd exe-hijack (tested): planting git.bat and then git.exe in the untrusted
  repo root did NOT hijack the call - Python resolves the executable against the parent
  PATH before applying the child cwd (real git ran, exit 128). Not exploitable here;
  minor hardening note H-1.
- Path traversal (finding P-1, REPRODUCED): active_intents values and intent
  identifiers flow unvalidated into the path (plane.intents / intent + .intent.json) in
  build_bundle_body (hydrate) and cmd_verify. The schema constrains active_intents
  items and state_index.intents keys to bare strings with NO charset/pattern. A
  ../TOPSECRET value read ../TOPSECRET.intent.json from outside the intents directory
  and copied its title/acceptance_criteria into the bundle. Violates skills/security.md
  (path: canonicalize + prefix-check).
- Trust boundary (finding P-2): hydrate/status consume checkpoint.json directly and
  never invoke verify, so a chain-broken (tampered) checkpoint is used silently. With
  the SessionStart auto-hydrate hook this is a realistic drive-by via malicious PR.
- Markdown/prompt injection: intent titles, distillate claims, decision text are
  embedded verbatim into the bundle that becomes agent context. Inherent to the design;
  document as a trust assumption.

### 3. Dependencies
- Stdlib-only, zero third-party runtime deps - matches standards/dependency-policy.md
  (stdlib first / zero-runtime-dependency preferred). No lockfile required; pip-audit
  is N/A (nothing to audit). PASS.
- CI actions pinned to major tags: actions/checkout@v4, actions/setup-python@v5.
  Acceptable; SHA-pinning is the stronger posture (hardening note H-2).

### 4. Dangerous constructs
- No eval / exec / pickle / yaml.load / subprocess(shell=True) / disabled-TLS /
  world-writable files. JSON via json.loads. PASS on construct inventory.
- Finding R-1 (REPRODUCED): untrusted JSON is parsed with no size or depth bound.
  Deeply-nested input raises RecursionError, which the tool never catches (only
  json.JSONDecodeError is handled in _unresolved_effects / _merge_dead_ends /
  _graph_index). Schema caps apply only AFTER the whole document is parsed. This is the
  [JSON parsed with size/depth bounds] control from skills/security.md, absent.

### 5. AuthZ / AuthN
- No authentication or authorization surface in the tool. The integrity analog is the
  verify gate; see P-2 - the privileged consumers (hydrate/status) do not re-check
  integrity at the moment of action. Noted, not independently blocking.

### 6. Failure posture
- Fail-closed on write: checkpoint validates both schemas BEFORE any write; the suite
  confirms nothing is written on validation failure (test_invalid_proposal_rejected).
  verify returns nonzero on tamper (test_tamper_detected). GOOD.
- Finding F-1 (REPRODUCED): cmd_verify sorts checkpoints/*.json by an int() of the
  filename prefix with no digit-dash regex filter (unlike _distillate_files). A
  stray/malicious file (e.g. evil.json) in checkpoints/ aborts verify with an uncaught
  ValueError instead of reporting a finding. Exit is nonzero (fail-closed-ish) but it
  is an ugly crash and a DoS lever that can mask real chain findings.
- Finding F-2 (minor): git subprocesses carry no timeout; a hung git blocks forever.
- Finding CI-1: .github/workflows/doctrine.yml has NO permissions block. The workflow
  triggers on pull_request and runs the repo tool/test code with the default
  GITHUB_TOKEN scope - a least-privilege violation flagged explicitly by
  skills/security.md (least privilege everywhere: CI permissions). No timeout-minutes
  on the job either.

---

## Reproductions (real output)

R1 - Suite + lint (baseline green):
    python -m unittest discover -s tests -v  ->  Ran 21 tests ... OK
    python tools/doctrine_lint.py            ->  doctrine_lint: corpus clean  (exit 0)

R2 - Path traversal via active_intents (P-1), hydrate bundle output:
    - STALE@f3a9c21 **../TOPSECRET** - API_KEY=sk-live-DEADBEEF-leaked
      - AC: secret exfiltrated
    (planted ../TOPSECRET.intent.json, outside plane.intents, read into the bundle)

R3 - Windows git-in-cwd hijack (NOT exploitable):
    planted git.bat -> ignored; planted git.exe -> real git ran (exit 128).
    Python resolves the exe via parent PATH before applying child cwd.

R4 - Unbounded JSON parse (R-1):
    RecursionError raised (uncaught by tool) on 60k-deep nested JSON array.

R5 - verify crashes on non-conforming file in checkpoints/ (F-1):
    verify CRASHED uncaught: ValueError: invalid literal for int() with base 10: evil.json

---

## Findings register

| ID   | Sev      | Area             | Disposition |
|------|----------|------------------|-------------|
| P-1  | Moderate | Path traversal   | BLOCK: constrain intent ids to a safe charset AND/OR resolve()+prefix-check under plane.intents in hydrate and verify. |
| CI-1 | Moderate | CI least-priv    | BLOCK: add top-level permissions contents:read; add timeout-minutes. |
| P-2  | Moderate | Trust boundary   | Follow-up: hydrate/status should refuse or loudly warn on a checkpoint whose chain fails verify. |
| R-1  | Low-Mod  | Resource bound   | Follow-up: bound untrusted JSON (byte cap before parse; catch RecursionError as a finding, not a crash). |
| F-1  | Low-Mod  | Fail posture     | Follow-up: filter checkpoints/ by the digit-dash prefix and report stray files as findings instead of crashing. |
| S-1  | Moderate | Secrets/guidance | Follow-up: doctrine text + ideally a secret-scan gate on committed state artifacts. |
| F-2  | Minor    | Fail posture     | Recommend: add a timeout to git subprocess calls. |
| H-1  | Minor    | Hardening        | Recommend: resolve git once via shutil.which() / absolute path. |
| H-2  | Minor    | Supply chain     | Recommend: SHA-pin GitHub Actions. |

Nothing in scope contains hardcoded secrets, shell injection, unsafe deserialization,
disabled TLS, or an unrun-but-green audit step. The blockers are input-boundary and
CI-least-privilege controls that skills/security.md mandates as MUSTs and that are
entirely absent (P-1, CI-1), both reproduced/verified and both cheap to fix.

---

## VERDICT: VETO (ship blocked)

Rationale: the mission is [nothing ships that leaks, injects, or trusts the
untrustable]. P-1 trusts untrustable checkpoint content to build a filesystem path and
leaks file contents into agent context (reproduced), violating the loaded skill rule
[path: canonicalize + prefix-check]. CI-1 ships a pull_request-triggered workflow with
no permissions block, violating [least privilege everywhere: CI permissions]. Both are
small, well-scoped fixes.

Release is blocked until P-1 and CI-1 are remediated (P-2, R-1, F-1, S-1 to be fixed or
dispositioned in writing in the same pass). Per the role card, only the human may
override this security veto, explicitly and in writing, and that override must be
recorded in this file.

Hands off to: Builder (remediate P-1/CI-1 and follow-ups), then re-review.

-- Security Reviewer, 2026-07-12

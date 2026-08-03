# Review — Enterprise Control Plane (v0.7.0)
<!-- G4 artifact. Reviewer: Code Reviewer + Security Reviewer (see caveat). -->

**Scope:** `tools/doctrine_guard.py` (new), `tools/doctrine_fleet.py` (new),
`tools/doctrine_gold.py` (attestation), `tools/doctrine_dashboard.py` (flake
fix), `tools/doctrine_install.py` (CI providers, manifest),
`.Doctrine/schemas/gold-build.schema.json`, `.Doctrine/templates/ci/*`, the
hook wiring, and the docs/version carriers.

## Caveat on independence — read this first

The doctrine's G4 calls for a **fresh-context reviewer that did not write the
code**, and `02-role-protocol.md` forbids grading your own homework. This
session was instructed not to dispatch subagents, so what follows is a
**self-review by the author**, not an independent panel. That is a real
weakening of the gate, recorded here rather than papered over: the findings an
author is structurally blind to are exactly the ones this pass cannot catch.
Treat it as an author's disclosure, and run `/review` in a fresh session
before any release.

## Findings

Severity: BLOCKER (must fix) · MAJOR (fix before release) · MINOR · NIT.

### Fixed during the pass

| # | Sev | Finding | Resolution |
|---|-----|---------|------------|
| 1 | MAJOR | A credential name with a prefix (`DATABASE_` + the secret word) slipped the secret rule: the pattern required a word boundary, and underscore is not one. | Identifier prefix allowed, while the secret word must still END the name, so a name like `PASSWORD_RESET_URL` stays clean. Test: `test_credential_name_with_a_literal_value_is_denied`. |
| 2 | MAJOR | The shape-documenting env file was refused as a secrets file — the repo-devops skill *requires* that file to exist. | `PROTECTED_EXEMPT` for the `example/sample/template/dist` variants; the secret rules still apply to them (names yes, values no). Test: `test_placeholders_are_not_secrets`. |
| 3 | MAJOR | **Shell redirects bypassed the path rule entirely.** A redirect into a gold record sailed past a rule that blocked the identical Write. | `check_protected_in_command` judges commands carrying a mutation token (`>`, `rm`, `mv`, `cp`, `tee`, `sed -i`, `dd`); reads stay allowed. Tests: `test_a_shell_redirect_cannot_bypass_the_path_rule`, `test_reading_a_protected_file_is_always_fine`. |
| 4 | MAJOR | **False denial, found by dogfooding.** The secret-assignment pattern let one quote character open and a different one close, so it matched across unrelated text — the guard denied the edit that was writing its own test file. | Backreferenced quotes. Test: `test_an_unquoted_shell_write_to_env_example_is_not_a_secret`. |
| 5 | MAJOR | **Second false denial, also found by dogfooding**: this very review document was refused, because prose *about* credential handling matched the credential pattern. | Values containing whitespace are not credentials. Tests: `test_prose_about_secret_handling_is_not_a_secret` plus `test_a_credential_without_whitespace_is_still_denied` to keep the fix from becoming a hole. A gate that blocks its own documentation gets switched off, so precision is a correctness property here, not polish. |
| 6 | MINOR | A policy file of the wrong shape (a string where a list belongs) was iterated character-by-character into junk patterns. | `load_config` accepts a key only when it is a list. Test: `test_a_policy_of_the_wrong_shape_is_ignored_not_obeyed`. |
| 7 | MINOR | Draining the request body in the oversized branch would have blocked on bytes the client may never send, turning a 413 into a 10-second hang. | That branch marks the body consumed and deliberately skips the drain; `test_rejects_oversized_mutation_before_reading_it` covers it. |

### Accepted limitations (documented, not fixed)

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| 8 | MAJOR | The guard binds only runtimes that honour a pre-execution hook. Another agent editing the same repo is unconstrained. | ADR-012 consequence, accepted. The tool is runtime-neutral (JSON in, JSON out), so a second adapter is wiring, not a rewrite. The doctrine must not claim enforcement it lacks: §7 now states exactly which four rules are mechanical and that the other six are not. |
| 9 | MINOR | Writes to paths *outside* the repo skip the path rule (they have no repo-relative meaning). The secret rules still apply to them. | Denying them would break legitimate cross-repo work — installing Doctrine into a sibling repo is exactly that. Documented. |
| 10 | MINOR | Pattern-based detection has false negatives: a bare high-entropy string with no credential-shaped name is not caught, and after finding 5, neither is a passphrase containing spaces. | Stated in `05-packaging.md` — a floor, not a scanner. The provider formats (AWS/GitHub/Anthropic/OpenAI/Slack/Google/private-key blocks) are matched regardless of naming, and `skills/security.md` still calls for a real scanner at G5. |
| 11 | MINOR | `git verify-tag` proves the tag was signed by a key in the verifier's trust store — not that the signer read the evidence. | ADR-012 consequence; stated in `standards/merge-and-promotion.md`. |
| 12 | MINOR | The ssh-signature text fallback depends on a git output string that could change. | Fails **closed** by construction: a format drift can only under-report a signature, never invent one. Asserted by `test_a_failed_verification_is_never_reported_as_signed`. |

## Checklist

- [x] Public functions type-hinted; `ruff` clean at line-length 88.
- [x] External input parsed at the boundary; no `shell=True`; git invoked with
      argv lists; tag strings format-validated before reaching argv or a path.
- [x] Bounded resources: request reads capped **and** now time-bounded (a
      slowloris could previously hold a bridge thread forever); the guard never
      reads an unbounded body.
- [x] Fail-closed verified: an unparseable payload denies; a malformed policy
      is ignored rather than obeyed; a crashed evaluation denies.
- [x] No credential literals in the diff — fixtures are assembled from
      fragments so the repository never carries a credential-shaped string.
- [x] Behavior changes carry tests; the bridge fix carries a reproduction that
      fails against the pre-fix module and passes after.
- [x] Backwards compatibility: `attestation` is optional, so gold records
      written before 0.7.0 still validate (asserted by a test).
- [x] Scope: no drive-by refactors. The working tree also carries earlier
      uncommitted work from other sessions, which this change did **not** touch.

## Verdict

**Approved with disclosure.** No BLOCKER survives; every MAJOR is fixed with a
test. The independence caveat is itself the most significant finding: this
passed a thorough author's review, not an adversarial one.

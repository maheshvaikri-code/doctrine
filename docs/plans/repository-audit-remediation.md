# Plan — Repository Audit Remediation
<!-- G2 artifact. Task class: L. -->

1. **Verifier identity and required gates** — Backend Engineer
   - Files: `tools/doctrine_verify.py`, `tools/doctrine_lint.py`
   - Proof: regression tests for compact TOML, comment/table false positives,
     and unavailable Ruff returning failure.
   - Rollback: revert parser/gate changes together.
2. **Activation and CI** — DevOps Engineer
   - Files: `AGENTS.md`, `tools/doctrine_awaken.py`,
     `.github/workflows/doctrine.yml`
   - Proof: activation audit plus missing-boot regression test; workflow diff
     shows OS × supported-Python matrix and pinned Ruff.
3. **Test harness and documentation** — QA Engineer / Tech Writer
   - Files: `tests/test_doctrine_packaging.py`, `README.md`, `CHANGELOG.md`
   - Proof: MCP test with `ResourceWarning` promoted to error; discovered test
     count equals README.
4. **Release identity** — Release Manager
   - Create a local annotated `v0.6.46` tag at commit
     `51e7263cd1f2d2fec815ef86eda951d4ac0dfe38`.
   - Do not push. Do not fabricate missing historical tags.
   - Proof: `git rev-list -n 1 v0.6.46` equals the recorded release commit and
     `git ls-remote` showed no authoritative remote tag to fetch.
5. **G4/G5 verification** — Code Reviewer, QA, Security Reviewer
   - Review the complete diff, run Ruff and the full suite on Python 3.12,
     run the suite at the Python 3.11 floor, verify state and activation,
     scan changed content for credential/dangerous patterns.

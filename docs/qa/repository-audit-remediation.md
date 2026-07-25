# QA — Repository Audit Remediation
<!-- G5 artifact. QA: PASS. Security: PASS. -->

## Environment

- Windows
- Python 3.12.7
- Python 3.11.9-family Microsoft Store runtime
- Ruff 0.15.15 on Python 3.12

## Executed evidence

### Focused regressions

- `python tests\test_doctrine_verify.py -v` — 9 tests, OK.
- `python tests\test_doctrine_awaken.py -v` — 6 tests, OK.
- `python -W error::ResourceWarning tests\test_doctrine_packaging.py
  TestMcpServer.test_handshake_list_and_calls -v` — 1 test, OK; no resource
  warning.
- `python tests\test_doctrine_lint.py -v` — 10 tests, OK.

### Full Python 3.12 gate

`python tools\doctrine_verify.py`

```text
Ran 172 tests in 38.230s
OK
=== lint: PASS
=== ruff: PASS
=== tests: PASS
=== state: PASS
VERIFY OK: 4 gate(s) green
```

### Python 3.11 floor

`py -3.11 tools\doctrine_lint.py`

```text
doctrine_lint: corpus clean
```

`py -3.11 -m unittest discover -s tests`

```text
Ran 172 tests in 40.935s
OK
```

`py -3.11 -m pip install --dry-run ruff==0.15.15`

```text
Would install ruff-0.15.15
```

The original fail-open probe was then re-executed directly:
`py -3.11 tools\doctrine_verify.py`. With Ruff absent in that interpreter,
lint/tests/state passed but the overall command returned `1` and printed
`VERIFY FAILED: ruff`, proving the gate now fails closed.

### Activation and release identity

```text
AWAKE: 9/9 checks pass
```

```text
git cat-file -t v0.6.46
tag
git rev-list -n 1 v0.6.46
51e7263cd1f2d2fec815ef86eda951d4ac0dfe38
```

The corresponding `git ls-remote --tags origin` probe returned no v0.6.46
remote ref; the repair is local-only.

## Security sign-off

- No runtime dependency added.
- Ruff is an existing development gate and is now version-pinned in CI.
- Changed files contain no private-key, GitHub-token, AWS-key, or OpenAI-key
  patterns.
- No shell interpolation, unsafe deserialization, credential handling, or
  privilege expansion was introduced.
- No tag or code was pushed or published externally.

**Security verdict: PASS.**

## Limitations

`actionlint` is not installed locally, so the GitHub Actions workflow was
reviewed statically but not executed in this environment. The full matrix will
execute only when the change reaches GitHub.

## Verdict

**QA PASS / SECURITY PASS.**

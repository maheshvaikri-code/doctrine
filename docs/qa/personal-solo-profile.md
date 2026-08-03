# QA + Security Report — Personal/solo profile and default MAPLE
<!-- G5 artifact. QA: PASS. Security: PASS. -->

**QA Engineer** · **Security Reviewer** · **Date:** 2026-07-29
**Build under test:** uncommitted working tree on `main`, based at
`9f42611a892a71d94741b8083329135162a04f19`; tests include all working-tree
changes. Environment: Windows, Python 3.12.7, Ruff 0.15.15.

## Acceptance criteria verification

| # | Criterion | How executed | Evidence (real output) | Pass |
|---|-----------|--------------|------------------------|------|
| 1 | Default installation selects MAPLE | Unit regression + black-box CLI install | `default rc=0`; `default marker: Workforce runtime: maple` | yes |
| 2 | `--personal` and `--solo` share one profile | Direct API regression + CLI alias regression | packaging suite includes both; `solo+startup marker: Delivery profile: personal` | yes |
| 3 | Personal law uses Solo Builder → DevOps with minimal standing ceremony | Corpus lint and cross-document review | `doctrine_lint: corpus clean`; law, workflow, role, governance, and boot files agree | yes |
| 4 | Real risk still activates controls | Law/governance/role review | explicit triggers cover data/regulation, auth/secrets, contracts, destructive/external/paid/publish surfaces | yes |
| 5 | Enterprise conflicts fail before mutation; startup remains compatible | Unit regressions + black-box CLI | conflict `rc=2`, `target_exists=False`; solo+startup contains both markers | yes |
| 6 | Legacy `--maple` is idempotent | Unit regression | marker count asserted equal to 1 | yes |
| 7 | Full source gates pass | `python tools/doctrine_verify.py` | 4/4 gates green; 195 tests OK | yes |
| 8 | Solo defaults creative without weakening deterministic boundaries | Unit regressions, black-box CLI, and policy review | `Agent latitude: creative`; explicit deterministic template field preserved; tests/effects remain gated | yes |

## Adversarial & edge matrix

| Input/scenario | Expected | Observed | Pass |
|----------------|----------|----------|------|
| `--personal --enterprise` | reject before target mutation | exit 2; target absent | yes |
| personal over existing enterprise brief | reject before framework copy | exit 2; law absent | yes |
| enterprise over existing personal brief | reject before framework copy | exit 2; law absent | yes |
| `--solo --startup` | compatible markers | MAPLE + startup + personal markers | yes |
| default install | MAPLE marker, no profile invention | one MAPLE marker | yes |
| legacy `--maple` rerun | no duplicate marker | count = 1 | yes |
| default non-personal install | no latitude invention | `Agent latitude:` absent | yes |
| personal install + rerun | one creative default | creative marker count = 1 | yes |
| templated explicit deterministic latitude | preserve human choice | bold deterministic field retained; creative absent | yes |

Black-box solo install:

```text
solo rc=0
solo marker: Workforce runtime: maple
solo marker: Delivery profile: personal
solo marker: Agent latitude: creative
```

## Regression evidence

Focused packaging:

```text
Ran 30 tests in 3.436s
OK
```

Focused activation:

```text
Ran 7 tests in 0.017s
OK
```

Complete source verification:

```text
Ran 195 tests in 93.794s
OK
=== lint: PASS
=== ruff: PASS
=== tests: PASS
=== state: PASS
VERIFY OK: 4 gate(s) green
```

Additional checks:

```text
doctrine_lint: corpus clean
All checks passed!
doctrine_signature: all signatures current
root/adapters AGENTS byte-identical: True
```

One initial focused invocation used dotted unittest module names even though
`tests/` is not a Python package; it produced two loader errors. The command
was corrected to this repository's discovery form, which produced the green
focused and full results above. No retry of a flaky product test occurred.

## Security sweep

- Secrets scan: changed-content credential/private-key name scan returned no
  matches.
- Dependency audit: no manifest or lockfile changed; no dependency was added.
- Injection review: no shell command or dynamic code execution was introduced.
- License boundary: Doctrine records an external runtime selection but does
  not install, vendor, import, or link AGPL MAPLE code.
- Filesystem boundary: incompatible profiles are rejected before target
  creation/copy; existing brief bytes are decoded with replacement for policy
  detection; canonical markers are appended idempotently.
- Permanent controls: truthfulness, tests, secret handling, irreversible and
  external-action escalation, and risk-specific specialists remain active.
- Creative latitude changes candidate generation only; it grants no new
  filesystem, network, publishing, spending, secret, scope, or risk-acceptance
  authority.

**Security verdict: SIGN-OFF.**
**QA verdict: PASS.**

## Limitations

Fresh-context reviewer separation could not be created under the active
no-delegation tool rule. The objective automated gates and black-box probes are
green; the same-session review limitation is recorded in G4.

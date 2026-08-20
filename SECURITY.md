# Security Policy

Doctrine is a governance and enforcement layer, so a defect in it can let a
governed agent do something a human never approved. Security reports are taken
seriously and are always welcome.

## Reporting a vulnerability

**Do not open a public issue for a vulnerability.**

Use either:

1. **GitHub private vulnerability reporting** — *Security* → *Report a
   vulnerability* on this repository. Preferred, because it keeps the whole
   thread in one place.
2. **Email** — <mahesh.vaikri.ai@gmail.com>, with `DOCTRINE SECURITY` in the
   subject.

Please include:

- The version or commit SHA, your OS, and your Python version
- A **minimal reproduction** — the exact command or payload
- The real observed output, and what you expected instead
- Which control you believe was bypassed (`doctrine_guard`, `doctrine_gold
  gate`, the state chain, `doctrine_lint`, the MCP server, the loopback bridge)

### What to expect

This is maintained by one person, so these are honest targets rather than a
contractual SLA:

| Stage | Target |
|---|---|
| Acknowledgement | within 3 business days |
| Initial assessment | within 10 business days |
| Fix or documented disposition | depends on severity and complexity |

You will be told which of *fixed*, *documented limitation*, or *out of scope*
your report landed in, and why. Credit is given in the changelog unless you ask
otherwise. Please allow a reasonable window before public disclosure — and if
the finding is already publicly known, say so and we can skip the embargo.

## Supported versions

Doctrine is **0.x under active development**. Only the latest release receives
fixes; there are no backports to older 0.x tags.

| Version | Supported |
|---|---|
| 0.7.x (latest) | ✅ |
| < 0.7 | ❌ — upgrade via `doctrine_install.py --force` |

Installed copies drift. `doctrine_fleet status` shows which of your repos are
behind, and a drifted corpus is fixed by a `--force` reinstall, never by
hand-editing an installed corpus.

## In scope

- **`doctrine_guard`** — any input that reaches a protected path through the
  **Write/Edit** surface, where the guard is meant to be sound
- **`doctrine_gold gate`** — any way to alter a committed gold record that the
  gate still passes
- **The state plane** — forging or altering a checkpoint or distillate such
  that `doctrine_state.py verify` still reports an intact chain
- **`doctrine_dashboard`** (the loopback bridge) — any path to arbitrary
  command execution, any non-loopback exposure, any mutation beyond the fixed
  verifier
- **The MCP server** — a tool performing an action outside its declared
  contract
- **The installer** — path traversal, writing outside `--target`, or executing
  unvetted code from a target repo
- **Secret handling** — a credential pattern the guard should deny and does not

## Known limits — please read before reporting

These are **documented, deliberate, and already public**. Reporting them again
is not a finding, though a way to make one materially *worse* is.

- **There is no Bash guard.** As of ADR-014 the `PreToolUse` hook is wired to
  `Write|Edit|MultiEdit|NotebookEdit` only, and the shell path-analysis code is
  deleted. Doctrine does not inspect, restrict, or prompt on shell commands.
  It was previously a *tripwire, not a boundary* — shell is Turing-complete,
  the path need not appear in the command, and no static text analysis of it
  can be complete — so novel shell spellings reaching a protected file were
  *expected*, not vulnerabilities. They are now simply out of scope: a shell
  command doing anything at all is the documented behaviour. The real boundary
  is an isolation tier — see
  [`skills/sandboxing.md`](.Doctrine/skills/sandboxing.md) — plus your own
  runtime `permissions.deny`/`ask` lists, which outrank any hook decision.
- **Gold records are tamper-evident, not tamper-proof.** A record forged and
  committed in the **same single commit** has no prior state to diff against
  and passes the gate. CI does not help — it checks out the same HEAD. That
  class is caught by a human reading the diff.
- **Verifier isolation is a strong default, not a sandbox.** Verifier subagents
  lack Edit/Write but retain Bash.
- **Nothing inside a repo the agent can write is tamper-proof against that
  agent.**
- **Without the `PreToolUse` hook wired, Doctrine is advice.** An agent runtime
  with no pre-execution gate cannot enforce §7 #2/#4 or §5.

Full strength table and reasoning:
[`.Doctrine/05-packaging.md`](.Doctrine/05-packaging.md).

**Still very interesting**, despite the above:

- A **Write/Edit** bypass (that surface is claimed sound — a break there is a
  real defect, not a known limit)
- Tampering with a **previously committed** gold record that the gate passes
- A state-chain alteration that `verify` accepts
- The guard **failing open** — crashing, timing out, or returning allow on
  malformed input
- A blanket policy pattern that silently disables the guard
- The loopback bridge reachable off-host, or executing anything beyond the
  fixed verifier

## Out of scope

- Vulnerabilities in the AI models or agent runtimes Doctrine governs
- MAPLE, or any third-party tool referenced by an integration document —
  report those upstream
- Findings that require an attacker who already has write access to the repo
  **and** the maintainer's credentials
- Social engineering, physical access, or attacks on GitHub itself
- Automated scanner output with no demonstrated impact
- Missing hardening that the docs already disclose as absent

## Our own practice

Doctrine's enforcement tooling was hardened through five rounds of adversarial
verification, and the findings are committed in public — including the round
that **overturned a sign-off the system had already given itself**. The audit
trail is in [`docs/reviews/`](docs/reviews/) and [`docs/qa/`](docs/qa/), and
every limit above is stated in the corpus rather than discovered by you later.

Claiming a control is stronger than it is would violate this project's first
law. If you find documentation that overstates a mechanism, that is a valid
security report too.

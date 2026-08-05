# doctrine-integrations — index

Wiring for third-party projects Doctrine **composes with**. Every one is a thin
shim over a pinned upstream — **never a vendored copy**, because a vendored fork
goes stale and forks the behaviour silently.

## The rule

Doctrine's own tooling is **stdlib-only with zero dependencies**, and it
installs, imports, and vendors **nothing** from this folder. That is what keeps
it installable into any repo on any OS with nothing to resolve, and what keeps
the gates working when none of these are present.

**Every integration is optional. No gate depends on one.** A missing upstream
degrades that one capability and nothing else.

## What is wired

| File | Upstream | What it adds |
|---|---|---|
| `maple.md` | [maple-oss](https://github.com/maheshvaikri-code/maple-oss) (AGPL-3.0) | Multi-agent runtime: typed messages, `Result<T,E>`, broker-enforced separation of duties. Carried for **OpenHawk**; Doctrine itself needs no runtime. |
| `floci.md` | [floci](https://github.com/floci-io/floci) (MIT) | Local cloud emulation under the `cloud-*` skills and the FDE pipeline — local-first, so real spend stays a §5 decision. |
| `fde.md` | — | Overview of the FDE prototype pipeline (P1–P6) that `floci` serves. |
| `codemonk.md` | [codemonk](https://github.com/aroora-ai-labs/codemonk) (MIT) | The metrology subsystem: change metrics, token metering, a graded scorecard. |

## Adding one

An integration document is a **contract**, not an endorsement. It must state:

- the upstream URL, licence, and a **pinned version** that has actually been
  verified — a pin nobody re-checked is a claim, not a fact
- what the shim adds on top (doctrine-side precedence rules), and what it does not
- how the capability **degrades** when the upstream is absent; every integration
  degrades cleanly and never fails a gate
- a `verified:` date, against a real run whose output was pasted

If a shim needs its upstream installed before it does anything, **say so in the
shim itself**. A routed skill that silently does nothing is worse than no
skill, because it reads as covered when it is not.

New integrations pass `standards/dependency-policy.md` first, and adoption is
the human's decision (§5).

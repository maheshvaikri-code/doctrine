---
integration: maple
upstream: https://github.com/maheshvaikri-code/maple-oss
license: AGPL-3.0 — free/open-source copyleft; ordinary use is unrestricted
pinned_version: 1.1.3
discipline: multi-agent-runtime
verified: 2026-08-04
---

# MAPLE — Integration (one agent runtime among many; Doctrine needs none)

**Read this first, because the older framing of this file got it backwards.**
**Doctrine does not need an agent runtime.** Its gates, roles, artifacts, and
state plane run on plain serial role-switching in a single session, and on the
host agent's native subagents when it has them. Nothing in G0→G7 requires a
broker, a message bus, or a persistent fleet.

**MAPLE is one agent runtime among many, not a designated default.** Doctrine
is runtime-agnostic and carries integration playbooks the same way it carries
any other tool knowledge (`skills/tooling.md` — portfolio first, adoption via
`standards/dependency-policy.md` and §5). MAPLE has the fullest document here
for two ordinary reasons: it is first-party, and it is what **OpenHawk** runs.
Another runtime in the same slot gets the same treatment and the same
boundaries — nothing in this file privileges MAPLE over an alternative.

**Scope: software development.** What Doctrine carries about any runtime is
the engineering usage — how work packages, gate verdicts, separation of duties,
and escalations map onto its primitives for building software. Doctrine does
not govern the runtime's other applications, does not operate it, and does not
document it beyond that seam.

MAPLE (Multi Agent Protocol Language Engine, `pip install maple-oss`) is a
multi-agent runtime and protocol: typed messages with `Result<T,E>` error
handling, a broker (in-memory to NATS), pairwise link-identified secure
channels, resource negotiation, task scheduling, and an autonomy layer
with LLM providers (Anthropic included) — three layers: L1 protocol,
L2 runtime, L3 autonomy SDK. It ships a first-class **doctrine profile**
(`maple.adapters.doctrine_adapter`) and a **broker-enforced fresh-context
verifier preset** (`maple.security.separation`) built to this integration's
spec.

Re-verified here (2026-08-04, Windows, Python 3.12) against **1.1.3**, in an
ephemeral install, all real output: `register_handler("work.package")`
normalizing to `WORK.PACKAGE`; `MessageBroker.is_routable` present and
`Agent.send` accepting `require_routable`; `build_work_package` producing a
typed `WORK.PACKAGE`; `GATE_VERDICTS == {PASS, FAIL, BLOCKED, WAIVED}` with a
bogus `"LGTM"` verdict rejected; `tokens` present as a `ResourceRequest` field;
and the preset **blocking a verifier→builder route** with
`SEPARATION_OF_DUTIES_VIOLATION`.

When `maple-oss` is available to OpenHawk, roles become persistent, addressable
agents. When it is unavailable, execution degrades to native subagents or
serial role-switching (`04-agent-adapters.md`) **without weakening gates** —
because the gates never depended on it.

## The fit — Doctrine concept → MAPLE primitive

| Doctrine                                | MAPLE                                    |
|-----------------------------------------|------------------------------------------|
| Role / subagent                         | `Agent` (L2) or `AutonomousAgent` (L3, Anthropic provider) |
| Orchestrator (main session)             | `AgentOrchestrator.execute_supervised`   |
| Verifier panel (G4/G5 fan-out)          | `AgentOrchestrator.execute_consensus`    |
| Work package (declared file scope)      | `build_work_package(package_id, role, file_scope, brief_ref)` → typed `WORK.PACKAGE`; `validate_work_package` checks an incoming one |
| Gate verdict                            | `build_gate_result(gate, verdict, artifact_ref)` → typed `GATE.RESULT`; verdict validated against `GATE_VERDICTS` (`PASS`/`FAIL`/`BLOCKED`/`WAIVED`) |
| Honest reporting ("blocked" is valid)   | `Result<T,E>` — errors are values, never fabricated success; `send(..., require_routable=True)` → `Err UNROUTABLE` instead of a misleading `Ok` |
| Separation of duties                    | `fresh_context_verifier_preset(orchestrator, builders, verifiers)` → a broker-enforced `SeparationOfDutiesPolicy`: per-agent sender allowlist (fail-closed) + artifact-ref-only payloads. A verifier **cannot** route to a builder. Not a convention — a runtime guarantee |
| Permission matrix (enterprise profile)  | `security/` authentication + authorization + audit; the separation policy above |
| Loop caps / budgets                     | `ResourceRequest.tokens` (LLM budget, first-class beside compute/memory) + `ResourceNegotiator` |
| doctrineos MCP server                   | `maple.adapters.mcp_adapter` — MAPLE agents read the law over MCP |

Two hard boundaries, non-negotiable:

1. **MAPLE routes; gates decide.** A message reaching a verifier is not a
   review. Verdicts count only as artifacts under `docs/` (content-pinned,
   per `standards/merge-and-promotion.md`). The runtime is transport.
2. **The state plane stays the durable truth.** MAPLE's state store is
   ephemeral runtime state. Checkpoints, distillates, and decisions live
   in `.doctrine-state/` (hash-chained, git-committed) — never in the
   broker.

## Wiring pattern (verified shape, 1.1.3)

```python
from maple import Agent, Config
from maple.adapters.doctrine_adapter import build_work_package
from maple.security.separation import ArtifactRef, fresh_context_verifier_preset

worker = Agent(Config(agent_id="backend-engineer",
                      broker_url="memory://localhost", capabilities=["build"]))
worker.register_handler("work.package", on_work_package)  # normalized to WORK.PACKAGE

# separation of duties as a runtime guarantee, not a convention:
policy = fresh_context_verifier_preset(
    "orchestrator", builders=["backend-engineer"], verifiers=["code-reviewer"])

wp = build_work_package("wp-1", "backend-engineer", ["src/service/"],
                        ArtifactRef("docs/brief.md", brief_sha256),
                        sender="orchestrator", receiver="backend-engineer")
orchestrator.send(wp.unwrap(), require_routable=True)   # Err UNROUTABLE, not a false Ok
```

Payload discipline: work packages and verdicts carry **artifact
hashedrefs** (`ArtifactRef(path, sha256)`), not prose — enforced by the
preset's artifact-ref-only payload policy for guarded types. A builder's
reasoning cannot travel to a verifier; the verifier reads the artifact
fresh. Message types are Doctrine's protocol vocabulary: `WORK.PACKAGE`,
`GATE.RESULT`, plus §5 escalations, which always terminate at the human,
never at another agent.

## Resolved in 1.1.2, still holding at 1.1.3 (the 1.1.1 sharp edges)

- **Handler-key case trap → fixed.** `register_handler` now normalizes keys
  to upper-case, matching `Message` (the `@agent.handler` decorator path
  too). A handler registered `"work.package"` fires for `WORK.PACKAGE`.
  Verified here.
- **`send()` Ok = enqueue → opt-in delivery check.** `send(...,
  require_routable=True)` returns `Err UNROUTABLE` when the receiver has no
  live subscription (via `MessageBroker.is_routable`). The default `send()`
  is unchanged (Ok = enqueued), so still treat a default dispatch as
  reply-or-timeout; use `require_routable=True` when a false Ok would
  mislead. Reachability is checked at *send* time — a post-delivery
  acknowledgement receipt remains future work. Verified here.
- Also fixed in 1.1.2 (pre-existing bugs): broker **double-delivery** (each
  direct message was enqueued into two queues and delivered twice) and a
  `TaskQueue` **shutdown hang** (`stop()` blocked ~5s on a sleeping cleanup
  thread).

## Enhancement asks — SHIPPED in maple-oss 1.1.2, re-verified at 1.1.3

All five landed (the 1.1.2 CHANGELOG maps each to its ask number; re-verified
here against the source tree):

1. ✅ `register_handler` key normalization (kills the case trap). 5 tests.
2. ✅ Routability check: `MessageBroker.is_routable`, `send(...,
   require_routable=True)` → `Err UNROUTABLE`. 7 tests. (Post-delivery ack
   receipt still open.)
3. ✅ Fresh-context verifier preset: `maple.security.separation` —
   `SeparationOfDutiesPolicy` (fail-closed sender allowlist +
   artifact-ref-only payloads), `fresh_context_verifier_preset(...)`,
   `ArtifactRef(path, sha256)`. Separation of duties is now a
   **broker-enforced runtime guarantee**.
4. ✅ Doctrine profile: `maple.adapters.doctrine_adapter` —
   `build_work_package` / `build_gate_result` (→ `Result[Message]`),
   `validate_work_package` / `validate_gate_result`, `DoctrineAdapter`,
   `GATE_VERDICTS`. 34 tests. Imported explicitly, so `import maple` stays
   free of the security layer.
5. ✅ `tokens` as a `ResourceRequest` resource type (round-trips through
   negotiation; `ResourceManager` allocates it). 9 tests.

This closes the v0.6.11 caveat: transport-level duty separation was a
documented convention; with ask #3 shipped it is a broker-enforced
guarantee. Remaining open upstream: a true post-delivery acknowledgement
receipt (beyond send-time reachability).

## License — a note, not a gate

MAPLE is free/open-source software under **AGPL-3.0**, and first-party (same
author as this doctrine). **Anyone may use, run, and build on it freely,
including commercially.** Copyleft is a reciprocity condition on *redistribution
and on serving a modified version over a network* — it is not a usage fee, not a
restriction on ordinary use, and not something a consumer of this doctrine needs
clearance for.

`standards/dependency-policy.md` §4 makes GPL/AGPL **in a shipped library** an
explicit human decision. Doctrine ships no such library, so that clause never
applied here — an earlier revision of this file invoked it anyway and turned a
non-issue into a "verdict." That framing was wrong and is removed.

The reason `doctrineos` does not import `maple-oss` is not the license. It is
that **Doctrine needs no runtime**: the wheel, MCP server, and tools stay
stdlib-only so the doctrine installs into any repo on any OS with zero
dependencies, and so the gates keep working when no broker exists. The doctrine
profile ships inside `maple-oss`, not here. A brief's `Workforce runtime: maple`
marker records a selection for OpenHawk; it installs, links, and downloads
nothing, and the installer performs no hidden package or network mutation.

## Boundaries

The runtime never replaces briefs, gates, artifacts, or the human's §5
authority. If the broker is down, the doctrine still runs — degraded to
native subagents or serial role-switching. Adoption order: prove the
task needs persistent cross-agent messaging first (most Class M work
does not); the runtime earns its keep at fleet scale, not on a bugfix.

**And the direction of dependence only points one way.** OpenHawk needs both
Doctrine and MAPLE; Doctrine needs neither OpenHawk nor MAPLE. Per ADR-003 the
family is `product → {doctrine, maple}` with `doctrine ⟂ maple` — no cycles.
A reader who comes away thinking Doctrine *requires* a runtime has read this
file wrong, and earlier revisions of it were partly to blame.

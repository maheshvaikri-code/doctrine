# Project/Task Brief — Productize the DOCTRINE + MAPLE stack (working name: DoctrineOS)

<!-- G0 artifact. File as docs/brief.md or docs/briefs/<task>.md -->

**Date:** 2026-07-13 · **Class:** L — new product program, cross-cutting, multi-month, spans packaging + runtime + a new daemon + channel adapters · **Requested by:** human (Mahesh)

## Problem

DOCTRINE + MAPLE already own the *hard* half of a great agent product — governed
gates, hash-chained verified state, a multi-agent runtime, separation of duties,
adversarial verification — but there is no product **surface** on top of it. Today
you reach the stack only from inside a coding agent's session (Claude Code, Codex).
OpenClaw ([openclaw.ai](https://openclaw.ai/), 100k+ GitHub stars in a week, Jan 2026)
proved the surface that makes an agent go viral: a persistent self-hosted daemon,
reachable from the chat apps people already use, a heartbeat scheduler, cross-run
memory, pluggable skills, and one-command install with docs so smooth adoption is
frictionless. OpenClaw's own weakness — an ungoverned agent taking shell actions with
no gates, no audit trail, no duty separation — is precisely DOCTRINE's core strength.
The opportunity: wrap the DOCTRINE+MAPLE core in the OpenClaw-style shell. The product
is not "another personal assistant that acts" — it is **a governed engineering
organization you talk to**, one that cannot fabricate, cannot ship unreviewed, and
keeps the receipts.

## Scope

- **In (the program):** a productized, self-hosted distribution of the DOCTRINE+MAPLE
  stack that (a) installs and runs turnkey, (b) runs as a persistent daemon on the
  MAPLE runtime, and (c) is reachable and controllable from at least one chat channel,
  emitting the Engagement Block, gate events, and §5 escalations to the human.
- **Serves all three tiers via existing machinery:** solo (default), team, enterprise
  — mapped onto DOCTRINE's existing `startup`/`enterprise` **profiles** rather than a
  new tiering model. Solo = lightest surface; team adds shared state plane + review
  fan-out + merge council; enterprise adds the GRC governance surface + permission
  matrix + audit trail.
- **Program shape (phased — each phase is its own L/M engagement through the gates):**
  1. **v0.1 — Turnkey distribution** *(this brief's acceptance criteria)*. One-command
     install of the whole stack, docs/onboarding, health-checked. The foundation a
     daemon requires: you cannot daemonize what does not cleanly install.
  2. **v0.2 — The daemon (`doctrined`)**. Wrap the agent loop in a persistent process
     on MAPLE's broker/runtime; heartbeat scheduler; session persistence via the state
     plane (memory already exists — reuse, don't rebuild).
  3. **v0.3 — Chat gateway (one channel first)**. Slack *or* Telegram adapter; the
     human drives tasks and receives Engagement Blocks, gate verdicts, and escalations
     in-channel. This is the "governed org you talk to" moment.
  4. **Later** — more channels, polish, the proud-moment OSS public launch.
- **Non-goals (this program, stated now to prevent scope-creep):**
  - **Not** a clone of OpenClaw's 12+ channels or 100+ skills at once — one channel,
    the existing skills, then expand on evidence of use.
  - **Not** a hosted SaaS in this program — self-hosted first; managed cloud is a paid
    service and a separate §5-gated program if it ever happens.
  - **Not** replacing DOCTRINE's gates, artifacts, or the human's §5 authority with a
    smoother UX — the product exposes the discipline, it does not soften it.
  - **Not** going public / relicensing yet — private until the "proud moment."
- **Deferred (parked ideas):** brand name (OpenHawk or other — working name is
  DoctrineOS, which already exists as the package + MCP server name); voice/Canvas
  surfaces like OpenClaw's; a skills marketplace; multi-tenant hosting.

## Acceptance criteria (numbered, testable) — for v0.1 (Turnkey distribution) only

1. Given a fresh machine with Python and git, when the user runs a single documented
   command, then the full stack (DOCTRINE corpus + tools + MAPLE runtime wiring + state
   plane) installs and `doctrine_verify` passes with 4 green gates — no manual fixups.
2. Given the install, when the user follows the quickstart doc end to end, then they
   can engage a real task (`doctrine: <task>`) and see the Engagement Block, a produced
   artifact under `docs/`, and a committed checkpoint — with zero steps the doc omits.
3. Given a Windows, macOS, and Linux run, when install + verify execute, then all three
   pass (the stack is already cross-platform; this criterion guards regressions).
4. Given the MAPLE runtime is selected, when the user opts in, then `Workforce runtime:
   maple` is recorded in their brief and a documented smoke path proves an
   orchestrator→worker dispatch succeeds locally.
5. Given the distribution ships, when a security reviewer audits it, then no criterion
   above was met by weakening a check, and no secret/credential path is introduced.

## Constraints

- Cross-platform (Win/macOS/Linux); Python stdlib-first for doctrineos (MAPLE is the
  one heavy, opt-in, AGPL dependency and is never imported by doctrineos — document +
  protocol contract only, per `integrations/maple.md`).
- Licensing: stays private now; relax to OSS across the whole stack at the proud
  moment. MAPLE is AGPL-3.0; DOCTRINE's public license is a launch-time decision — must
  be settled *before* the OSS flip, not after.
- An agent that takes actions across channels is a first-order security + responsible-AI
  surface: G1 requires **Head of AI + CISO co-sign**; the daemon's action authority must
  be default-deny with §5 escalations wired to a real human, never auto-approved.

## Assumptions (chosen defaults — correct me if wrong)

- Working product name **DoctrineOS**; daemon **`doctrined`**. Placeholders until the
  brand decision at launch.
- v0.1 ships **before** any daemon/channel code — distribution is the foundation, and
  it is the fastest honest proof of value.
- First chat channel (at v0.3) will be **Slack or Telegram**; picked at that phase's G0,
  not now.
- "All tiers" is served by the **existing profile system**, not a rebuild.

## Open questions (blocking — answered before G1)

- None blocking G1 for **v0.1 (distribution)** — scope is well-defined by the criteria
  above. The daemon (v0.2) and gateway (v0.3) phases each open their own G0/G1 with
  their own questions (channel choice, scheduler policy, action-authority model).
- One to hold for the human at the v0.2 boundary: **how much autonomy does the daemon
  get between heartbeats** — fully autonomous within gates, or human-confirmed at every
  §5? (Default assumption: gates run autonomously, §5 always escalates — same as the
  Engagement Protocol today.)

**Human confirmed:** pending · 2026-07-13

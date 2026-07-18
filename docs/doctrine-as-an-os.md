# Doctrine as an Operating System for Agents

> Doctrine is the **operating system for coding agents — not the machine that
> runs them.** It owns the *policy* — how work is scheduled, isolated,
> remembered, and privileged — and delegates the *mechanism of execution* to
> whatever harness runs the agent (Claude Code, Codex, Cursor, Gemini CLI,
> MAPLE, …). An OS layered over hardware it does not itself provide: that is
> precisely what makes Doctrine portable across every agent and harness.

## Not a harness — a layer on top of one

A *harness* is the thing that actually runs an agent: the loop, the tool calls,
context management, the model calls. Claude Code, Codex, the Agent SDK, and
MAPLE are harnesses. Doctrine has none of that machinery. It is two things:

- a **markdown corpus** — the law, roles, skills, standards, and gate artifacts;
- **thin, stdlib-only tooling** — corpus lint, the state plane, gold-build
  gates, an MCP server, an installer.

It never calls a model or drives an agent loop. It installs into a repository and
the running harness reads it (via `CLAUDE.md` / `AGENTS.md`). The *processor* is
the LLM + harness; Doctrine is the OS scheduled onto it.

## The mapping

| OS concept | Doctrine component | How real is it? |
|---|---|---|
| **Kernel** (always resident, privileged, unbypassable) | `.Doctrine.md` — the root law, **always loaded** — plus the Non-Negotiables (§7) and Prime Directive | Hybrid: the *law* is cooperative (the agent chooses to obey), but the **stdlib gates** (`doctrine_lint`, `doctrine_verify`, gold-build checks) are **hard-enforced, fail-closed** — the "protected mode" |
| **Processes** | tasks/engagements flowing through gates **G0→G7**; **classes S/M/L/HOTFIX** = scheduling priority | Real lifecycle + state machine; a failed gate faults back to the gate that owns the defect |
| **Context switch** | swapping role "hats" (`[ROLE: …]`), one at a time | Real — and in multi-agent mode each role is a *separate process* |
| **Process isolation / privilege rings** | separation of duties — a reviewer runs **read-only** and *physically cannot* edit what it judges | Hard-enforced with subagents (read-only toolset); cooperative (fresh-context) single-agent |
| **Memory** | the **state plane** (`.doctrine-state/`): checkpoint → hydrate. *The repo remembers so the model doesn't have to* | Very real — this *is* the memory subsystem |
| **Durable storage vs RAM** | committed **hash-chained checkpoints** (durable, tamper-evident) vs the machine-local runtime ledger (volatile) | Real two-tier split |
| **Demand paging** | progressive disclosure — a skill is read only when the task touches it; `.Doctrine/` is never bulk-loaded | Real — keeps the working set lean |
| **Syscalls / privilege escalation** | **§5 escalations** — every irreversible or external action requires elevated privilege; **the human is root** | Real capability boundary (least privilege) |
| **HAL / drivers** | the **adapters** (`AGENTS.md` + per-editor overlays) that let it run on Claude Code / Codex / Cursor / … | Real hardware-abstraction analog |
| **Filesystem** | the gate **artifacts** (`docs/brief`, `adr`, `plans`, `reviews`, `qa`, `retro`) | Real structured on-disk state |
| **init / boot** | the SessionStart hydration hook + the Engagement Protocol | Real |
| **Package manager** | `doctrine_install` + the dependency policy | Real |
| **Audit log / dmesg** | the hash-chained state plane + the anti-fabrication law (real output pasted, never paraphrased) | Real, tamper-evident |

## The kernel

An operating-system kernel is the always-resident, privileged core that every
process obeys and none can bypass. Doctrine's kernel is `.Doctrine.md` — a single
file, **always loaded at session start**, small on purpose (progressive
disclosure keeps the rest out of the working set). It carries the Prime Directive
(*correctness over speed, truth over optimism*), the ten Non-Negotiables (§7), the
task-classification rules, and the routing table that pages in the rest on demand.

But a law you can *choose* to ignore is not a kernel. Doctrine's privileged,
unbypassable half is its **tooling**: `doctrine_lint` (corpus self-consistency),
`doctrine_verify` (the gate runner), and the gold-build checks — all **fail
closed**. A version that lies about its own counts, a checkpoint whose hash chain
is broken, a gold record without its sign-offs: these are *rejected by code*, not
by good intentions. That is the kernel's protected mode.

So the kernel is a **hybrid**: the always-on law (cooperative — an obedient agent
follows it) fused with fail-closed gates (hard — the tooling refuses bad states).

## Processes

A process is a unit of work with a lifecycle. In Doctrine, that unit is a **task**
(or *engagement*), and its lifecycle is the gate pipeline **G0 → G7**: intake,
architecture, planning, build, review, verification, release, retrospective. Each
task is **classified** on entry — S / M / L / HOTFIX — which sets how much of the
pipeline it runs, exactly like a scheduling priority or niceness (a typo does not
convene a council; a release always does).

Processes run *as* a **role**. A single agent **context-switches** between role
hats (`[ROLE: Code Reviewer]` → `[ROLE: Engineer]`), one at a time; a fleet runs
each role as a **separate process**. Either way, **isolation** is the point:
separation of duties means the reviewer of a change is never its author. With
subagents this is *hard-enforced* — the reviewer's toolset is read-only, so it
**physically cannot** edit the code it judges (a privilege ring). Single-agent, it
is enforced by a fresh-context pass plus tool restriction. A failed gate is a
**fault** that routes the task back to the gate that owns the defect — a closed
loop, not a crash.

## Memory

The hardest problem for an agent is that the model itself is stateless between
sessions. Doctrine's answer is a real **memory subsystem**: the **state plane**
under `.doctrine-state/`. Work ends with a **checkpoint** (write to memory) and
the next session begins with **hydration** (load memory into context). *The repo
remembers so the model doesn't have to.*

It is tiered, like durable storage versus RAM:

- **Durable, tamper-evident:** committed **hash-chained checkpoints** — each folds
  in the previous hash and a monotonic sequence, so an edit, deletion, or reorder
  breaks the chain and `verify` catches it.
- **Volatile, local:** a machine-local runtime ledger (gitignored) for
  in-flight session state.

And the working set is managed by **demand paging**: the routing table pages a
skill in only when a task touches its domain; `.Doctrine/` is never bulk-loaded.
That is what keeps the always-resident kernel small.

## The privilege model

Every OS draws a line between what a process may do freely and what requires a
**syscall into privileged code**. Doctrine draws it at **§5**: read and plan
proceed freely; anything **irreversible or external** — deleting data, force-push,
publishing a release, adding a paid dependency, sending outward — **escalates**.
The escalation target is the human: in this operating system, **the human is
root.** Default posture is least-privilege; elevation is explicit, announced, and
never a silent convenience.

## Single agent or a fleet — the OS doesn't care

Because Doctrine owns policy and not the processor, it is **agent-count-agnostic**:

- **One agent** wears every role hat sequentially — a complete, functioning
  single-"CPU" system.
- **A fleet** dispatches parallel workers on disjoint file scopes plus
  fresh-context verifiers (the shipped `.claude/agents/`), or a persistent,
  broker-governed workforce on the **MAPLE** runtime.

The strongest isolation guarantee — *the reviewer is not the builder* — is fullest
multi-process, but the policy is identical either way. The OS scales from one core
to many without a rewrite.

## Where the metaphor holds, and where it doesn't

Honesty is the first Non-Negotiable, so the limits are stated plainly:

- **No CPU of its own.** The processor is the LLM + harness. Doctrine is the OS;
  the agent + harness is the machine. That is *why* it is not the machine that runs
  the agents.
- **No preemptive scheduler.** The gate pipeline is a *cooperative* lifecycle
  advanced by the agent and human — there is no timer interrupt preempting a task.
- **The kernel is half cooperative.** A real kernel enforces via hardware privilege
  rings. Doctrine's is half the always-loaded law (which relies on an obedient
  agent) and half fail-closed tooling. The parts closest to hardware-grade
  enforcement are the memory tier (hash chains), the review isolation
  (tool-scoping), and the gates (fail-closed); the law itself is followed, not
  physically imposed.

## In one line

**Kernel** = the always-on law + fail-closed gates · **processes** = tasks through
G0→G7, run as roles with isolation · **memory** = the hash-chained state plane ·
**syscalls** = §5 (the human is root). Doctrine owns the *policy*; the harness owns
the *CPU* — the definition of an operating system layered over hardware it does not
itself provide.

---
argument-hint: [task to isolate | "this session" | tier to verify]
description: Size the isolation tier to the blast radius, then prove the boundary actually holds
---

Act as the **DevOps Engineer** (`.Doctrine/roles/devops-engineer.md`) on the isolation
boundary, loading `skills/sandboxing.md`. Announce `[ROLE: DevOps Engineer]`.

**Report the tier you are actually in before you reason about the tier you want.**
On a developer machine the honest answer is usually **tier 0 — no isolation**, and an
agent that believes it is contained when it is not is worse off than one that knows it
is on the host. Check, don't assume: `/.dockerenv`, `/proc/1/cgroup`,
`systemd-detect-virt` on Linux; the platform equivalent elsewhere. Say plainly if the
check is inconclusive.

**1 — Blast radius.** If this work goes wrong, is compromised, or is prompt-injected,
what does it reach? Enumerate concretely: which paths are writable, which credentials
are in the environment, what the network can reach, what persists after the task.
"Probably nothing important" is not an answer — list it.

**2 — Tier.** Pick the lowest tier from the ladder in `skills/sandboxing.md` whose
"does not stop" column you can genuinely accept, and **write down why**. Tier 5
(paid/remote sandbox) sends data off the machine — that is a §5 escalation before it
happens, not after.

**3 — The five dimensions**, named separately because most "sandboxes" control one and
are assumed to control all five: writable **filesystem** · **egress** · **credentials**
that cross in · **lifetime** · what **results** carry back out.

**4 — Prove it.** Run the boundary proof *inside* the sandbox and **paste the real
output**. Each must fail:

- write to a protected path → `Read-only file system` / `Permission denied`
- `curl` an unlisted host → timeout / refused / DNS failure
- `env` + credential-file check → empty / `No such file or directory`
- `/var/run/docker.sock` absent, non-root uid, capabilities dropped

A config file is a claim. A pasted refusal is a boundary. **If you cannot run the proof,
say the tier is unverified — do not report the tier as achieved.** Re-prove after any
config change: one added `-v` flag silently returns tier 2 to tier 0 while the docs
still say tier 2.

**5 — Report honestly.** Current tier, target tier, gap, and the evidence. Then flag
theater if you see it: root inside the container, a mounted docker socket, the host FS
bind-mounted rw, `--net=host`, or the sandbox holding the same credentials as the host.

Isolation bounds damage; it does not buy correctness. Never let "it ran sandboxed"
stand in for review, tests, or evidence.

Target (task / "this session" / tier to verify): $ARGUMENTS

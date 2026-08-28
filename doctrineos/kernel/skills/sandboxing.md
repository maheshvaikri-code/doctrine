---
on: ["intent:sandbox|isolat|blast radius|untrusted|egress"]
cost: read
provides: skill
---

# Skill: Sandboxing & Isolation

**Scope.** Choosing, building, **proving**, and operating the boundary that
agent work runs inside. Distinct from `skills/security.md` (build-time: secrets,
input handling, deps), from `skills/platform-engineering.md` (a sandbox tier is
a paved road, and should be shipped as one), and from `skills/repo-devops.md`
(one repo's tooling). This skill owns the question *what can this agent reach,
and how do you know?*

**Why this skill exists — and why it is now the ONLY answer for shell.**
Doctrine's `PreToolUse` guard governs Write/Edit, where it is sound: one field
names one file. **It no longer runs on Bash at all** (ADR-014). It used to,
reading the command as text, and that was a **tripwire, not a boundary**:
shell is Turing-complete, the path need not appear in the command, and four
independent review rounds each found a new spelling reaching a protected file
(`05-packaging.md`). No static analysis of that text will ever be complete, so
the arm was deleted rather than patched a fifth time. Nothing in Doctrine now
stands between an agent and your filesystem via the shell. If that matters for
your blast radius, the control is here — there is no longer a second layer in
front of it.

A boundary that *is* complete works one layer down, on **effects** rather than
text:

```bash
p=$(echo L2dvbGQvcmVjb3Jk | base64 -d); rm "$p"   # names no path; defeats text analysis
                                                  # on a read-only mount: EROFS, every time
```

The kernel does not care how the write was spelled. **That is the difference
between a tripwire and a boundary, and this skill is how you get the boundary.**
Doctrine does not ship a sandbox and does not provision one — it carries the
doctrine for selecting and verifying yours.

## Principles

- **A boundary you have not tested is a belief.** The only evidence a sandbox
  works is a recorded attempt that it *refused*. A sandbox that has never
  denied anything is unproven, whatever the config file says.
- **Choose the tier from blast radius, not from convenience.** The question is
  never "is this sandboxed" but "what does this reach if the agent is wrong,
  compromised, or prompt-injected — and can I afford that?"
- **Default deny, then open by name.** Writable paths, egress destinations, and
  credentials are allowlists. Anything that starts permissive and gets narrowed
  by exception ends permissive.
- **What you hand in, you have given away.** No tier protects a credential you
  mounted. The strongest control is not a stronger jail — it is the prod key
  never entering the room.
- **Isolation bounds damage; it does not buy correctness.** Inside a perfect
  sandbox an agent can still fabricate results, ship placeholder code, and
  weaken a test. §7 and the review gates are what catch that. Never let "it
  ran sandboxed" stand in for "it was verified."
- **Ephemeral by default.** A long-lived sandbox accumulates state, drifts, and
  becomes a second host you must defend.

## The tier ladder

Pick the lowest tier whose "doesn't stop" column you can genuinely accept.

| Tier | Mechanism | Stops | Does **not** stop | Cost |
|---|---|---|---|---|
| **0** None | agent runs as you, on your host | nothing | everything you can reach: SSH keys, cloud creds, every repo, the browser profile | zero |
| **1** Least privilege | separate OS user, no sudo, ACLs / read-only perms on protected paths | accidental writes, casual overreach, the careless `rm` | anything that user *can* do; privilege escalation | minutes |
| **2** Container | namespaces + read-only mounts + dropped capabilities + non-root + no docker socket | host filesystem writes regardless of shell spelling; most casual escape | kernel bugs (shared kernel); anything you mounted in; anything egress reaches | hours |
| **3** MicroVM / gVisor | Firecracker, Cloud Hypervisor, gVisor — own kernel or syscall interposition | kernel-sharing escapes | hypervisor bugs; deliberate egress of data you supplied | days |
| **4** Separate host | dedicated VM or machine, distinct credentials | everything on *your* machine | whatever that host itself can reach | provisioning |
| **5** Ephemeral remote | managed cloud sandbox, destroyed after each task | persistence between tasks; local blast radius entirely | data you sent in; the provider is now in your trust boundary | $$ + §5 |

**Tiers 3–4 assume an already-safe host.** Container runtimes, microVM
monitors, and remote-sandbox agents all presuppose a hardened machine with
virtualization available and a sane network posture. Provisioning *that* is a
separate job with its own failure modes — do not treat "installed Docker" as
having reached tier 2.

**Escalation is §5.** Tier 5 is a paid external service. Elevating from local
isolation to a remote sandbox means data leaves the machine — escalate before
it does, not after.

## The five things a sandbox must control

Naming them separately matters: most real "sandboxes" control one and are
assumed to control all five.

1. **Filesystem — what is writable.** Mount protected paths **read-only**;
   grant a single writable workspace. Since ADR-014 removed the Bash arm of
   the guard, this is the ONLY control protecting those paths from a shell
   command — not a backstop behind a tripwire.
2. **Network egress — where it can reach.** Default-deny outbound, allowlist
   the package registry and API you actually need. Most exfiltration and most
   "the agent installed something strange" incidents are egress events, and
   egress is the control people skip first.
3. **Credentials — what crosses in.** Enumerate deliberately. A sandbox that
   inherits your shell environment inherits your keys. Prefer short-lived,
   least-scoped, task-specific credentials over a mounted long-lived secret
   (`skills/security.md`).
4. **Lifetime — how long it persists.** Destroy and recreate rather than clean
   up. State that survives a task is state nobody is auditing.
5. **Results — what comes back out.** A reviewable diff is a good egress
   channel; an opaque binary or a "just run this" script is not. What leaves
   the sandbox re-enters your trust boundary and gets reviewed as untrusted
   input (G4).

## Proving the boundary

**Run these inside the sandbox and paste the real output.** Each must *fail*.
An expected failure that succeeds is the finding.

```bash
# 1. Filesystem: a protected path must refuse the write, at the kernel
touch /path/to/protected/canary        # expect: Read-only file system / Permission denied

# 2. Egress: an unlisted destination must not resolve or connect
curl -sS --max-time 5 https://example.com   # expect: timeout / refused / DNS failure

# 3. Credentials: the keys must simply not be present
env | grep -iE 'secret|token|password|_key'  # expect: no output
ls ~/.aws ~/.ssh ~/.config/gh 2>&1           # expect: No such file or directory

# 4. Escape surface: the classic holes must be absent
ls -l /var/run/docker.sock 2>&1        # expect: No such file  (a mounted socket IS host root)
id -u                                   # expect: non-zero (not running as root)
capsh --print 2>/dev/null | head -2     # expect: a dropped, not full, capability set
```

- **Record the output as evidence**, in the QA report or the paved-road doc.
  "We run in Docker" is a claim; a pasted `Read-only file system` is a boundary.
- **Re-prove after every config change.** A boundary verified once is not
  verified forever — one added `-v` flag or one widened egress rule silently
  returns you to tier 0 while the documentation still says tier 2.
- **Know your actual tier before trusting it.** On a developer machine the
  honest answer is usually tier 0. Check rather than assume: `/.dockerenv`,
  `/proc/1/cgroup`, and `systemd-detect-virt` on Linux; the equivalent on your
  platform. An agent that believes it is contained and is not is worse off than
  one that knows it is on the host.

## Sandbox theater — the costume, not the boundary

Each of these is a real configuration that reads as isolation and provides
approximately none:

- `--privileged`, or running as **root** inside the container.
- **The docker socket mounted in.** That is not a sandbox with a convenience —
  it is a root shell on the host with extra steps.
- **The host filesystem bind-mounted read-write.** The namespace is intact and
  entirely beside the point.
- `--net=host`, or any egress policy of "allow all" — the most common gap.
- **The same credentials as the host.** The jail is real; the keys walked in
  with you.
- "It runs in CI" — CI is a build environment, not a containment boundary, and
  it usually holds deployment credentials.

## Honest limits — state these rather than imply their absence

- **Containers share the host kernel.** A container escape is one kernel bug
  away, and those ship regularly. Tier 2 is a strong default and not a
  guarantee; if the blast radius genuinely warrants a guarantee, tier 3+.
- **No tier protects what you deliberately handed in.** Mount the production
  key and the isolation tier is irrelevant to the outcome.
- **A sandbox is a blast-radius control, not a correctness control.** It does
  not make output honest, tested, or correct — those are §7 and G4/G5.
- **Prompt injection crosses boundaries that data does not.** Untrusted content
  the agent *reads* can redirect its behaviour inside a perfect sandbox; the
  sandbox bounds what that redirected behaviour can touch, which is exactly
  why the egress and credential dimensions carry the weight.

## Do

- Select the tier from a written blast-radius judgement, and record it.
- Mount protected paths read-only rather than relying on command inspection.
- Default-deny egress; allowlist by name.
- Give the sandbox its own short-lived, least-scoped credentials — or none.
- Prove the boundary with pasted output, and re-prove after config changes.
- Ship the chosen tier as a paved road with an escape hatch
  (`skills/platform-engineering.md`, `templates/paved-road.md`), so isolation
  is the easy default rather than a per-task act of virtue.

## Don't

- Don't call it sandboxed without a recorded refusal.
- Don't mount the docker socket, run as root, or bind-mount the host FS rw.
- Don't leave egress open because "it needs the internet" — name what it needs.
- Don't let the sandbox inherit your shell environment.
- Don't expect the `PreToolUse` guard to see a shell command at all — since
  ADR-014 it is not wired to Bash. Even on Write/Edit, where it is sound, it
  is a decision at the point of action, not containment.
- Don't let "it ran in a sandbox" substitute for review, tests, or evidence.

## Review checklist

- [ ] Tier chosen from a written blast-radius judgement, not by default
- [ ] Protected paths mounted read-only; single writable workspace
- [ ] Egress default-deny with a named allowlist
- [ ] Credentials enumerated; none long-lived or broader than the task
- [ ] Lifetime ephemeral; destroy-and-recreate rather than clean-up
- [ ] Boundary proof run **inside** the sandbox, output pasted
- [ ] Re-proved after the most recent config change
- [ ] Elevation to a paid/remote sandbox escalated (§5)

## Common failure modes

The container that runs as root · the mounted docker socket · egress left open
because "it needs npm" · the sandbox holding the same AWS profile as the host ·
a tier claimed in docs and never verified in fact · a `-v` flag added months ago
that quietly returned tier 2 to tier 0 · "it ran sandboxed" offered as evidence
the work is correct · a long-lived sandbox nobody audits · assuming Docker
installed means isolation achieved.

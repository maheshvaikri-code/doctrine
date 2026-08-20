# 05 — Packaging & Distribution

Two things ship, on two different vehicles:

1. **The law** (`.Doctrine.md`, `.Doctrine/`, tools, wiring) lives IN each
   governed repo, committed — installed once by `tools/doctrine_install.py`.
   Doctrine is per-repo law; it cannot live in a plugin cache.
2. **The tooling surface** reaches every agent two ways: native wiring
   (hooks/commands/agents) and the **doctrineos MCP server**
   (`tools/doctrine_mcp.py`) — stdlib stdio JSON-RPC exposing
   `doctrine_lint`, `state_{status,verify,hydrate,checkpoint}`,
   `gold_{check,record}` to any MCP-capable agent.

## The installer (any repo, any tool)

```
python tools/doctrine_install.py --target <repo> --tool claude,cursor,codex
                                 [--solobuilder] [--enterprise]
                                 [--startup] [--force] [--local]
                                 [--ci [--ci-provider github|gitlab|azure]]
```

Copies the law + enforcement suite + tests + required companion artifacts
(including the dashboard OpenAPI contract) + Makefile, the AGENTS.md boot
(only if absent), per-tool adapter overlays, and the Claude wiring; appends
(never replaces) CLAUDE.md imports, and writes a single marker-delimited
managed block to `.gitignore`. Files that exist with different content are
skipped with a warning — `--force` is a deliberate act. `--enterprise`
seeds the merge/promotion profile. `--local` makes the managed block cover
the installed framework (corpus, tools, tests, adapters at their variable
paths, MCP registration) instead of just machine-local state, so Doctrine
stays out of the repo's history — one block to add or delete; `docs/`
artifacts remain committable.

Every install seeds `Workforce runtime: maple` — a recorded selection for
OpenHawk's execution layer, not a Doctrine requirement. The installer writes
the marker and nothing else: no package install, no import, no network call. `--maple`
remains accepted as a backward-compatible no-op. `--solobuilder` seeds
`Delivery profile: solobuilder` and, unless already selected,
`Agent latitude: creative`. The profile selects creative Solo Builder work →
deterministic DevOps verification. The latitude field is a portable behavior
policy, not a provider temperature setting; a pre-existing explicit latitude
is preserved. Personal and enterprise profiles are mutually exclusive; startup
is compatible with either.

## Reinstall preservation contract

A reinstall, including `--force`, overwrites only Doctrine-managed corpus,
tools, companion tests/contracts, and selected adapter files. It never writes
repository-owned runtime or planning data under `.doctrine-state/`, `memory/`,
`sessions/`, `docs/plans/`, `docs/briefs/`, `docs/adr/`, `docs/reviews/`,
`docs/qa/`, `docs/releases/`, or `docs/retro/`.

**Removal is confined to the corpus, and only under `--force`.** `--force`
deletes files under `.Doctrine/` that no longer exist upstream — otherwise a
role or skill removed from the doctrine stays installed and selectable forever
(a consumer went on offering a deleted role after a `--force` upgrade). Every
pruned file is **copied to `.doctrine-state/local/prune-backup/<UTC stamp>/`
before deletion** and the location is printed, so the operation is recoverable
rather than merely careful. A plain install removes nothing. Nothing outside
`.Doctrine/` is ever pruned — not `.claude/commands/` or `.claude/agents/`
(a consumer may add its own), not `docs/`, and above all not
`.doctrine-state/`; each of those is pinned by a test. The sole project-brief mutation is append-only: missing profile
markers may be added to `docs/brief.md`; its existing bytes are otherwise
preserved. The fixed dashboard OpenAPI file under `docs/contracts/` is an
explicit Doctrine-managed companion artifact.

`--verify` may initialize missing state-plane structure after copying, but it
must not replace existing checkpoints, decisions, effects, distillates, or
repo-local application state. Regression coverage seeds state, memory,
sessions, and plan artifacts, force-reinstalls Doctrine, and requires every
seeded byte to remain identical.

## The enforcement gate (`PreToolUse`)

`tools/doctrine_guard.py` turns the law into a decision at the point of
action, **for file writes only** (see the strength table below; the durable
guarantee is `doctrine_gold gate`). It reads the runtime's pre-execution
payload on stdin and answers on stdout; the shipped `.claude/settings.json`
and `plugin/hooks/hooks.json` wire it for
`Write|Edit|MultiEdit|NotebookEdit`. Any runtime with an equivalent
pre-execution contract can call it the same way — JSON in, JSON out.

**`Bash` is deliberately absent from that matcher (ADR-014).** The guard used
to run on shell commands too, analysing the command text for paths it would
write. That arm is deleted — not disabled, deleted — because it was known
incomplete by construction (four review rounds, four new bypass spellings)
while charging real friction in false positives on ordinary reads. Doctrine
does not inspect your shell. The `evaluate()` code path for commands still
exists for a repo that deliberately re-adds `Bash` to the matcher: it runs
secrets, §5 irreversible/external, enforcement-config and test-weakening
checks, and then approves. Nothing analyses command paths any more.

| Class | Verdict | Why |
|---|---|---|
| Secret-shaped content in a write or command | **deny** | §7 #2 — never commit secrets |
| Write to a gold record, the state checkpoint, `.env`, or (in a consumer repo) the installed corpus | **deny** | immutable evidence; §12 forbids editing an installed corpus |
| Force-push, history rewrite, `--no-verify`, publish, `terraform destroy`, `curl \| sh` | **ask** | §5 — the human decides irreversible and external actions |
| An edit adding a skip/xfail marker to a test file | **ask** | §7 #4 — never silence a failing test to go green |

Posture: **silent** outside a doctrine repo (the law is not in play);
**fail-closed** inside one — an unparseable request is denied, because a
governed repo must not gain a bypass by malforming a request. Local policy
lives at `.doctrine-state/guard.json`:

```json
{"protected_paths": ["infra/*"], "allow": ["tests/fixtures/*"]}
```

`allow` exempts a path from the path and secret rules — the escape hatch for
legitimate secret-shaped fixtures. A malformed policy file is ignored, never
obeyed, and **an entry that would un-protect the world is dropped even from a
well-formed file** - tested against canary paths rather than a list of
spellings, because `?*`, `*.*` and `docs/*` are off switches too. "Allow
everything" is not a policy.

**The enforcement surface is guarded against a WRITE, and no longer against a
shell command.** This policy file, the hook wiring (`.claude/settings.json`,
`CLAUDE.md`, `AGENTS.md`), `pyproject.toml` (its package name decides whether
the installed corpus is protected here), `.doctrine-state/fleet.json` and
`.github/workflows/` all require an explicit human **ask** before an agent may
change them *with Write/Edit*. An earlier version protected none of these, and
three independent verifiers each disabled the entire guard from inside the repo
it governs with a single write. They **ask** rather than deny because widening
policy is a legitimate human act.

**Read the limit of that sentence, because ADR-014 moved it.** "What must never
happen is the governed party doing it silently" is no longer true through the
shell, and the consequence reaches back into the arm this document calls sound.
A G5 audit demonstrated the full chain, executed end to end:

```text
shell: echo '{"allow":["tools/*",".claude/*"]}' > .doctrine-state/guard.json
       -> allow   (was: ask - nothing inspects a command any more)
Write: tools/doctrine_guard.py        -> allow   (exempted by the policy just written)
Write: .claude/settings.json          -> allow
Write: an AWS key into tools/x.py     -> allow   (`allow` exempts the SECRET rules too)
```

Neither `tools/*` nor `.claude/*` is a blanket pattern, so `is_blanket()`
correctly does not refuse them. **The Write/Edit arm is therefore enforced only
until one unchecked shell command rewrites its policy, its wiring, or its own
source** — no prompt at any point in that chain. This is not the loss ADR-014
set out to accept (that was "shell commands are unchecked"); it is a second-order
consequence of it, recorded here rather than discovered later.

**What actually closes it — and be precise, because the obvious answer is
mostly theatre.** The first draft of this section said "put those paths in
`permissions.deny`". That is only partly true, and the part that is false is
the part that matters:

- **Permission rules are matched per tool, and `Bash(...)` patterns match
  COMMAND TEXT, not paths.** There is no rule form meaning "any command that
  writes this path". `Read(...)`/`Edit(...)` deny rules do reach a *recognized*
  subset of file commands in Bash (`cat`, `head`, `tail`, `sed`) — genuinely
  useful, and worth setting — but they do **not** stop `echo x > path`, a
  redirect, or any subprocess that opens the file itself. Same undecidability
  that retired the guard's own arm; the permission layer does not escape it.
- **The only complete control is the isolation tier**
  (`skills/sandboxing.md`). `sandbox.filesystem.denyWrite` — into which
  `Edit(...)` deny rules are merged — is enforced by the kernel (Seatbelt on
  macOS, bubblewrap on Linux/WSL2), so the write fails however it was spelled.
- **Platform caveat, stated because it decides the answer for many readers:**
  sandboxing is **not supported on native Windows**. On Windows the honest
  position is that this chain is open, and closing it means running Claude Code
  inside WSL2 or a container. Not "configure a rule" — change where it runs.

**Doctrine ships NO permission rules for these paths, deliberately.** They were
added and then removed the same day, and the reason is worth keeping: an `ask`
rule *always* prompts — auto mode cannot clear it and no hook can override it —
and because `Edit(...)` rules also reach the file commands the runtime
recognises in Bash (`cat`, `sed`, `head`, `tail`), shipping them reintroduced
exactly the Bash-level prompting that removing the Bash arm was meant to end.
Partial protection bought with a prompt on every profile is the same bad trade
ADR-014 rejected, one layer up.

So the gap stands, unpatched and stated: an unchecked shell command can rewrite
the guard's policy, and the only thing that closes it is a kernel-enforced
isolation tier (`skills/sandboxing.md`), unavailable on native Windows. An
operator who wants the permission-layer partial coverage should add those
`Edit(...)` rules to **their own** settings knowingly, accepting the prompts. It
is not Doctrine's call to impose them. Same lesson as "nothing inside a
repository the agent can write is tamper-proof against that agent", now
applying to the guard's own policy file.

### Three in-repo layers, and none of them is a containment boundary

| Layer | What it is | Strength |
|---|---|---|
| The guard on **Write/Edit** | structured input: one field names one file | Sound *for the paths it is given*: the path is data, not a language to interpret |
| The guard on **Bash** | *nothing — removed in ADR-014* | **No coverage at all, by design.** It was a tripwire; a tripwire that costs friction and stops no determined write is worse than an honest gap |
| `doctrine_gold gate` | re-checks records against git and a manifest | **Tamper-evident, not tamper-proof** — see below |
| **The isolation tier** (`skills/sandboxing.md`) | read-only mounts, default-deny egress, no inherited credentials | **The actual boundary** — enforced by the kernel, not by reading text. Not shipped by Doctrine; selected, built, and **proved** by you |

**Nothing inside a repository the agent can write is tamper-proof against that
agent.** An earlier version of this table claimed `gate` was "Sound. Tampering
fails regardless of how it was written." That was false: the gate re-hashed
each referenced file against a hash *stored in the record being verified*, so
editing the record and recomputing its own hashes passed — including a forged
`human_approval` and a council verdict flipped to a veto. A record is written
after its tag, so no signature ever covered it. A **second** round of
independent review then showed the fix — anchoring on git's committed copy —
was itself narrower than the words around it claimed. Both corrections are
folded in below rather than layered as a third retelling.

**What `gate` actually verifies: has this evidence changed since the LAST
commit that touched it?** Concretely:

- **Any edit to a record already committed, left uncommitted, is caught** —
  its bytes no longer match git's copy of it (EOL-normalized, so an honest
  Windows clone under `core.autocrlf=true` is not flagged as tampering).
- **Deletion or relocation is caught whether or not it was committed** — git's
  *history* on the gold directory (`git log`), not only its current tree, is
  the anchor; `git mv docs/releases lib && git commit` cannot make the gate
  say "nothing was ever promoted" merely because HEAD's tree is now empty.
- **A record git has never seen at all is refused** — hand-writing JSON next
  to a fresh tag and committing it is caught, because there is no prior
  version to compare against, and "no anchor" fails closed rather than
  passing on trust.
- **Git being unreachable fails closed**, not silently as "there is nothing to
  check" — a broken or absent git binary denies the gate rather than passing it.

**What it cannot do, stated precisely rather than gestured at:** if an actor
with ordinary commit access forges a record's content and commits that forgery
in the **same, single commit** — no amend, no force-push, no history rewrit —
the gate has nothing to diff against and passes. This is the same limit as
S1/S7 in the round-5 review: a HEAD-relative check cannot see a forgery whose
only recorded state ever agreed with itself. **Nor is "CI running this gate on
the pushed commit" a second anchor for that case** — CI checks out the same
HEAD the forgery was committed to and reaches the identical answer. The
control that catches an in-commit forgery is a **human reading the diff**:
`git log -p -- docs/releases/gold/` on every release-bound merge, and branch
protection that makes that diff unavoidable before the merge lands. Gate
locally and in CI for the classes above; review the diff for this one.

The Bash rule was for a long time described as a tripwire, because three
independent security passes each found new spellings that reached a protected
file — wrapper verbs, newline segmentation, nested shell strings, program text,
long-form output flags, process substitution. Each round was fixed; each next
round found more. That is not a run of bad luck: **shell is Turing-complete,
and no static text analysis of it is complete.** A gate whose guarantee rests
on enumerating spellings is a gate that will be wrong again.

**ADR-014 finished that argument by removing the rule.** A fourth review round
found more spellings, and a live session found the other half of the bill: the
same analysis denied ordinary read-only work whenever it could not classify
the command (a path named inside a `python -c`, a loop, an unlisted verb).
Paying friction for a control that is incomplete by construction is the worst
of both; Doctrine now states the gap instead of dressing it. `Bash` is out of
the `PreToolUse` matcher and the path-analysis code is deleted.

So the durable guarantee is moved to where it cannot be spelled around:

```
python tools/doctrine_gold.py gate       # every record re-hashed
```

`doctrine_verify` runs it automatically when `docs/releases/gold/` exists or
git's history has ever held a record, and the CI templates run it on every
push. A record edited *after* it was committed fails there, whoever or
whatever edited it — a tool call, a shell redirect, `awk`, an editor, a script
nobody reviewed. A record forged and committed in one step is a different
class the gate cannot see (above) — that needs a human on the diff, not
another automated check.

A pre-commit hook is **not** recommended here. The gate compares the worktree
against HEAD, and a record has no HEAD copy to compare against until *after*
its own promoting commit exists — so a correctly-installed hook refuses the
very commit that files the genesis record, and the shebang-less version
documented in an earlier revision of this file refused *every* commit,
silently, because git could not spawn it at all. If a local pre-merge check
is wanted, run the gate against the merge commit in CI instead, where a full
history is guaranteed to exist.

**What replaced it: nothing in-repo, and that is the honest answer.** Doctrine
no longer inspects shell commands. Two earlier attempts to keep a partial hold
— a narrow "every verb is a proven reader with no redirect" grant, then a
blanket grant for `Delivery profile: solobuilder` — are both gone with the
rest of the arm. They were the right shape for a control worth keeping; the
control was not worth keeping.

What still governs a shell command, in order:

- **Your own `permissions.deny` / `permissions.ask` lists.** These are the
  runtime's, not Doctrine's, and they outrank any hook decision — documented
  behaviour: a matching deny blocks the call and a matching ask still prompts
  even when a hook returned `allow`. This is where a rule you actually want
  enforced on shell belongs.
- **The isolation tier** (`skills/sandboxing.md`) — the only real boundary.
- **§5 and §7 as prose.** The agent is still bound by them; nothing mechanical
  checks them for shell. Say so rather than implying otherwise.

A repo that wants the old behaviour back can add `Bash` to the matcher in
`.claude/settings.json`: the command branch in `evaluate()` still runs
secrets, §5 irreversible/external, enforcement-config and test-weakening
checks before approving. What it will not do again is analyse command paths.

**Where the containment boundary does come from.** Since no parser of a
Turing-complete shell can be complete, a stronger parser is the wrong
investment; the boundary belongs one layer down, on **effects** rather than
text. A path mounted read-only refuses `rm`, `>`, `python -c`, `find -exec`,
and every spelling nobody has thought of yet — the kernel returns `EROFS`
without reading the command. Egress default-deny does the same for
exfiltration, and a sandbox holding no credentials makes the question moot.
Selecting that tier against the blast radius, and **proving it with a recorded
refusal rather than asserting it from a config file**, is `skills/sandboxing.md`.

Doctrine ships no sandbox and provisions none — that is deliberate, since a
container requirement would stop it installing into any repo on any OS with
zero dependencies. It carries the playbook; the agent and its operator run it.
Since ADR-014 there is no second layer to pair it with for shell: the mount
*is* the guarantee, and there is no tripwire in front of it any more.

Honest limits, measured rather than assumed:

- Pattern matching finds known credential formats, not every secret. A value
  with no credential-shaped name, or one containing spaces, is not caught, and
  a secret **assembled across two separate tool calls** is never seen whole.
  Pair it with a real scanner at G5 (`skills/security.md`).
- Command enforcement resolves the paths a command *names*. A path built at
  runtime — `cd docs/releases && echo x > gold/f.json`, or one assembled from
  a shell variable — is beyond a pre-execution text check.
- It binds only runtimes that honour a pre-execution hook, and only the tools
  its matcher lists. MCP filesystem/exec servers are ungoverned.
- It gates four checkable non-negotiables, not all ten.

## Fleet view (many repos, one posture)

```
python tools/doctrine_fleet.py status ../repo-a ../repo-b
python tools/doctrine_fleet.py status --root .. --json
```

Reports each repo's doctrine version, drift from this source tree (`current` /
`behind vX` / `ahead` / `modified` / `incomplete`), state-plane posture,
worktree cleanliness, release distance, and gold-record count. Repos also come
from `.doctrine-state/fleet.json` (`{"repos": ["../a", "../b"]}`).

Strictly read-only, and exit 1 when any repo drifts — so a scheduled job can
watch a portfolio. Drift is repaired by reinstalling
(`doctrine_install.py --target <path> --force`), never by hand-editing an
installed corpus.

## Install matrix

| Agent | Doctrine law | Commands/agents | Tooling access |
|---|---|---|---|
| **Claude Code** | `/doctrine-init` (plugin) or installer `--tool claude` | Plugin: `/plugin marketplace add <this repo>` → `/plugin install doctrine@doctrine-marketplace` — ships /checkpoint, /doctrine-init, /doctrine-verify, /gold-check, 14 subagents, SessionStart hydrate hook | plugin `.mcp.json`, or `claude mcp add doctrineos -- python tools/doctrine_mcp.py` |
| **Codex CLI/IDE** | installer `--tool codex` (AGENTS.md native) | custom prompts: copy `plugin/commands/*.md` into `~/.codex/prompts/` | `config.toml`: `[mcp_servers.doctrineos] command="python" args=["tools/doctrine_mcp.py"]` |
| **Cursor** | installer `--tool cursor` (rules overlay) | — (AGENTS.md + rules drive behavior) | `.cursor/mcp.json` with the same server entry |
| **Windsurf** | installer `--tool windsurf` | — | MCP plugin config with the same entry |
| **GitHub Copilot** | installer `--tool copilot` | — | repo `.vscode/mcp.json` / org MCP registry |
| **Gemini CLI** | installer `--tool gemini` | `gemini-extension.json` may wrap the commands | `settings.json` `mcpServers` entry |
| **Cline / Roo / Amazon Q / Continue / Junie** | installer `--tool <name>` | — | each tool's MCP config, same server entry |
| **Anything else** | installer (AGENTS.md boot) | — | MCP if available; else the CLIs directly |

## Python packaging

`pyproject.toml` builds a `doctrineos` wheel with console scripts
(`doctrine-state`, `doctrine-lint`, `doctrine-gold`, `doctrine-mcp`,
`doctrine-install`, `doctrine-metrics`, `doctrine-signature`,
`doctrine-awaken`, `doctrine-guard`, `doctrine-fleet`, and the
loopback-only `doctrine-dashboard`) for `pipx
install` distribution. The wheel carries the TOOLS only — the law travels by
repo: `doctrine-install` needs a doctrine source tree (`--source <clone of this
repo>`). **Publishing to PyPI or any registry is an external action: explicit
human go required**
(`.Doctrine.md` section 5), through the G6 release checklist — and on an
enterprise repo, from a gold record.

## Versioning rule

The plugin manifest, marketplace entry, pyproject, and MCP serverInfo
carry the doctrine version; bump them with the `.Doctrine.md` header in
the same commit (the corpus lint checks version sync with the CHANGELOG).

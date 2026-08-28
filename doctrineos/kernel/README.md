# The kernel

The corpus DoctrineOS can actually reach. Every file here carries an
**activation contract** in its frontmatter:

```yaml
---
on: ["path:migrations/**", "path:**/*.sql", "intent:migration|schema"]
cost: read
---
```

`doctrineos context` evaluates those against the task and returns exactly the
set that fires — and says *why*, so a wrong trigger is diagnosable rather than
mysterious.

## Generated, not hand-edited

Built by `tools/build_kernel.py` from the
[doctrine](https://github.com/maheshvaikri-code/doctrine) corpus:

```
DOCTRINE_REF=/path/to/doctrine python tools/build_kernel.py
```

Edit the **manifest in that script**, not the files here — a hand-edited kernel
silently becomes a fork of the doctrine, and nothing would say so. The manifest
also keeps every trigger in one reviewable place instead of scattered across
29 files, which is what made a real over-firing bug obvious on sight.

The build wipes `kernel/` first. A file left behind from an earlier manifest
would still **activate** — the engine scans this directory rather than reading
a list — which is the same defect `init --prune` exists for.

## Cost and the threshold rule

`cost` declares what firing this resource actually spends:

| cost | meaning | may be fired by |
| --- | --- | --- |
| `read` | put a file in context | anything, including weak intent |
| `adopt` | take on a lens or a role | deterministic or declared signals only |

`provides` says WHAT KIND of thing it is, and that matters because a lens and
a role both cost `adopt` but compose differently. **Lenses stack** — each adds
load paths and narrows write scope. **Roles are worn one at a time and
announced** (`02-role-protocol`). So `context` returns them separately, and the
`roles` list is a set of CANDIDATES: the engine can compute which hats the work
matches, but not which one the task is being done under.

That asymmetry is the design, not an implementation detail: a keyword someone
happened to type may hand you a document, but it may not change what you are
allowed to do. See [`../docs/02-ACTIVATION-MODEL.md`](../docs/02-ACTIVATION-MODEL.md).

Lenses here trigger on **path only**. `class:L` was tried and removed: it made
every large task adopt every lens, so a Class-L refactor that touched no
database still took on the database lens.

## Two honest limitations

**This is a curated subset, not the whole corpus.** 45 resources out of the
doctrine's 196 — 22 skills, 16 roles, 5 standards, 2 lenses. The rest are not missing by accident — a resource earns a place
here only if firing it changes what the agent does *and* the trigger can be
expressed in a signal the engine evaluates (`path:`, `repo:`, `class:`,
`intent:`). Domain overlays (`compose`) and subagents (`dispatch`) are not yet modelled —
both cost tiers exist in the engine with zero resources declaring them.
Templates fit no tier at all: they are instantiated, not read.

25 of the 41 roles are absent **because they have no deterministic trigger** —
growth-marketer, legal-ops, investor-relations, the governance heads, the
domain specialists. The threshold rule forbids weak intent from firing an
`adopt`, and that is right: putting on a hat with authority and hands-off
boundaries because someone typed a keyword is the "wrong signal, wrong price"
failure v1 had. Those roles are named by the human instead.

**Prose cross-references point at the full corpus.** These files were written
for the doctrine repo and cite things like `skills/metrics.md` that DoctrineOS
does not ship. The references are informational and were left intact rather
than silently rewritten; follow them in the doctrine repo. The generated
`## Signature` block *is* stripped, because it lists roles and skills that do
not exist here and would put dangling references in front of an agent.

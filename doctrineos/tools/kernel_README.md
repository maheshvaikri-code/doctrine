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
| `adopt` | take on a lens: checks, tool grant, write scope | deterministic or declared signals only |

That asymmetry is the design, not an implementation detail: a keyword someone
happened to type may hand you a document, but it may not change what you are
allowed to do. See [`../docs/02-ACTIVATION-MODEL.md`](../docs/02-ACTIVATION-MODEL.md).

Lenses here trigger on **path only**. `class:L` was tried and removed: it made
every large task adopt every lens, so a Class-L refactor that touched no
database still took on the database lens.

## Two honest limitations

**This is a curated subset, not the whole corpus.** 29 resources out of the
doctrine's 196. The rest are not missing by accident — a resource earns a place
here only if firing it changes what the agent does *and* the trigger can be
expressed in a signal the engine evaluates (`path:`, `repo:`, `class:`,
`intent:`). Roles, domain overlays, and templates are not yet modelled.

**Prose cross-references point at the full corpus.** These files were written
for the doctrine repo and cite things like `skills/metrics.md` that DoctrineOS
does not ship. The references are informational and were left intact rather
than silently rewritten; follow them in the doctrine repo. The generated
`## Signature` block *is* stripped, because it lists roles and skills that do
not exist here and would put dangling references in front of an agent.

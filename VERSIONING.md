# Versioning and Compatibility

Doctrine follows [SemVer](https://semver.org/) and is currently **0.x — under
active development**. Under 0.x, a **minor** bump may carry a breaking change;
the changelog says so explicitly when it does.

## What a version number covers

Doctrine ships a corpus *and* tools, so "breaking" means more than an API
signature. One version number covers all of it:

| Surface | Example of a breaking change |
|---|---|
| **The corpus** | a role or skill renamed or removed, so `roles/x.md` references stop resolving |
| **Gate semantics** | a class requiring a gate it previously did not |
| **Non-negotiables** | adding or materially widening a §7 rule |
| **Tool CLIs** | a flag removed or its meaning changed |
| **State-plane schema** | a checkpoint field older tools cannot read |
| **Artifact schemas** | a gold-record field required where it was optional |
| **Guard policy** | denying a class of action that was previously allowed |

Adding a skill, role, template, or domain pack is **additive** — a minor bump,
not a breaking one, even though the counts move.

## Version carriers, kept in lockstep

The version appears in several places and **lint fails if they desync**:

- `.Doctrine.md` — the header line (the source of truth)
- `CHANGELOG.md` — the top release heading
- `pyproject.toml`
- `plugin/.claude-plugin/plugin.json`
- `tools/doctrine_mcp.py` — the MCP `SERVER_INFO`
- `README.md` — the version badge

Never bump one by hand. `python tools/doctrine_lint.py` is the check.

## Upgrading an installed repo

An installed corpus is a **read-only snapshot**. Do not hand-edit it — the
installed `.Doctrine/` is a copy, and local edits are silently lost on the next
install and will make the repo drift invisibly.

```bash
python tools/doctrine_fleet.py status                  # what drifted, and how far
python <doctrine>/tools/doctrine_install.py \
    --target <your-repo> --force                       # roll it forward
cd <your-repo> && python tools/doctrine_verify.py      # confirm green
```

`--force` overwrites files whose content differs. Without it, the installer
**skips** differing files and reports them — which is why a hand-edited corpus
quietly stops receiving updates.

### Drift is normal; silent drift is the problem

A fleet of repos will sit on different versions. That is fine. What is not fine
is not knowing. `doctrine_fleet status` is a read-only view of every governed
repo's version, drift, state and release distance.

## Release process

Releases run through the doctrine's own **G6** gate:

1. Gates green — `make verify` (corpus lint, ruff, tests, gold gate)
2. Version bumped in every carrier above; `CHANGELOG.md` updated in
   [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) form
3. Public surface documented (§7 #8)
4. Annotated, signed tag
5. On `Merge profile: enterprise` repos, promotion from a **gold record** with
   the council verdict content-pinned

**Publishing is always a human decision** (§5). No release, tag push, or
registry publication happens automatically, and none of it is done by an agent
without an explicit human go.

## Distribution and what carries the law

Only the repository carries the corpus. This matters when you plan an upgrade:

| Channel | Carries tools | Carries the corpus |
|---|---|---|
| Git clone + `doctrine_install.py` | ✅ | ✅ |
| Claude Code plugin | ✅ (commands, agents, hooks) | ❌ — `/doctrine-init` installs from a source tree |
| MCP server (`doctrineos`) | ❌ — registers tools only | ❌ |
| Python wheel | ✅ (11 console scripts) | ❌ |

The wheel is deliberately tools-only, and **is not published to PyPI**.
`doctrine-install` from a wheel still needs `--source <clone>`.

## Multi-repo products

If a product ships Doctrine alongside other components, pin the whole stack per
release with
[`templates/compatibility-manifest.md`](.Doctrine/templates/compatibility-manifest.md).
Dependency direction is fixed by
[ADR-003](docs/adr/003-product-family-topology.md): `product → {doctrine,
maple}`, with `doctrine ⟂ maple` — no cycles. Doctrine depends on neither.

## Python support

**Python 3.11+**, stdlib only. Dropping a Python version is a breaking change
and gets a changelog entry.

## Deprecation

Within 0.x, deprecated surfaces are marked in the changelog and kept working
for at least one minor release where practical. Compatibility aliases are
preferred over hard removals — `--maple`, for instance, remains accepted as a
no-op after MAPLE selection became universal.

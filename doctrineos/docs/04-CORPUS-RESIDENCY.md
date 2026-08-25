# DoctrineOS — where the corpus lives and how it is used

**Date:** 2026-08-25 · **Status:** G1 detail spec

---

## The constraint that decides the layout

An obvious design is: keep one corpus in `~/.doctrineos/` and have the agent read from there. **It does not work**, and the reason is worth stating before the layout.

Claude Code restricts file reads to the project directory plus any explicitly configured `additionalDirectories`. Other hosts have comparable sandboxes, and an agent in a container may have no home directory worth the name. So a corpus that lives *only* outside the repo is a corpus the agent frequently **cannot read** — and requiring every user to add a directory to their settings reintroduces exactly the per-machine setup step that A1 exists to eliminate.

Equally, copying 230 corpus files into every repo is what produced the documented drift (15 installs spread across v0.6.19–v0.6.46).

**The resolution: store once, materialise per repo.**

---

## Layout

### Machine level — the store (write-once, content-verified)

```
~/.doctrineos/
├── bin/doctrineos                 the binary (or anywhere on PATH)
├── store/
│   ├── 0.8.0/
│   │   ├── MANIFEST.json          sha256 of every file + the corpus root hash
│   │   ├── kernel/
│   │   │   ├── law.md             Tier-0. hard cap ~2k tokens.
│   │   │   ├── skills/*.md        ~20 cross-cutting
│   │   │   ├── lenses/*.md        ~8, each with paths + tool grant
│   │   │   └── templates/*.md
│   │   └── packs/
│   │       ├── security-operations/
│   │       ├── domains/healthcare/
│   │       └── …                  v1's corpus, carried whole
│   └── 0.7.3/                     older pins stay; repos may differ
└── cache/                         downloads, before verification
```

Versions are immutable once written. Two repos on two versions is normal and supported.

### Repo level — what is actually committed

```
repo/
├── doctrine.toml            ~20 lines. THE install artifact.        [committed]
├── .doctrine/               materialised corpus, exact pinned bytes [gitignored]
├── .doctrine-state/         memory, hash chain, distillates          [committed]
├── docs/adr|plans|reviews|qa/   the artifacts                        [committed]
└── .claude/settings.json    hook wiring                              [committed]
```

**`.doctrine/` is materialised, not authored.** The binary writes it from the store and verifies it against `MANIFEST.json`. The agent reads ordinary repo-relative paths — `.doctrine/kernel/skills/database.md` — so **no host sandbox, no `additionalDirectories`, no symlink or Windows-junction problem**. Bytes are stored once per machine; the repo gets a verified copy.

### `doctrine.toml` — the entire committed surface

```toml
[doctrine]
version = "0.8.0"
sha256  = "9f2c…"                     # pins the exact corpus. drift becomes impossible.

[packs]
enable = ["core", "security-operations", "domains/healthcare"]

[profile]
delivery = "solobuilder"              # ceremony, not capability
merge    = "standard"

[local]
extend = ".doctrine-local/"           # optional: repo-owned skills/lenses, COMMITTED
```

A pull request adding DoctrineOS is these twenty lines — reviewable — instead of 254 files nobody reads.

---

## Vendored mode: one layout, two git policies

A1 is absolute: air-gapped or offline must never block an agent.

| | Thin (default) | Vendored (fallback) |
|---|---|---|
| `.doctrine/` | gitignored, materialised from store | **committed** |
| Needs store/network | yes, once per version per machine | no |
| Drift risk | none — hash-pinned | v1's model: each repo carries its own |
| Repo weight | 20 lines | ~2 MB |

**Identical directory layout; only the `.gitignore` line differs.** Switching is `doctrineos vendor` / `doctrineos thin`. Nothing else in the repo, the hooks, or the agent's reading habits changes — which is what makes the fallback safe to rely on rather than a second architecture.

---

## Resolution order (deterministic, A7)

```
1. read doctrine.toml            -> version + sha256 + packs
2. is .doctrine/ present and matching MANIFEST?   -> use it, done
3. is the version in ~/.doctrineos/store/?        -> materialise, verify, use
4. network available?             -> fetch to cache, verify sha256, promote, materialise
5. is .doctrine/ committed (vendored)?            -> use it, warn that the pin is unverified
6. otherwise -> FAIL LOUD with the exact command to fix
```

Step 6 matters for agents specifically: an unresolvable corpus must produce **one actionable line**, never a silent degrade. An agent that half-loads a corpus will confidently apply half a law.

---

## How it is used, per lifecycle event

### Install (once per repo)
```
$ doctrineos init
  wrote doctrine.toml            (0.8.0, packs: core)
  materialised .doctrine/        (230 files, verified against MANIFEST)
  added .doctrine/ to .gitignore
  wired .claude/settings.json    (PreToolUse, SessionStart, Stop)
  -> commit doctrine.toml and .claude/settings.json
```

### Session start — Tier 0, hard-capped
The `SessionStart` hook runs `doctrineos context --session-start`, which emits **only**:
- `kernel/law.md` (~2k tokens, capped — the entire per-session tax)
- hydrated state from `.doctrine-state/` (agent fact 2: the one thing an agent cannot reconstruct)
- the names of installed packs — *names only, never contents*

The 77-row routing table is **not** loaded. It no longer exists as a thing to read.

### Per task — activation resolves; nothing is browsed
```
$ doctrineos context --task "add a column to the orders table" --paths migrations/0007.sql
{
  "read":     [".doctrine/kernel/skills/database.md",
               ".doctrine/kernel/skills/testing.md"],
  "adopt":    ["database"],
  "template": [".doctrine/kernel/templates/adr.md"],
  "why": {
    "database.md": "path:migrations/** matched migrations/0007.sql"
  }
}
```
The agent `Read`s the returned paths. **It never scans the corpus** — activation is computed by the binary and explains itself (`why`), so a wrong trigger is diagnosable rather than mysterious.

### Per tool call — the guard
`PreToolUse` → `doctrineos check` → `allow` / `deny` / `ask`. Reads only `doctrine.toml` and the lens scopes; no corpus load. This is the hot path and it stays cold.

### Turn end — the Stop gate
`Stop` → `doctrineos gate --done`. If the declared class is M/L and the required artifacts are absent from `docs/`, refuse to end the turn. Fails **open** on its own errors — a Definition-of-Done gate that bricks a session is worse than the gap it closes.

### Upgrade — one operation, not N
```
$ doctrineos upgrade --to 0.9.0        # in one repo: rewrites the pin, re-materialises
$ doctrineos upgrade --all             # every repo with a doctrine.toml
```
Because the pin is committed, an upgrade is a **reviewable diff of one line** — and a rollback is `git revert`. Contrast v1, where an upgrade was a `--force` reinstall of 254 files, and where one such reinstall shipped the source machine's own `settings.local.json` into consumers.

---

## Where each kind of thing lives, and why

| Thing | Lives | Committed? | Reason |
|---|---|---|---|
| Kernel law, skills, lenses, templates | store → materialised `.doctrine/` | no (thin) | identical everywhere; pinned by hash |
| Packs (SOC, domains, founder-ops, marketing) | same | no (thin) | enabled per repo in `doctrine.toml` |
| **Repo-local skills / lenses** | `.doctrine-local/` | **yes** | genuinely repo-specific; nobody else's business |
| **Artifacts** (ADRs, plans, reviews, QA) | `docs/` | **yes** | **the product.** layer-4 provenance. |
| **State** (chain, distillates, decisions) | `.doctrine-state/` | **yes** | agent fact 2 + A6. must survive a fresh container. |
| Hook wiring | `.claude/settings.json` | **yes** | must be present before the binary runs |
| The pin | `doctrine.toml` | **yes** | the whole install |
| The binary | `~/.doctrineos/bin` or PATH | no | machine-level, versioned separately |

**The rule:** *what the repo produced* is committed; *what the repo consumes* is pinned.

---

## What this buys, checked against the criteria

| | |
|---|---|
| **A1** present without asking | Static binary, no runtime. Vendored mode covers offline. |
| **A6** state in repo | `.doctrine-state/` + `docs/` committed; survives a fresh container. |
| **A7** deterministic | `sha256` pin + `MANIFEST` verification. Six repos on three versions is a **stated fact**, not a discovered one. |
| Drift | Structurally impossible in thin mode. `doctrine_fleet` becomes unnecessary rather than necessary. |
| Context cost | Tier 0 capped at ~2k tokens. Activation computed, not browsed. |
| Review surface | 20 lines instead of 254 files. |
| Usage telemetry | `doctrineos context` logs what it emitted — which finally answers *which skills earn their keep*, with data instead of intuition. |

---

## Open questions

1. **Is `.doctrine/` materialisation worth the disk?** ~2 MB per repo, duplicated across repos on the same machine. Content-addressed hard-links would remove it; hard-links across Windows drives fail. **Recommendation: copy first, optimise later only if it bites.**
2. **Should `doctrineos context` return paths or content?** Paths let the agent Read normally and keeps the binary simple. Content lets the binary enforce a token budget and log usage precisely. **Recommendation: paths by default, `--content` for MCP hosts where filesystem reads are awkward.**
3. **Who owns `.gitignore` edits?** `init` writing to a repo's `.gitignore` is a small intrusion. **Recommendation: write a managed block with begin/end markers, as v1 already does.**

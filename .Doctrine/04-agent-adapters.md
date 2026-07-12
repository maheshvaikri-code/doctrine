# 04 — Running the Doctrine on Any Coding Agent

The doctrine is agent-agnostic: it is markdown on disk, and every serious
coding agent can Read files. Only the **ignition** differs per tool — which
file the agent auto-loads at session start. This doc wires that ignition.

## The model: one boot file + thin overlays

- **`AGENTS.md`** (repo root) is the canonical universal boot — the open
  standard read natively by Codex, Cursor, Windsurf, GitHub Copilot,
  Gemini CLI, Aider, Zed, Devin, Jules, Amp, and others. It compresses the
  prime directive, non-negotiables, loop caps, and the read-`.Doctrine.md`-
  first instruction into <3 KB (Codex truncates oversized doc files, and
  short beats long for instruction-following everywhere).
- **Tool-native overlays** are optional belt-and-suspenders for editors
  with always-on rule slots. They are thin pointers (<1 KB) — never fork
  doctrine content into them. Single source of truth stays `.Doctrine.md`;
  AGENTS.md is its compression; overlays are its address.

## Install map (files ship in `.Doctrine/adapters/`)

| Tool | Copy adapter to | Notes |
|------|-----------------|-------|
| **Codex CLI/IDE** | `AGENTS.md` → repo root | Native; nested AGENTS.md files: closest-to-edited-file wins — in monorepos, drop a two-line pointer per package |
| **Cursor** | `AGENTS.md` → root, plus `cursor-doctrine.mdc` → `.cursor/rules/doctrine.mdc` | `.mdc` is `alwaysApply: true`; legacy `.cursorrules` not needed |
| **Windsurf** | `AGENTS.md` → root, plus `windsurf-doctrine.md` → `.windsurf/rules/doctrine.md` | Rule set to always-on (frontmatter `trigger: always_on`; if a Windsurf version ignores it, set activation to "Always On" in the rules UI). Limits: 6,000 chars/file, 12,000 total — our overlay is ~0.8 KB |
| **GitHub Copilot** | `AGENTS.md` → root, plus `copilot-instructions.md` → `.github/copilot-instructions.md` | Applies to chat, review, and the coding agent |
| **Gemini CLI** | `GEMINI.md` → repo root (AGENTS.md too) | Or set `contextFileName` to AGENTS.md in settings |
| **Cline** | `AGENTS.md` → root, plus `cline-doctrine.md` → `.clinerules/doctrine.md` | Folder form scales to more rules later |
| **Roo Code** | `AGENTS.md` → root, plus `roo-doctrine.md` → `.roo/rules/doctrine.md` | Applies across all Roo modes |
| **Amazon Q Developer** | `AGENTS.md` → root, plus `amazonq-doctrine.md` → `.amazonq/rules/doctrine.md` | Project rules auto-load in chat/agent |
| **Continue** | `AGENTS.md` → root, plus `continue-doctrine.md` → `.continue/rules/doctrine.md` | Rules dir is read per-workspace |
| **JetBrains Junie / AI Assistant** | `AGENTS.md` → root, plus `junie-doctrine.md` → `.junie/guidelines.md` | Junie also reads AGENTS.md natively |
| **Aider** | `AGENTS.md` → root | Or `aider --read AGENTS.md`; a `CONVENTIONS.md` pointer also works |
| **Zed / Amp / Devin / Jules / opencode / Junie** | `AGENTS.md` → root | All read the standard natively |
| **Claude Code** | already wired | `CLAUDE.md` line `@.Doctrine.md` + shipped `.claude/agents/` (see `.Doctrine.md` §11) |
| **Anything else** | `AGENTS.md` → root | If it can't auto-load, first message: "Read AGENTS.md, then .Doctrine.md, and follow them." |

## Capability degradation — what changes off Claude Code

1. **No subagents** (Codex today, Copilot, Aider, most others): the
   parallel protocol (`03-parallel-execution.md`) degrades to **serial
   role-switching** in one session, PLUS fresh-session verification:
   run G4/G5 verifiers in brand-new sessions seeded only with the role
   card + diff + brief. Never let the verifier session see the build
   session's reasoning.
2. **No `@import`**: AGENTS.md instructs the agent to Read `.Doctrine.md`;
   verify early in a session that it did (ask it to state the task class).
3. **Weaker file discipline**: some agents bulk-ingest. If you see it
   quoting deep `.Doctrine/` files unprompted, restate: routing table
   only, progressive disclosure.
4. **Cloud/paid actions**: tools with auto-approve modes (Cursor YOLO,
   Windsurf turbo) must have publish/deploy commands on the deny list —
   escalation gates assume a human is actually asked.

## Sync rule

When the doctrine changes materially (new non-negotiable, new gate, new
skill), regenerate the AGENTS.md compression as a Class-S change. The
overlays almost never change — they carry only the address and the
unchanging hard rules.

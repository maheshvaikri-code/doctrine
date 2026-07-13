# Implementation Plan — Doctrine Enforcement Tooling
<!-- G2 artifact. Brief: docs/brief.md -->

## Steps
1. **[Backend] `tools/doctrine_state.py`** — canonical JSON writer;
   sha256 helpers; minimal JSON-Schema validator (type, const, enum,
   required, properties, additionalProperties:false, items, maxItems,
   minimum, minLength, maxLength, pattern, anyOf, $ref → $defs);
   commands: init, checkpoint (propose→dispose: stamp at_commit/seq/
   created_at, chain prev_sha256, write checkpoint + history copy +
   distillate, append decision_refs to NDJSON, prune-with-merge),
   verify (chain links, monotonic seq, state_index re-hash), hydrate
   (7 sections, budgets 800/200/1200/1600/800/1000/400 tokens ≈ 4 chars,
   degrade rules, STALE@ prefixes, header with bundle_sha256, --check
   double-compile), prune, status.
   *Design decision:* pruned distillates' dead_ends merge into the NEW
   distillate at checkpoint time (stored artifacts stay immutable; the
   schema cap of 8 applies, drops reported). Proposal file supplies
   session_id + control + distillate body; validator stamps the rest.
2. **[Backend] `tools/doctrine_lint.py`** — corpus checks (brief §Scope 2);
   imports the validator from doctrine_state for example checks;
   allowlist for upstream-repo references (`skills/ponytail/SKILL.md`).
3. **[QA] `tests/test_doctrine_state.py` + `tests/test_doctrine_lint.py`**
   — unittest; temp git repos for chain tests; determinism, tamper,
   prune-merge, degrade, lint pass/fail cases.
4. **[DevOps] `Makefile` (test/lint targets) + `.github/workflows/doctrine.yml`**.
5. **Fix `state-plane/examples/*.json`** to canonical bytes (they carry
   trailing spaces today — violates STATE.md canonicalization).
6. **[G4/G5] Verifier fan-out**: code-reviewer + security-reviewer +
   qa-engineer subagents over the new code → docs/reviews + docs/qa;
   fix findings; then CHANGELOG 0.2.0 + tag.

## Risks / rollback
Schema-validator subset must cover exactly the constructs the two schemas
use — test against both examples and hand-broken variants. Windows paths:
use pathlib throughout; LF enforced by writing bytes. Rollback: tools are
additive; reverting the tag removes them cleanly.

## v0.3.0 slice — session wiring (added 2026-07-12, Class M)
7. **[Backend] `hydrate --if-present`** (exit 0 on empty plane, for
   hooks) and **`hydrate --emit-agents`** (marker-managed
   `<!-- doctrine:state:begin/end -->` block in root AGENTS.md; replace
   between markers, append block if absent, skip+note if no AGENTS.md;
   idempotent for unchanged state).
8. **[DevOps] Claude Code wiring**: `.claude/settings.json` SessionStart
   hook running `hydrate --if-present`; CLAUDE.md gains the bundle
   import line; `.claude/commands/checkpoint.md` wraps the checkpoint
   protocol as a slash command. Stop-hook auto-checkpoint deliberately
   NOT implemented: distillates are model-authored — a mechanical hook
   cannot write an honest one (documented in 04-agent-adapters).
9. **[Docs] `04-agent-adapters.md`** gains a State-plane wiring section;
   HYDRATION.md notes the reference implementation.
10. **[QA] tests** for --if-present and all --emit-agents paths;
    then G4/G5 fan-out on the delta.

## v0.4.0 slice — enterprise merge & promotion profile (2026-07-12, Class M)
OPT-IN profile (activated by `Merge profile: enterprise` in docs/brief.md);
the default gates stay unchanged for non-enterprise repos.
11. **[Docs] `standards/merge-and-promotion.md`**: Merge Council (unanimous
    independent sign-offs for protected-branch merges of Class L /
    release-bound work), permission matrix (role → merge/tag/promote/
    deploy rights → enforcement mechanism), Gold Build ladder
    (candidate → soak → gold record with hash-chained provenance;
    deploy only from gold; rollback = previous gold record).
12. **[Docs] `templates/merge-verdict.md`** (council verdict record) and
    **[Interop] `schemas/gold-build.schema.json`** (additionalProperties
    false, prev_gold_sha256 chain like checkpoints).
13. **[Backend] `tools/doctrine_gold.py`**: `record --input` (stamps
    at_commit from the tag, hashes artifacts, chains to previous gold,
    refuses missing sign-offs/verdict/human approval) and `check --tag`
    (schema + re-hash + chain + referenced-files + tag/commit match).
    Reuses canonical_bytes/validate/load_json from doctrine_state.
14. **[QA] tests**; wiring (routing row, G6 enterprise note, README
    counts); delta G4/G5; tag v0.4.0; checkpoint 3.

## v0.5.0 slice — packaging & distribution (2026-07-12, Class L)
Doctrine CONTENT installs into repos (committed law); TOOLING ships as
plugin + MCP + installer. Publishing to any registry stays human-gated.
15. **[DevOps] `tools/doctrine_install.py`**: copy .Doctrine.md,
    .Doctrine/, .claude/{agents,commands,settings.json}, CLAUDE.md,
    AGENTS.md + selected adapter overlays into a target repo.
    `--tool claude|codex|cursor|windsurf|copilot|gemini|cline|roo|
    amazonq|continue|junie|all`, `--enterprise` seeds the brief line,
    idempotent, refuses to clobber newer files without --force,
    never overwrites an existing CLAUDE.md/AGENTS.md silently (append
    import / marker block instead).
16. **[Interop] `tools/doctrine_mcp.py`**: stdlib stdio MCP server
    (newline-delimited JSON-RPC: initialize, tools/list, tools/call,
    ping) exposing doctrine_lint, state_{status,verify,hydrate,
    checkpoint}, gold_{check,record} — works in Claude Code, Codex,
    Cursor, Windsurf, Copilot, Gemini via each tool's MCP config.
17. **[DevOps] Claude Code plugin**: `plugin/` (.claude-plugin/
    plugin.json, commands/, agents/, hooks/hooks.json, .mcp.json) +
    root `.claude-plugin/marketplace.json` → `/plugin marketplace add
    <repo>` + `/plugin install doctrine`. Drift hazard managed by NEW
    lint parity checks: plugin/agents ≡ .claude/agents,
    plugin/commands/checkpoint.md ≡ .claude/commands/checkpoint.md.
18. **[Docs] `.Doctrine/05-packaging.md`**: install matrix per tool
    (Claude plugin/manual, Codex AGENTS.md+MCP+prompts, Cursor/Windsurf
    rules+MCP, Gemini extension, generic). README/§11 pointers.
19. **[DevOps] `pyproject.toml`** (name `doctrineos` — see naming
    decision; console scripts doctrine-state/-gold/-lint/-mcp/-install);
    wheel build verified locally; PUBLISHING requires the human (§5).
20. **[QA] tests** (installer round-trip into temp repo; MCP protocol
    handshake + tool call over real stdio subprocess; parity lints);
    review round #4; tag v0.5.0; checkpoint 4.

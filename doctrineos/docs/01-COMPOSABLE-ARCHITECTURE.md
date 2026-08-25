# DoctrineOS — the composable architecture

**Supersedes** the "drop list" in `00-THESIS-AND-PLAN.md` Part 3. That framing was wrong.
**Date:** 2026-08-25 · **Status:** G1 architecture proposal

---

## The principle

**Nothing is deleted. Doctrine v1 becomes the library; DoctrineOS becomes the composition.**

The earlier plan asked "what do we cut?" That was the wrong question, and it was wrong for a reason worth naming: **the 90% of the corpus that went unused this session was not unused because it was bad. It was unused because this session didn't build a healthcare product, run a SOC, or ship a data pipeline.** Absence of demand in one session is not evidence of absence of value. Deleting on that basis would be exactly the reasoning error the doctrine forbids everywhere else.

The right question is: **what does a stranger meet on the first screen, and how does everything else stay one command away?**

That is progressive disclosure — Doctrine's own stated design principle — applied to **distribution** instead of only to reading.

```
doctrineos init                    -> kernel. small. one gate, one refusal.
doctrineos add security-operations -> the SOC corpus, intact
doctrineos add domains/healthcare  -> the overlay pack, intact
doctrineos add founder-ops         -> the startup roles, intact
```

Every pack is v1's work, carried forward whole, versioned, and installable. The corpus stops being a wall and becomes a catalogue.

---

## Three buckets, by evidence

### Bucket 1 — KERNEL: proven by receipts, ships by default

Each of these earned its place in *this session*, with a specific catch. Nothing is in the kernel on intuition.

| Mechanism | The receipt |
|---|---|
| **Hash-chained state + hydration** | Implements agent fact 2 (memory resets). No competitor ships it. |
| **Gold records / content-pinned verdicts** | The entire competitive survey found **no equivalent anywhere**. The moat. |
| **`PreToolUse` guard, Write/Edit arm** | Denied a real gold-record write, verified live — **including from a dispatched subagent**. |
| **Dispatched fresh-context verification** | Caught invalid YAML that would have silently disabled every CI gate; caught 7 untracked files that would have shipped a corpus claiming 69 skills to consumers receiving 62; caught the guard self-disarm chain the builder missed. |
| **Anti-fabrication law (§7 #1)** | Caught the maintainer four separate times this session. |
| **ADR / plan / review / QA artifacts** | The layer-4 product. Durable, diffable, outlive any vendor. |
| **Core skills** (~15–20) | `loop-engineering`, `debugging`, `testing`, `security`, `sandboxing`, `ai-slop`, `repo-devops`, `cicd`, `engagement-engineering`, `architecture`, `requirements`, `observability`, `error-handling`, `dependency-policy`, `git-conventions`. Agent-native, cross-cutting, used constantly. |

### Bucket 2 — PACKS: good work, situational demand, installable whole

Carried forward **unchanged**, as versioned packs. Not demoted — *catalogued*.

| Pack | Contents | Why it's a pack, not core |
|---|---|---|
| `security-operations` | soc-analyst, detection-engineer, incident-responder + 4 skills | Superb work. Needed by teams running a SOC — which is not the median repo. |
| `domains/*` (16) | healthcare, finance, quant, aerospace… | The regulatory overlays are genuinely differentiated. Demand is per-industry by definition. |
| `founder-ops` (7 roles) | growth, content, sales, support, finance, legal, IR | Real, draft-only, useful to a solo founder. Not software development. |
| `governance` (4 heads) | head-of-ai, head-of-data, ciso, risk-officer | Enterprise-shaped. Belongs where an enterprise asks for it. |
| `marketing` (10 skills) | brand → localization, built this session | Same logic. Ships as a pack the day it's wanted. |
| `data-and-ml` | data-engineer/architect, DBA, analyst, ml-engineer + skills | Deep and correct; loaded only by repos that do this work. |
| `enterprise-merge` | merge council, gold ladder, compatibility manifest | Only meaningful on `Merge profile: enterprise`. |
| `cloud/*` (7) | aws, azure, gcp, vercel, railway, render, fly | Already effectively dynamic — one is fetched when a provider is chosen. |

**Nothing above is judged inferior.** A pack is how good work reaches the person who needs it without taxing the person who doesn't.

### Bucket 3 — CORRECT: carry forward, but fix first

"Avoid the bad" means **repair**, not discard. These are defects, and shipping them into a fresh start would launder them.

| Defect | Why it's a defect (not just unused) | Fix |
|---|---|---|
| `Workforce runtime: maple` stamped unconditionally (`doctrine_install.py:481`) | Contradicts the corpus's own corrected position. Every install carries a retracted claim. | Honour the `maple` parameter; stamp only when asked. |
| **Two inert `FEATURES.md` toggles** (`drift-banner`, `state-plane`) | Advertise controls **nothing reads**. An advertised control that does nothing is worse than an honest gap — and it caused a wrong recommendation to the maintainer this session. | Wire them, or demote them to "describes behaviour, not a switch." Every toggle must be read by code or relabelled. |
| **Mandatory engagement ritual on every task** | A per-turn token cost paid before any work, on Class S typo fixes as much as Class L migrations. Benefit unmeasured. | Fire on **risk**, not on existence. |
| **The "software company" framing** | The metaphor that drove surface area past demand. BMAD deleted personas at 52k stars; AWS shipped gate-free Quick Spec. | Reframe as **lenses** (checks + tool grant + file scope). The v1 role cards become each lens's reference text — kept, repurposed. |
| **Guard positioned at layer 2** | Weakest there, duplicates the vendor, and `allowManagedHooksOnly` switches it off. | Keep the sound Write arm; state the layer-2 limit plainly; move the emphasis to layers 3–4 where nothing can disable it. |
| **Mid-workflow enforcement gap** | Write-time and release-time are enforced; between them is narration. Cost proven this session. | The `Stop`-event Definition-of-Done gate. |

---

## The pack mechanism

A pack is a directory with a manifest. Nothing exotic.

```
packs/security-operations/
  pack.toml            name, version, requires, description
  roles/*.md           carried from v1, unchanged
  skills/*.md          carried from v1, unchanged
  routing.toml         the §6 rows this pack contributes
  templates/*.md       optional
```

**The routing table becomes generated, not hand-maintained.** Today `.Doctrine.md` §6 is ~77 hand-written rows — a file that must be edited every time anything is added, and which drifted this session (the three marketing skills existed for weeks while being routed from nowhere). With packs declaring their own rows, **the table assembles itself from what is installed.**

Three wins from one change:
1. The first screen is short because only the kernel's rows exist.
2. A row can never point at an uninstalled file — the class of defect that shipped seven untracked skills.
3. Adding a pack cannot silently fail to be reachable.

**Measurement comes free.** `doctrineos add <pack>` is a demand signal. After twenty repos you will know which packs are real — replacing the aesthetic argument about surface area with data, permanently.

---

## What DoctrineOS *is*, in one screen

```
Layer 1  containment   -> your sandbox         (not ours; we help you pick)
Layer 2  permission    -> your agent vendor    (not ours; a deny rule outranks us)
Layer 3  process       -> DoctrineOS kernel    OURS
Layer 4  provenance    -> DoctrineOS records   OURS
```

> **Your agent vendor decides what the agent may do.
> DoctrineOS decides how work gets done — and proves it afterwards.**

Kernel = **memory** (state plane), **evidence** (gates + artifacts + reviewer identity), **refusal** (guard + Stop gate). Three nouns, three agent facts, one command to install.

---

## Sequence

**Phase 0 — decide.** Approve this architecture, the Go spike, and the Bucket-3 fix list.

**Phase 1 — spike.** One Go binary: `guard`, `stop`, `verify`. Prove ~2 ms startup here and that hooks fire from Claude Code. **If Go doesn't beat Python measurably on this machine, the decision reverses on evidence.**

**Phase 2 — port the moat.** Gold records + state plane into Go, with **v1's Python suite kept as a differential oracle**: both run identical fixtures and must agree byte-for-byte. That is how a rewrite avoids silently losing four rounds of adversarial hardening.

**Phase 3 — pack the library.** Mechanical: v1's corpus → packs, unchanged content, plus a manifest and routing rows each. Nothing is rewritten. Nothing is lost.

**Phase 4 — kernel corpus.** The ~20 core skills, ~8 lenses, 3 default gates (L-class can still expand to 7).

**Phase 5 — first screen.** README, one-command install, and the refusal demo as a checked-in `vhs` tape regenerated in CI.

**Phase 6 — cut over.** New repo, rename, claim `doctrineos` on PyPI and npm, repoint. Only when 1–5 are green.

**v1 stays.** Tagged, intact, and the canonical source every pack is cut from. It is not deprecated; it is the library.

---

## What could still make this wrong

- **Pack granularity is a guess.** Eight packs may be four or twenty. Install telemetry answers it; the initial split should be held loosely.
- **Generated routing is new machinery.** It removes a drift class and adds a build step. The build step must fail loudly, or it trades a visible problem for an invisible one.
- **The lens reframe is a bet, not a finding.** BMAD's persona deletion is evidence against the *org-chart metaphor* — not proof that lenses work better. Phase 4 should test it, not assume it.
- **A vendor may ship layers 3–4 natively.** Qodo's *Skill Review Standards* is the leading indicator. If that lands, differentiation narrows to portability.

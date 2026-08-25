# Plan: DoctrineOS — positioning, hardening, and the usage model

**Class:** L · **Date:** 2026-08-25 · **Owner:** Chief Architect → Product Owner for scope
**Evidence base:** `supportfolder/Doctrine-Market-Position-and-GTM.md` (4 research lanes, primary-source verified) + one empirical test run in-repo.

> **Rule for this plan.** Every change below stands or falls on its own merits and carries its own evidence, cost, and risk. Nothing is bundled. If you reject item 4, items 1–3 are unaffected. Anything I could not verify is labelled.

---

## Part I — What the stack actually is, and how each layer should be used

The single clearest thing the research produced is that **Doctrine has been describing itself at the wrong layer.** There are four layers in an agent-governed repo. Doctrine owns exactly one, touches a second, and should stop implying it owns the others.

| Layer | Who owns it | What it answers | Doctrine's role |
|---|---|---|---|
| **1. Containment** — kernel/OS | A sandbox (Kiro Crew, container, VM, `garagebox`) | *What can the process physically touch?* | **None.** Doctrine ships no sandbox and must keep saying so. `skills/sandboxing.md` selects one. |
| **2. Permission** — runtime | The agent vendor: Anthropic managed settings, `permissions.deny/ask`, Cursor Team Rules, Copilot policy | *May this agent perform action X, anywhere?* | **None, and this is not a gap.** It is machine-scoped and coarse by design. Doctrine should *defer* to it and document that a deny rule outranks any hook. |
| **3. Process** — repository | **Doctrine** | *Has this change passed G0→G7, by whom, with what evidence?* | **Owns it. This is the product.** |
| **4. Provenance** — artifact | **Doctrine** | *Can I prove afterwards what was decided, reviewed, and shipped?* | **Owns it.** Hash-chained state + gold records. No competitor sells this. |

**Why this framing matters commercially:** the research found every vendor control plane answers layer 2 and none answers layers 3–4. Cursor's audit log is 19 event types covering auth, membership, and API keys — a *SaaS account* trail. It records that Alice's role changed; it cannot record that the security reviewer signed off on the auth change. That is the whole opening.

**Why it matters technically:** Doctrine currently has a `PreToolUse` guard operating at layer 2, where it is (a) weakest, (b) duplicative of the vendor, and (c) **switchable off by `allowManagedHooksOnly`**. Its irreplaceable work is at layers 3–4, where nothing can turn it off because the artifacts are committed files.

### How Doctrine should be used (the usage model to document)

```
Layer 1  sandbox            <- you provide (skills/sandboxing.md picks one)
Layer 2  permissions.deny   <- you configure in YOUR agent, once
Layer 3  DoctrineOS gates   <- per repo, per task class
Layer 4  DoctrineOS records <- committed, diffable, auditable forever
```

One sentence for the README: **"Your agent vendor decides what the agent may do. DoctrineOS decides how work gets done, and proves it afterwards."**

---

## Part II — The changes, each justified independently

### Change 1 — Make the repository public
**Merit:** Adoption is mechanically zero. `gh repo view` returns `"isPrivate":true, "stargazerCount":0`; the public API 404s. Every other item in this plan is downstream.
**Cost:** One switch. **Risk:** None that is not already accepted by intending to open-source it.
**Do it first, before anything else on this list.**

### Change 2 — Rename to DoctrineOS
**Merit — verified, not aesthetic.** The current name is unfindable:

| Collision | Verified scale |
|---|---|
| npm `doctrine` (ESLint JSDoc parser) | **123,957,578 downloads in one week** |
| PHP `doctrine/orm` | 10,170 stars, owns `doctrine-project.org` since 2010 |
| PyPI `doctrine` | Taken by another author |

A user types one name, installs another (`doctrineos`), and searches a third. Organic discovery is structurally impossible.

**`doctrineos` is free in all three namespaces — verified this session:**
- npm `doctrineos` → **404, unclaimed**
- PyPI `doctrineos` → **404, unclaimed** *(note: your `pyproject.toml` already declares `name = "doctrineos"` but has never been published — the name you depend on is currently squattable by anyone)*
- `github.com/maheshvaikri-code/doctrineos` → **does not exist, free**

**This is the lowest-cost rename that will ever be available**: the package name, the MCP server name, and the plugin identity are *already* `doctrineos`. The rename makes the human-facing name match the machine-facing one that shipped months ago. It is a correction, not a rebrand.

**Timing is the whole risk.** Renaming after a launch essay costs the essay's inbound links. Renaming now costs a `git remote set-url` and a find-and-replace.
**Cost:** ~1 hour. **Risk:** low now, high later.
**Sub-action, independent merit:** publish `doctrineos` to PyPI as a placeholder even if you do nothing else — an unclaimed name your build already declares is a supply-chain exposure.

### Change 3 — Rewrite the tagline and the first screen
**Merit — the strongest evidence in the study.** Seven 2026 Show HN posts pitching *governance / guardrails / operating layer for AI agents* scored **1, 1, 2, 2, 3, 3, 3**. Essays pitching the identical idea as *"how I stop my agent lying to me"* scored **837, 524, 435, 394, 232, 196, 142**.

The idea sells; the vocabulary repels. The current tagline — *"A gated engineering operating layer for AI coding agents for Enterprise/Startup/SoloBuilder Profiles. (Developer Preview)"* — is a category noun + a segmentation matrix + a disclaimer, in that order.

The README's **failure table is already correct** and is buried below it. Lead with the failure. Name one mechanism nobody else has.
**Cost:** an afternoon. **Risk:** none. **Independent of the rename** — worth doing even if the name stays.

### Change 4 — Reviewer-identity stamping (claim the empty slot)
**Merit — this is the only place the research found genuinely unoccupied ground.** No open-source project mechanically enforces *the builder cannot approve its own build*:
- `flow-next` (687★) enforces **dispatch** — the verdict is authored by a separate binary — but has no check that the reviewer isn't the same model family.
- **GitHub** blocks PR self-approval, but keys on *account identity* — one bot token defeats it.
- `agentic-os`, `agent-pr-flow`, `FC-FUZ` all gate on **whether** a review artifact exists, never **who wrote it**.

Doctrine already does the hard architectural half — and I **verified this session** that dispatched subagents *do* trigger the guard, so the mechanism is real. What is missing is proof.

**Build:** each verifier writes its verdict with a stamp (agent type + dispatch id). `doctrine_verify` and the gold gate **refuse G4/G5 when the reviewer stamp is absent or equals the builder stamp.**
**Cost:** moderate — touches the verifier cards, the review template, and two tools.
**Payoff:** per this survey, it would make DoctrineOS **the first OSS project mechanically enforcing reviewer identity.** That is a headline an essay can carry.

### Change 5 — `Stop`-hook Definition-of-Done gate
**Merit — closes the band the research showed is Doctrine's real hole.** Doctrine enforces at **write-time** (`PreToolUse`) and **release-time** (`doctrine_gold` content-pinning), and **nothing in between**. Whether a Class-M task produced its G4 review is currently narration.

**This session supplied the proof:** seven new skill files were left untracked and would have shipped a broken install — the corpus claiming 69 skills while a consumer install received 62. Only a dispatched reviewer caught it. A `Stop` gate that refuses to end a turn when declared-class artifacts are missing would have caught it mechanically.

Precedent exists: `FC-FUZ/claude-code-governance` registers a `Stop` hook (`gate-browser-verify.py`) for exactly this.
**Cost:** one hook event, stdlib-only, ~100 lines. **Risk:** must fail *open* on its own errors — a Definition-of-Done gate that bricks the session is worse than the gap.
**This is the highest value-per-line item on the list.**

### Change 6 — Document the managed-settings degraded mode
**Merit — §7 #1 requires it.** Anthropic ships keys that disable Doctrine: **`allowManagedHooksOnly`** (only managed hooks run → `doctrine_guard.py` does not execute) and **`strictPluginOnlyCustomization`** (blocks skills/agents/hooks/MCP from *project sources* → `.claude/agents/` verifiers do not load).

The enterprises most likely to set those keys are exactly the ones Doctrine targets. **A buyer must not discover this; the README must state it.**
**Sub-action:** test empirically whether those keys disable the guard here, then document the true degraded behaviour (layers 3–4 survive because artifacts are files; layer 2 enforcement does not).
**Cost:** a test plus a README section. **Risk of not doing it:** a credibility failure on precisely the honesty the project sells.

### Change 7 — Progressive disclosure for the *human*
**Merit — Doctrine's own stated principle, never applied to the reader.** `obra/superpowers` (**277,129★**, solo maintainer, same category) won on *"a folder of Markdown that pulls in one doc under 2k tokens"* — Simon Willison quoted that line specifically. DoctrineOS presents **69 skills, 41 roles, 16 domains, 7 gates, 3 profiles** at the door.

**And the field has a receipt against surface area:** BMAD-METHOD (52,230★) shipped many personas and then **deleted its QA agent and Scrum Master agent** in v6.3.0 (2026-04-09), folding them into the developer. AWS shipped **Quick Spec** with *"no approval gates between phases"* — the vendor with the most spec telemetry in the world responding to ceremony fatigue.

**Do not delete the corpus.** Change the *first run*: one gate, one visible refusal, everything else discoverable later.
**Cost:** a README restructure + a minimal-install path. **Risk:** none to existing users.

### Change 8 — Ship a demo of the guard *refusing* something
**Merit:** "it actually stops something" is precisely what the seven 1-to-3-point governance posts could not show. You have a real refusal — this session produced one verbatim.
**Constraint that is not optional:** author it as a checked-in `vhs` tape regenerated in CI. A project whose first law is *never fabricate* cannot ship a hand-recorded demo that drifts from real output.
**Cost:** half a day. **Risk:** none.

### Change 9 — Fix the two inert FEATURES.md toggles
**Merit — an advertised control that does nothing is worse than an undocumented gap.** `drift-banner` and `state-plane` are documented as switches; `doctrine_engage.py` contains **no reference to `doctrine_features` at all**, and the state hook never checks. Setting either to `off` changes nothing.

I gave you a fix earlier that relied on `drift-banner: off` working. **It would not have worked.** That is exactly the failure this project exists to prevent, committed by its own maintainer.
**Two options, both defensible:** wire them (~10 lines each), or demote them in the table to "describes behaviour, not a switch."
**Cost:** trivial either way. **Do not leave it as-is.**

### Change 10 — Resolve the `Workforce runtime: maple` installer defect
**Merit:** `doctrine_install.py:481` stamps `Workforce runtime: maple` into **every** consumer brief unconditionally, ignoring its own `maple` parameter, under a comment reading *"MAPLE is the universal workforce selection"* — the exact framing the corpus was corrected away from. The fix never propagated to the installer (same class as ADR-012).
**Cost:** Class M — 4 tests and 3 corpus files must move together. **Risk of not fixing:** every install carries a claim the doctrine has formally retracted.

---

## Part III — What NOT to do

- **Do not pitch compliance.** EU AI Act **Annex III was read directly**: eight categories, and software development appears in none. High-risk deadlines slipped to **2027-12-02**; Article 4 weakened from *ensure* to *support*. ISO 42001 has ~350 certified orgs worldwide. NIST AI RMF is voluntary. SOC 2 has no AI criteria. **"EU AI Act compliance for your codebase" would be selling something the regulation does not ask for — a §7 #1 violation.** The true, narrower version: *when your SOC 2 auditor asks who approved the agent's privileged action, you have a signed, hash-chained record instead of a shrug.*
- **Do not relicense.** Every backlash case (MongoDB, Elastic, HashiCorp→OpenTofu at 29,901★, Redis→Valkey) tracked **retroactivity**, not destination. MIT from birth is an asset for a governance tool.
- **Do not compete on the markdown layer.** `AGENTS.md` is Linux Foundation-stewarded (Agentic AI Foundation, formed 2025-12-09; AWS, Anthropic, Google, Microsoft, OpenAI) and claimed at 60k+ projects. Instruction files are free infrastructure now. Ride the spec; don't fight it.
- **Do not submit the repo link to HN.** `spec-kit` was submitted **eight times and never cleared 7 points** (it has 131,171 stars — from GitHub's own blog). Superpowers' essay scored **435** while its repo link scored **1**.
- **Do not build more corpus before Changes 1–3.** Surface area is currently a liability, not an asset.

---

## Part IV — Sequence

**Gate A — unblock (hours).** Change 1 (public) → Change 2 (rename + claim `doctrineos` on PyPI/npm) → Change 3 (tagline). *Nothing else can start until A is done; the naming decision expires the moment a launch essay publishes.*

**Gate B — earn the claim (days).** Change 5 (`Stop` gate — highest value per line) → Change 4 (reviewer stamping — the unoccupied slot) → Change 9 (inert toggles) → Change 6 (degraded-mode honesty).

**Gate C — presentable (days).** Change 7 (progressive disclosure) → Change 8 (refusal demo) → Change 10 (maple defect).

**Gate D — only then, distribution.** `/plugin marketplace add` install path (the community catalog lists **652 plugins** — under-competed), then one first-person essay on your own domain titled around the failure, **not** submitted by you. Then, 14+ days later with visible commits, `awesome-claude-code` (hard-gated at 14 days or 100 stars).

**The honest reason for this order:** B and C are what make the essay in D *true*. Changes 4 and 5 give it a claim nobody else can make. Publishing before B/C means launching on the same "governance framework" pitch that scored 1–3 points seven times.

---

## Part V — What this plan does not resolve

- **Whether 41 roles is right.** BMAD's reversal is evidence against, not proof. Change 7 defers the question by hiding surface area rather than cutting it — deliberately, because deleting roles is irreversible and the evidence is one competitor's product decision.
- **Whether the Python runtime should stay.** Measured here: **1,875 ms** bare Python startup vs **391 ms** for Node, on this machine, with `-S` barely helping. But `node -e ''` at 391ms is *also* ~15× slow, so the machine is taxing all spawns. **Test a Defender exclusion on `C:\Program Files\Python312` before considering any rewrite** — it plausibly recovers most of it at zero cost. If it does not, port only the hot path (`doctrine_guard` + `doctrine_engage`, ~1,300 lines) and leave the other eleven tools alone.
- **Whether the vendor ships gated-SDLC-with-artifacts first.** Qodo's *Skill Review Standards* — governance of the agent's own configuration files — is the leading indicator. If a vendor ships layers 3–4 natively, DoctrineOS's differentiation collapses to portability alone.

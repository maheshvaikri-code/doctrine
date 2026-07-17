# Retrospective — Doctrine self-evolution v0.6.10 → v0.6.18 · 2026-07-16
<!-- G7 artifact. Filed per templates/retrospective.md. Author: Project Reviewer.
     Arc-level retro (nine releases), not a single-feature retro. This is the
     second retro in the repo's history and the first run per-version-arc —
     see "the meta-finding" below. -->

## Facts (no interpretation yet)

**Shipped:** nine releases in ~4 days (2026-07-13 → 2026-07-16):
- **Added (features):** v0.6.10 Engagement Protocol · v0.6.11 MAPLE runtime integration (opt-in) · v0.6.12 Turnkey install (`--verify`/`--maple`, QUICKSTART) · v0.6.15 Product-family topology (ADR-003 + compatibility-manifest template) · v0.6.18 Platform Engineering role+skill + four PaaS cloud skills.
- **Fixed (consumer-safety):** v0.6.13 `doctrine_verify` consumer-scoped (`is_source_repo`) · v0.6.16 `check_version` consumer-safe (pyproject) · v0.6.17 `check_version` whole-bug-class sweep (CHANGELOG too).
- **Changed:** v0.6.14 MAPLE integration → maple-oss 1.1.2 (all five asks shipped; separation-of-duties now broker-enforced, closing the v0.6.11 caveat).

**Gates walked (uneven — this is the arc's headline):**
- The **structural** work of this era dogfooded fully: `state-tooling` (v0.2.0) ran a complete G0→G7 with a filed retro; `productization` filed brief + plan + QA; ADRs 001–003 are filed G1 decisions.
- The **incremental version bumps** (v0.6.10–v0.6.18) engaged the gates *lightly* — Engagement Block + `doctrine_lint`/`doctrine_verify` + CHANGELOG — and largely **skipped the artifact trail** (no briefs/reviews/QA). v0.6.18 (this session) ran G2–G5 + lint/verify green but filed no brief, review, QA, or retro.
- **G7 ran once** in the entire arc (`2026-07-12-state-tooling`) until this document.

**Defects escaped past release:** the **consumer-vs-source bug class escaped three separate releases** — v0.6.13 (`verify` ran host ruff+tests), v0.6.16 (`check_version` flagged a consumer's own pyproject version), v0.6.17 (the sibling CHANGELOG check in the *same function* had the identical flaw). **Each was found live in a consumer repo** (MAPLE once, OpenHawk twice), never by Doctrine's own gates.

## What worked (keep doing)

- **Dogfooding *through real consumers* surfaced what self-tests could not.** Installing Doctrine into MAPLE and OpenHawk and running it is what caught every consumer-safety defect. The self-suite (green in-source) was structurally blind to them. Keep installing into real consumers.
- **The state plane captured the dead-ends as they happened.** This retro is mostly *assembly* — the distillate's `dead_ends` list already held the consumer-safety trap, the `json.dumps` trailing-space bug, the mtime chain-head forgery, the `list[:-0]` prune no-op, the Windows cp1252 crashes. Capturing dead-ends at the moment of learning is the single practice that made a per-arc retro cheap.
- **Honest deferrals, recorded, not silently dropped.** v0.6.15 deferred the *running* family gate "until the `openhawk` repo exists" (a gate over a missing repo is unenforceable) with the rationale written. v0.6.11's separation-of-duties caveat was explicitly *closed* in v0.6.14, not left dangling.
- **Fix-the-whole-bug-class — once it fired (v0.6.17).** After v0.6.16 fixed only the pyproject instance, v0.6.17 swept the entire `check_version` function and caught the CHANGELOG sibling. That sweep is the correct move; the finding below is that it fired two occurrences too late.
- **The Engagement Protocol is actually being followed.** Every change in this arc (incl. this retro) opened with the block; the ritual is real, not aspirational.

## What failed or hurt

- **One bug class, three field escapes, three separate emergency-shaped fixes.** The consumer-vs-source assumption (v0.6.13 → v0.6.16 → v0.6.17) is the dominant defect of the arc. Doctrine's own tooling repeatedly assumed "I am running in the source repo," and the *field* — a real consumer install — was the only thing that disproved it.
- **No consumer-context test harness.** Doctrine's self-tests run in the source repo, where the source-assumption is invisibly true. There is no automated "install into a synthetic consumer and assert the tools behave consumer-safely" gate — so the class had nowhere to be caught before a human hit it in MAPLE/OpenHawk.
- **The whole-bug-class rule depended on memory, not a trigger.** v0.6.16 shipped a one-instance fix; the identical sibling check sat un-audited in the same function until it broke in the field. Doctrine's own non-negotiable ("fix the whole bug class") existed but nothing *forced* the class-audit at find-time.
- **Uneven self-application (the meta-finding).** Big changes dogfood fully; incremental ones half. G7 ran once across nine releases; the rich dead-end stream was captured but never *formalized into §12 doctrine improvements*. Learning was recorded; the loop that turns learning into doctrine edits was not being closed. **This retro is the correction — and its own existence proves the gap: it took an explicit prompt to run the gate the doctrine already mandates.**

## Root causes (5-whys on the dominant escaped defect)

**Defect — the consumer-vs-source bug class** (three field escapes: `verify` ran host code; `check_version` flagged consumer pyproject; then consumer CHANGELOG).

1. **Why did the tools misbehave in consumer repos?** They assumed source-repo context — ran the host's tests, treated any `pyproject`/`CHANGELOG` version as a Doctrine carrier.
2. **Why did they assume source context?** They were written *and tested* only in the source repo, where "I'm in the source repo" is invisibly, always true — the assumption never got a chance to fail in the suite.
3. **Why wasn't the consumer path tested?** No consumer-context fixture exists. Self-tests are in-source; the consumer surface had no gate, so its correctness was asserted only by field use.
4. **Why did the fix recur three times instead of once?** Each fix repaired the *instance* found in the field. The "is this same wrong assumption present elsewhere?" sweep did not fire until the third occurrence (v0.6.17) — and even then only for one function.
5. **Why didn't the class-sweep fire earlier?** The "fix the whole bug class" non-negotiable is a *value*, not a *gate*: nothing in the pipeline forces a class-audit when a consumer-safety (or any implicit-context) defect is found. It depended on the author choosing to look.

**Root:** **tooling gap** (no consumer-context test harness — amendment 1) **+ process gap** (no class-audit trigger at find-time — amendment 2), compounded by the field being the only place the source-assumption could fail. Neither is a knowledge gap: the lessons were captured in the distillate each time; they were not *institutionalized* into a check.

## Doctrine & tooling amendments (concrete, or it didn't happen)

Per §12 the Project Reviewer does not edit doctrine; each row is **proposed**, to be routed through the normal Class-S path with this file as the evidence link and the human's approval.

| # | Amendment | Target file / CI check | Class-S change filed? |
|---|-----------|------------------------|-----------------------|
| 1 | **Consumer-context test harness.** Add a test that installs Doctrine into a *synthetic consumer* (non-`doctrineos` `pyproject`, a product `CHANGELOG`/version, host `tools/`+`tests/`) and asserts consumer-safe behavior: `doctrine_lint` does not flag the consumer's version carriers; `doctrine_verify` runs corpus lint+state only and skips host ruff/tests. This is the gate that would have caught all three field escapes before release. | new `tests/test_consumer_safety.py` (+ CI) | proposed — not yet filed |
| 2 | **Class-audit trigger.** New rule: when a defect rooted in an *implicit-context assumption* (consumer-vs-source, platform, encoding) is found, the fix does not ship until every sibling site of that assumption in the same function/module/tool is audited and swept. Makes the v0.6.17 lesson a gate, not a memory. | `standards/dos-and-donts.md` | proposed — not yet filed |
| 3 | **Right-size but close the self-application gap.** Doctrine's own Class-M+ changes (new role/skill/discipline/tool) file at least a one-paragraph brief and a self-review note in `docs/`; and a **G7 retro runs per version-arc** (per milestone or every ~N releases), not once. Small changes stay lint+verify+CHANGELOG (correct). | §12 note in `.Doctrine.md` (+ a short `CONTRIBUTING` process line) | proposed — not yet filed |
| 4 | **Retro-from-distillate cadence.** Since the state plane already accumulates `dead_ends`, the arc retro's "negative findings" section is seeded from the distillate entries since the last retro — turning captured learning into a closed §12 loop by default rather than by prompt. | `state-plane/STATE.md` (retro hook) | proposed — not yet filed |

## Honest negative findings worth remembering

Recorded so they are not re-tried from optimism (source: the session distillate `dead_ends` + this arc's CHANGELOG):

- **"I'm in the source repo" is a recurring, invisible trap.** Any Doctrine tool that touches the filesystem, versions, or tests must be asked "what does this do inside a *consumer*?" *before* it ships. It escaped three times (verify, version-pyproject, version-CHANGELOG); it will reappear wherever the assumption is made silently.
- **A one-instance fix to a bug class *is* the recurrence.** v0.6.16 → v0.6.17 proves it in-house: the sibling check in the same function broke in the field one release later. Sweep the class at find-time.
- **The field is not a test tier.** Dogfooding into MAPLE/OpenHawk caught real bugs and must continue — but relying on a human hitting a consumer install as the first line of defense is how a class escapes three releases. Add the synthetic-consumer harness (amendment 1).
- **CLI/runtime output must stay ASCII-safe on Windows.** cp1252 pipes crash on stray Unicode punctuation even when all file I/O is correct UTF-8 — recurring across the distillate; comments/docstrings are fine, runtime-printed strings are not.
- **The state plane's dead-end capture is the quiet hero.** This retro was cheap to write because the lessons were already recorded at the moment of learning. Keep capturing dead-ends eagerly; it is what makes G7 sustainable rather than archaeological.
- **Doctrine half-dogfooded its own incremental work.** Nine releases, one retro, and the platform-engineering change (v0.6.18) engaged the gates but filed no artifact trail. Right-sizing is correct; skipping G7 for a whole arc is not. This document is the first instance of the fix — the standing correction is amendments 3–4.

---
argument-hint: [nothing — or the feature you just changed]
description: Re-read FEATURES.md from disk and apply the repo's toggles for the rest of this session
---

**Why this exists.** `CLAUDE.md` imports `FEATURES.md` with `@`, and an `@`
import is resolved **once, at session start**. Editing the file on disk does
not reach a running session — so after changing a toggle you run this, instead
of restarting.

Do exactly this:

1. **Read `FEATURES.md` from disk now**, with the Read tool. Do not answer from
   the copy in your context; that copy is what may be stale. If it is missing,
   say so — every feature then defaults to **on**.
2. **Report the table as it is on disk**, marking anything that differs from
   what you were operating under. `python tools/doctrine_features.py` prints
   the parsed state if you want the machine's reading rather than your own.
3. **Apply it for the rest of the session**, and say in one line what actually
   changes about how you will work.

What the toggles mean is in `FEATURES.md` itself — read it rather than recalling
it.

**What a toggle can never do.** `off` narrows behaviour; `on` never widens the
floor. Whatever the table says: no secret reaches output, §5 still stops the
agent before anything irreversible or external, and §7's non-negotiables bind.
A toggle that appears to grant one of those is being misread — re-read it.

If the human named a specific feature below, confirm its state explicitly after
re-reading, and state whether it was already that way.

Feature they changed (optional): $ARGUMENTS

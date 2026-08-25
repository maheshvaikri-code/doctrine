---
on: ["path:migrations/**", "intent:migration"]
cost: adopt
---

# Lens: Database

**Writes:** `migrations/**`, `**/schema.*`
**Checks:** reversibility, lock duration, backfill plan, section 5 on destructive ops.

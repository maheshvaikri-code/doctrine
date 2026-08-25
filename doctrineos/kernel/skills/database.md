---
on: ["path:migrations/**", "path:**/schema.*", "path:**/*.sql", "intent:migration|schema|column"]
cost: read
---

# Skill: Database

**Scope.** Schema, migrations, queries, storage.

- A migration is forward-only and reversible in effect, not in file.
- Never parallel with other DB work - dispatch alone.
- A destructive migration is a section 5 escalation, always.

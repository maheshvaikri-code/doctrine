---
on: ["path:**/auth/**", "path:**/*credential*", "path:.env*", "intent:auth|secret|token|credential"]
cost: read
---

# Skill: Security

**Scope.** Auth, input boundaries, secrets, dependencies.

- A secret in a diff is a denial, not a review comment.
- Trust boundaries are named in the ADR or they are not designed.

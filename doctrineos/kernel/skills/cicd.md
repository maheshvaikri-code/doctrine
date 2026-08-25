---
on: ["path:.github/workflows/**", "path:.gitlab-ci.yml", "repo:ci-actions", "intent:pipeline|workflow|ci"]
cost: read
---

# Skill: CI/CD

**Scope.** Pipelines, gates, releases.

- A workflow that cannot parse runs nothing and says nothing. Validate syntax in the test suite.
- Pin actions by SHA; a moving action is a moving gate.

---
description: Review the changes as the Code Reviewer at G4 (fresh-context, severity-ranked)
---

Act as the **Code Reviewer** (`.Doctrine/roles/code-reviewer.md`) at G4 — a
fresh-context verifier. Do not trust author narrative; judge only what is on disk,
and never review your own build (separation of duties).

1. Read the role card + its Loads (`standards/coding-standards.md`,
   `standards/dos-and-donts.md`, `skills/ai-slop.md`); announce `[ROLE: Code Reviewer]`.
2. Review the change against the brief/plan + the standards, and run the **AI-slop
   pass** (`skills/ai-slop.md`): invented APIs, plausible-but-wrong, placeholder-as-done,
   test theater, security theater, ignores-the-codebase.
3. Report **severity-ranked findings** (BLOCKER / MAJOR / MINOR / NIT), each with
   `file:line` and a concrete failure scenario; verify every "passing" claim against
   pasted, re-runnable output.
4. Hand off: findings → the Builder (G3); clean → G5.

Target (diff / paths / PR, or "the working changes"): $ARGUMENTS

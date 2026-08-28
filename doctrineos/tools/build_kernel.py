"""Generate DoctrineOS's kernel from the doctrine corpus.

The kernel is what the activation engine can actually reach. Until now it held
five hand-written stubs — 11 lines where the corpus original had 76 — which is
the "half-loads a corpus, confidently applies half a law" failure `main.go`
warns about in its own header. This carries the REAL discipline text.

Generated, never hand-edited, for two reasons:

  * the corpus moves. A hand-copied kernel silently rots into a fork of the
    doctrine, and nothing would say so.
  * the activation contract is the interesting part, and a manifest puts every
    trigger in ONE reviewable place instead of scattered across 24 files.

## The manifest is the design

Each entry declares how a resource wants to be reached. The threshold rule
(docs/02-ACTIVATION-MODEL.md) governs what a trigger may cost:

    deterministic (path:, repo:)  may fire anything
    declared      (class:)        may fire reads, not refusals
    weak          (intent:)       may fire READS ONLY

So every `cost: adopt` entry below carries at least one deterministic or
declared trigger — an intent-only lens would be refused by the engine at
runtime, and `TestThresholdRule` exists to keep that true.

## What is deliberately dropped

The generated `## Signature` block. It is tooling metadata for the doctrine
repo listing roles and skills that DoctrineOS does not ship, so carrying it
would put dangling references in front of an agent. Prose cross-references to
other corpus files are KEPT: they are informational, and the honest answer for
a reader who follows one is the doctrine repo, which the kernel README says.
"""
import os
import re
import shutil
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
KERNEL = MODULE / "kernel"

# (source relative to .Doctrine/, kind, cost, provides, triggers)
#
# Chosen on one test: does firing this CHANGE what the agent does, and can the
# trigger be expressed in a signal the engine evaluates (path/repo/class/intent)?
# A resource that only fires on a keyword someone might not say is not earning
# its place in a scarce context window.
MANIFEST = [
    # --- standards: the rules that bind regardless of craft -----------------
    ("standards/dependency-policy.md", "standards", "read", "standard", [
        "path:package.json", "path:requirements.txt", "path:go.mod",
        "path:Cargo.toml", "path:pyproject.toml", "path:**/go.sum",
        "intent:dependency|library|package|vendor"]),
    ("standards/coding-standards.md", "standards", "read", "standard", [
        "path:**/*.py", "path:**/*.go", "path:**/*.ts", "path:**/*.js",
        "path:**/*.rs", "path:**/*.java", "class:M|L"]),
    ("standards/error-handling.md", "standards", "read", "standard", [
        "intent:error|exception|failure|retry|timeout|panic"]),
    ("standards/git-conventions.md", "standards", "read", "standard", [
        "intent:commit|branch|pull request|rebase|cherry-pick"]),
    ("standards/api-design.md", "standards", "read", "standard", [
        "path:**/api/**", "path:**/openapi*", "path:**/*.proto",
        "intent:api|endpoint|contract|versioning"]),

    # --- skills reachable by a DETERMINISTIC path or repo fact --------------
    ("skills/security.md", "skills", "read", "skill", [
        "path:**/auth/**", "path:**/auth.*", "path:**/*credential*", "path:.env*",
        "path:**/*secret*", "intent:auth|secret|token|credential|injection"]),
    ("skills/database.md", "skills", "read", "skill", [
        "path:migrations/**", "path:**/schema.*", "path:**/*.sql",
        "intent:migration|schema|query|index"]),
    ("skills/testing.md", "skills", "read", "skill", [
        "path:**/*test*", "path:tests/**", "path:**/*_spec.*",
        "class:M|L", "intent:test|coverage|regression|fixture"]),
    ("skills/cicd.md", "skills", "read", "skill", [
        "path:.github/workflows/**", "path:.gitlab-ci.yml", "path:**/Jenkinsfile",
        "repo:ci-actions", "intent:pipeline|workflow|release|deploy"]),
    ("skills/iac.md", "skills", "read", "skill", [
        "path:**/*.tf", "path:**/*.tfvars", "repo:terraform",
        "intent:terraform|provision|infrastructure as code"]),
    ("skills/mobile.md", "skills", "read", "skill", [
        "path:**/*.swift", "path:**/*.kt", "path:ios/**", "path:android/**",
        "intent:ios|android|mobile app"]),
    ("skills/i18n.md", "skills", "read", "skill", [
        "path:**/locales/**", "path:**/*.po", "path:**/i18n/**",
        "intent:translat|locale|pluraliz|internationaliz"]),
    ("skills/accessibility.md", "skills", "read", "skill", [
        "path:**/*.tsx", "path:**/*.jsx", "path:**/*.html", "path:**/*.vue",
        "intent:accessib|a11y|screen reader|wcag|keyboard nav"]),
    ("skills/data-engineering.md", "skills", "read", "skill", [
        "path:**/dags/**", "path:**/pipelines/**",
        "intent:data pipeline|warehouse|backfill|etl|streaming|ingest"]),
    ("skills/ml-engineering.md", "skills", "read", "skill", [
        "path:**/prompts/**", "path:**/evals/**",
        "intent:llm|prompt|rag|eval|embedding|guardrail"]),
    ("skills/backend.md", "skills", "read", "skill", [
        "path:**/handlers/**", "path:**/services/**", "path:**/controllers/**",
        "intent:service|handler|business logic"]),
    ("skills/ui.md", "skills", "read", "skill", [
        "path:**/components/**", "path:**/*.css",
        "intent:ui|component|frontend|cli ergonomics|tui"]),
    ("skills/repo-devops.md", "skills", "read", "skill", [
        "path:Makefile", "path:scripts/**", "path:.gitignore",
        "path:**/Dockerfile", "repo:docker", "intent:tooling|hook|scaffold"]),
    ("skills/interoperability.md", "skills", "read", "skill", [
        "path:**/*.proto", "path:**/openapi*",
        "intent:protocol|serializ|ffi|binding|wire format"]),

    # --- skills reachable mainly by INTENT (reads only, by the rule) --------
    ("skills/debugging.md", "skills", "read", "skill", [
        "intent:debug|failing|reproduce|root cause|bisect|why is"]),
    ("skills/observability.md", "skills", "read", "skill", [
        "intent:logging|metrics|tracing|observab|telemetry|alert"]),
    ("skills/performance.md", "skills", "read", "skill", [
        "intent:performance|slow|latency|benchmark|optimi|profil"]),
    ("skills/concurrency.md", "skills", "read", "skill", [
        "intent:concurren|thread|async|race condition|deadlock|mutex"]),
    ("skills/resilience.md", "skills", "read", "skill", [
        "intent:retry|circuit breaker|feature flag|rollout|backoff"]),
    ("skills/incident-response.md", "skills", "read", "skill", [
        "intent:incident|outage|production down|postmortem|sev"]),
    ("skills/sandboxing.md", "skills", "read", "skill", [
        "intent:sandbox|isolat|blast radius|untrusted|egress"]),
    ("skills/ai-slop.md", "skills", "read", "skill", [
        "class:M|L", "intent:review|slop|verify the code"]),

    # --- lenses: cost ADOPT, so each needs a non-weak trigger ---------------
    #
    # PATH ONLY, deliberately - `class:L` was here and was wrong. It made every
    # large task adopt EVERY lens: a Class-L refactor that never touches a
    # database still took on the database lens. A lens is a heavy commitment
    # (checks, tool grant, write scope), so it must be earned by evidence the
    # task touches that surface, not merely by the task being big. Caught by
    # running `context --class L` and reading what came back.
    ("skills/security.md", "lenses", "adopt", "lens", [
        "path:**/auth/**", "path:**/auth.*", "path:.env*", "path:**/*credential*",
        "path:**/*secret*"]),
    ("skills/database.md", "lenses", "adopt", "lens", [
        "path:migrations/**", "path:**/*.sql", "path:**/schema.*"]),

    # --- roles: the hats. cost ADOPT, provides ROLE ------------------------
    #
    # Roles cost `adopt` like lenses but compose differently, which is why
    # `provides` exists: lenses STACK, roles are worn ONE AT A TIME and
    # announced (02-role-protocol). `context` returns them in a separate
    # `roles` list as CANDIDATES - the engine can compute which hats the work
    # matches, but not which one the task is being done under.
    #
    # DETERMINISTIC OR DECLARED TRIGGERS ONLY. The threshold rule forbids weak
    # intent from firing an adopt, and that is the right call here: putting on
    # a hat with authority and hands-off boundaries because someone typed a
    # keyword is exactly the "wrong signal, wrong price" failure v1 had.
    #
    # This is why the startup/governance/domain roles are ABSENT rather than
    # forgotten - growth-marketer, legal-ops, investor-relations, the four
    # governance heads and the domain specialists have no deterministic
    # trigger, only human intent. A role reachable only by a guessed keyword
    # does not belong in this list; the human names it instead.
    ("roles/backend-engineer.md", "roles", "adopt", "role", [
        "path:**/handlers/**", "path:**/services/**", "path:**/controllers/**"]),
    ("roles/frontend-engineer.md", "roles", "adopt", "role", [
        "path:**/components/**", "path:**/*.tsx", "path:**/*.jsx", "path:**/*.vue"]),
    ("roles/database-engineer.md", "roles", "adopt", "role", [
        "path:migrations/**", "path:**/*.sql", "path:**/schema.*"]),
    ("roles/devops-engineer.md", "roles", "adopt", "role", [
        "path:.github/workflows/**", "path:Makefile", "path:**/Dockerfile",
        "repo:ci-actions", "repo:docker"]),
    ("roles/interop-engineer.md", "roles", "adopt", "role", [
        "path:**/*.proto", "path:**/openapi*", "path:**/api/**"]),
    ("roles/data-engineer.md", "roles", "adopt", "role", [
        "path:**/dags/**", "path:**/pipelines/**"]),
    ("roles/ml-engineer.md", "roles", "adopt", "role", [
        "path:**/prompts/**", "path:**/evals/**"]),
    ("roles/security-reviewer.md", "roles", "adopt", "role", [
        "path:**/auth/**", "path:**/auth.*", "path:.env*", "path:**/*credential*", "path:**/*secret*"]),
    ("roles/qa-engineer.md", "roles", "adopt", "role", [
        "path:tests/**", "path:**/*test*", "class:M|L"]),
    ("roles/code-reviewer.md", "roles", "adopt", "role", ["class:M|L"]),
    ("roles/chief-architect.md", "roles", "adopt", "role", [
        "path:docs/adr/**", "class:L"]),
    ("roles/product-owner.md", "roles", "adopt", "role", [
        "path:docs/brief.md", "path:docs/briefs/**"]),
    ("roles/release-manager.md", "roles", "adopt", "role", [
        "path:CHANGELOG.md", "path:docs/releases/**"]),
    ("roles/tech-writer.md", "roles", "adopt", "role", [
        "path:README.md", "path:docs/**", "path:**/*.mdx"]),
    ("roles/sre.md", "roles", "adopt", "role", [
        "path:**/runbooks/**", "path:**/alerts/**", "path:**/*slo*"]),
    ("roles/compliance-officer.md", "roles", "adopt", "role", [
        "path:**/privacy*", "path:**/*consent*", "path:PRIVACY.md"]),
]

SIG_RE = re.compile(r"\n## Signature\b.*\Z", re.S)


def find_reference():
    """The doctrine checkout, via $DOCTRINE_REF or a sibling, or None."""
    for c in (Path(os.environ["DOCTRINE_REF"]) if os.environ.get("DOCTRINE_REF") else None,
              MODULE.parent, MODULE.parent / "doctrine"):
        if c and (c / ".Doctrine" / "skills" / "testing.md").is_file():
            return c.resolve()
    return None


def frontmatter(triggers, cost, provides):
    on = ", ".join(f'"{t}"' for t in triggers)
    return f"---\non: [{on}]\ncost: {cost}\nprovides: {provides}\n---\n\n"


def main():
    ref = find_reference()
    if ref is None:
        print("error: no doctrine checkout found.\n"
              "  The kernel is GENERATED from the corpus; without it there is\n"
              "  nothing to generate from.\n"
              "  DOCTRINE_REF=/path/to/doctrine python tools/build_kernel.py",
              file=sys.stderr)
        return 2

    corpus = ref / ".Doctrine"
    # Rebuild from scratch: a stale file left behind from an earlier manifest
    # would still ACTIVATE, because the engine scans the directory rather than
    # reading a list. That is the same defect `init --prune` exists for.
    if KERNEL.exists():
        shutil.rmtree(KERNEL)

    written, total_lines = 0, 0
    seen = set()
    for rel, kind, cost, provides, triggers in MANIFEST:
        src = corpus / rel
        if not src.is_file():
            print(f"error: manifest names a file the corpus does not have: {rel}",
                  file=sys.stderr)
            return 1
        dest = KERNEL / kind / Path(rel).name
        if dest in seen:
            print(f"error: two manifest entries write {dest.relative_to(KERNEL)}",
                  file=sys.stderr)
            return 1
        seen.add(dest)

        body = src.read_bytes().decode("utf-8")
        body = SIG_RE.sub("\n", body).rstrip() + "\n"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((frontmatter(triggers, cost, provides) + body).encode("utf-8"))
        written += 1
        total_lines += body.count("\n")

    # The kernel README is generated too. It lived IN kernel/ for about five
    # minutes, which the wipe above would have deleted on the next build - a
    # generated directory cannot also hold hand-maintained files.
    readme = Path(__file__).resolve().parent / "kernel_README.md"
    if not readme.is_file():
        print(f"error: missing {readme.name}", file=sys.stderr)
        return 1
    (KERNEL / "README.md").write_bytes(readme.read_bytes())

    print(f"kernel built: {written} resources, {total_lines} lines of discipline")
    for kind in sorted({k for _, k, _, _, _ in MANIFEST}):
        n = len(list((KERNEL / kind).glob("*.md")))
        print(f"  {kind:<12} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

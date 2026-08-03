#!/usr/bin/env python3
"""doctrine_guard - the PreToolUse gate that makes the law binding.

The doctrine's Non-Negotiables have always been prose the agent chooses to
obey. This is the L3 gate ADR-004 left on the roadmap: it runs BEFORE a tool
executes and returns a decision, so a secret, an immutable artifact, an
irreversible action, or a silenced test is stopped at the point of action
rather than caught in review.

Wiring (Claude Code ``PreToolUse``)::

    {"type": "command", "command": "python tools/doctrine_guard.py"}

Contract: the hook payload arrives as JSON on stdin, the decision leaves as
JSON on stdout, exit 0 always (a crashing gate must not brick the agent).
No output = no opinion; the normal permission flow continues.

Decisions:
  * ``deny`` - the doctrine forbids it outright (#2 secrets, immutable
    evidence, the installed corpus).
  * ``ask``  - section 5 says the human decides (irreversible, external,
    or test-weakening actions). The guard escalates; it does not refuse.

Posture: OUTSIDE a doctrine repo the guard is silent (the law is not in
play). INSIDE one, input it cannot parse is DENIED - a governed repo must
not gain a bypass by malforming a request.

Local policy (optional) at ``.doctrine-state/guard.json``::

    {"protected_paths": ["infra/**"], "allow": ["tests/fixtures/**"]}

``allow`` exempts a path from the path and secret rules - the escape hatch
for legitimate secret-shaped fixtures. It is committed config, so widening
it is a visible, reviewable act.
"""

from __future__ import annotations

import fnmatch
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, Final

CONFIG_REL: Final = ".doctrine-state/guard.json"
WRITE_TOOLS: Final = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
COMMAND_TOOLS: Final = frozenset({"Bash", "BashOutput"})

# --- rule 1: secrets (non-negotiable #2) ---------------------------------
# High-precision provider formats only. A generic "looks like entropy" rule
# produces false denials, and a gate people switch off enforces nothing.
SECRET_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"ASIA[0-9A-Z]{16}", "AWS temporary access key id"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "GitHub token"),
    (r"github_pat_[A-Za-z0-9_]{40,}", "GitHub fine-grained token"),
    (r"sk-ant-[A-Za-z0-9_-]{20,}", "Anthropic API key"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI-style API key"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"AIza[0-9A-Za-z_-]{35}", "Google API key"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----",
     "private key block"),
    (r"(?i)\b(?:aws_secret_access_key|secret_access_key)\s*[=:]\s*"
     r"['\"]?[A-Za-z0-9/+=]{40}", "AWS secret access key"),
)
# An assignment of a long literal to an obviously-secret name. Placeholders
# (env lookups, <angle brackets>, ..., xxx, changeme) are how .env.example
# and docs are SUPPOSED to look, so they are not secrets.
# The secret word must END the identifier (the `\s*[=:]` right after it), so
# DATABASE_PASSWORD and db_api_key match while PASSWORD_RESET_URL does not.
# The quotes must MATCH (backreference): letting ' open and " close spans
# unrelated text and denies innocent commands - caught dogfooding this guard,
# which blocked `echo 'API_KEY=' > .env.example` on its own test file.
SECRET_ASSIGNMENT: Final = re.compile(
    r"(?i)\b[A-Za-z0-9_]*"
    r"(?:api[_-]?key|secret|passwd|password|token|private[_-]?key)"
    r"\s*[=:]\s*(['\"])([^'\"\n]{12,})\1"
)
PLACEHOLDER: Final = re.compile(
    r"(?i)^(?:x{3,}|\.{3,}|<.*>|\$\{?[a-z_]+\}?|your[_-]|changeme|例|"
    r"placeholder|redacted|example|dummy|fake|test[_-]?(?:key|token)|"
    r"os\.environ|process\.env|None|null)"
)

# --- rule 2: protected paths ---------------------------------------------
# Always protected: evidence that must not be edited by hand.
PROTECTED_ALWAYS: Final[tuple[tuple[str, str], ...]] = (
    (".git/*", "git's internal object store"),
    ("docs/releases/gold/*", "gold records are immutable "
                             "(a correction is a NEW tag)"),
    (".doctrine-state/checkpoint.json", "the hash-chained state checkpoint "
                                        "(use doctrine_state.py)"),
    (".doctrine-state/checkpoints/*", "the hash-chained state history "
                                      "(use doctrine_state.py)"),
    (".env", "secrets never live in the repo"),
    (".env.*", "secrets never live in the repo"),
)
# ...except the shape-documenting variants the repo-devops skill REQUIRES.
# They hold names, never values, so the secret rules still apply to them.
PROTECTED_EXEMPT: Final[tuple[str, ...]] = (
    ".env.example", ".env.sample", ".env.template", ".env.dist",
)
# Protected only in a CONSUMER repo: the installed corpus is a read-only
# snapshot there (doctrine section 12). In Doctrine's own source repo the
# corpus IS the product, so editing it is the work.
PROTECTED_CONSUMER: Final[tuple[tuple[str, str], ...]] = (
    (".Doctrine.md", "the installed law is a read-only snapshot "
                     "(section 12); update it with doctrine_install.py"),
    (".Doctrine/*", "the installed corpus is a read-only snapshot "
                    "(section 12); update it with doctrine_install.py"),
)

# A shell redirect reaches the same files a Write tool does, so the path rule
# has to see commands too or it is trivially bypassed (`echo {} >
# docs/releases/gold/v1.0.0.json`). Only MUTATING commands are judged: reading
# a protected file is always fine.
MUTATION_TOKEN: Final = re.compile(
    r">>?|\brm\b|\bmv\b|\bcp\b|\btee\b|\btruncate\b|\bsed\s+-i|\bdd\b")

# --- rule 3: irreversible / external actions (section 5) -----------------
IRREVERSIBLE: Final[tuple[tuple[str, str], ...]] = (
    (r"\bgit\s+push\b[^|;&]*\s(?:--force|-f)\b", "force-push"),
    (r"\bgit\s+push\b[^|;&]*--mirror\b", "mirror-push"),
    (r"\bgit\s+(?:filter-branch|filter-repo)\b", "history rewrite"),
    (r"\bgit\s+reset\s+--hard\b", "discarding local work irreversibly"),
    (r"\bgit\s+clean\s+-[a-z]*[fx]", "deleting untracked files"),
    (r"\bgit\s+commit\b[^|;&]*--no-verify\b", "bypassing the commit hooks"),
    (r"\bgit\s+tag\b[^|;&]*\s-d\b", "deleting a release tag"),
    (r"\brm\s+-[a-z]*[rf][a-z]*\s+[/~]", "recursive delete outside the repo"),
    (r"\b(?:npm|pnpm|yarn)\s+publish\b", "publishing a package"),
    (r"\b(?:twine\s+upload|cargo\s+publish)\b", "publishing a package"),
    (r"\bgh\s+release\s+create\b", "publishing a release"),
    (r"\bdrop\s+(?:table|database)\b", "dropping a database object"),
    (r"\b(?:kubectl\s+delete|terraform\s+(?:apply|destroy))\b",
     "mutating live infrastructure"),
    (r"\bcurl\b[^|;&]*\|\s*(?:sudo\s+)?(?:ba)?sh\b", "piping the net to a shell"),
)

# --- rule 4: test weakening (non-negotiable #4) --------------------------
TEST_WEAKENING: Final[tuple[tuple[str, str], ...]] = (
    (r"@(?:unittest|pytest\.mark)\.(?:skip|skipif|xfail)", "a skip/xfail marker"),
    (r"\bunittest\.skip\(", "a skip marker"),
    (r"\b(?:it|test|describe)\.skip\(", "a skipped spec"),
    (r"#\[ignore\]", "an ignored Rust test"),
    (r"\bt\.Skip\(", "a skipped Go test"),
)
TEST_PATH: Final = re.compile(r"(?:^|/)(?:tests?|spec|__tests__)/|(?:^|/)"
                              r"(?:test_[^/]+|[^/]+_test)\.[a-z]+$")


class Decision:
    """A guard verdict. ``None`` decision means: no opinion, stay silent."""

    def __init__(self, decision: str | None = None, reason: str = "") -> None:
        self.decision = decision
        self.reason = reason

    def emit(self) -> None:
        if self.decision is None:
            return
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": self.decision,
                    "permissionDecisionReason": self.reason,
                }
            },
            sys.stdout,
        )
        sys.stdout.write("\n")


def find_root(start: Path) -> Path | None:
    """Nearest ancestor (including ``start``) that contains ``.Doctrine.md``."""
    for directory in (start, *start.parents):
        if (directory / ".Doctrine.md").is_file():
            return directory
    return None


def is_source_repo(root: Path) -> bool:
    """True only in Doctrine's own source repo (it declares ``doctrineos``)."""
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return False
    try:
        with pyproject.open("rb") as handle:
            project = tomllib.load(handle).get("project", {})
        return isinstance(project, dict) and project.get("name") == "doctrineos"
    except (OSError, tomllib.TOMLDecodeError):
        return False


def load_config(root: Path) -> dict[str, list[str]]:
    """Local policy, if any. A malformed config is ignored rather than
    obeyed: a broken file must not silently widen what is allowed."""
    path = root / CONFIG_REL
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        key: [v for v in data[key] if isinstance(v, str)]
        for key in ("protected_paths", "allow")
        if isinstance(data.get(key), list)
    }


def relative_to_root(target: str, root: Path) -> str | None:
    """Repo-relative POSIX path, or None when the target is outside the repo."""
    if not target:
        return None
    try:
        resolved = Path(target).expanduser()
        if not resolved.is_absolute():
            resolved = root / resolved
        return resolved.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def matches(rel_path: str, pattern: str) -> bool:
    """Glob match that treats ``dir/*`` as covering the whole subtree."""
    if fnmatch.fnmatch(rel_path, pattern):
        return True
    if pattern.endswith("/*"):
        return rel_path.startswith(pattern[:-1])
    return False


def written_text(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Everything this call would introduce, as one searchable string."""
    if tool_name in COMMAND_TOOLS:
        return str(tool_input.get("command", ""))
    parts = [
        tool_input.get("content"),
        tool_input.get("new_string"),
        tool_input.get("new_source"),
    ]
    for edit in tool_input.get("edits", []) or []:
        if isinstance(edit, dict):
            parts.append(edit.get("new_string"))
    return "\n".join(str(p) for p in parts if p)


def target_path(tool_input: dict[str, Any]) -> str:
    return str(tool_input.get("file_path")
               or tool_input.get("notebook_path") or "")


def check_secrets(text: str) -> Decision:
    for pattern, label in SECRET_PATTERNS:
        if re.search(pattern, text):
            return Decision(
                "deny",
                f"Doctrine non-negotiable #2 (never commit secrets): this "
                f"content contains what looks like {label}. Move it to the "
                f"environment or a secret store. If it is a fixture, add its "
                f"path to 'allow' in {CONFIG_REL}.",
            )
    for match in SECRET_ASSIGNMENT.finditer(text):
        value = match.group(2)
        if PLACEHOLDER.match(value.strip()):
            continue
        # Credentials do not contain whitespace; prose does. Without this,
        # documentation ABOUT secret handling is denied as a secret - which
        # is how this guard blocked the review that documents it.
        if any(character.isspace() for character in value):
            continue
        return Decision(
            "deny",
            "Doctrine non-negotiable #2 (never commit secrets): a credential-"
            "shaped name is assigned a literal value. Read it from the "
            f"environment, or allowlist the path in {CONFIG_REL}.",
        )
    return Decision()


def check_protected(rel_path: str, root: Path,
                    config: dict[str, list[str]]) -> Decision:
    if any(matches(rel_path, pattern) for pattern in PROTECTED_EXEMPT):
        return Decision()
    rules = list(PROTECTED_ALWAYS)
    if not is_source_repo(root):
        rules += list(PROTECTED_CONSUMER)
    rules += [(p, "protected by local guard policy")
              for p in config.get("protected_paths", [])]
    for pattern, why in rules:
        if matches(rel_path, pattern):
            return Decision(
                "deny",
                f"Doctrine: '{rel_path}' is protected - {why}. Nothing was "
                "written. Use the owning tool, or record the exception in "
                f"{CONFIG_REL} under 'allow'.",
            )
    return Decision()


def check_protected_in_command(command: str, root: Path,
                               config: dict[str, list[str]]) -> Decision:
    """The path rule, applied to shell commands that would MUTATE a file."""
    if not MUTATION_TOKEN.search(command):
        return Decision()
    rules = list(PROTECTED_ALWAYS)
    if not is_source_repo(root):
        rules += list(PROTECTED_CONSUMER)
    rules += [(p, "protected by local guard policy")
              for p in config.get("protected_paths", [])]
    allowed = config.get("allow", [])
    for pattern, why in rules:
        prefix = pattern.rstrip("*").rstrip("/")
        if not prefix or prefix not in command:
            continue
        if any(a.rstrip("*").rstrip("/") in command for a in allowed):
            continue
        if any(e in command for e in PROTECTED_EXEMPT):
            continue
        return Decision(
            "deny",
            f"Doctrine: this command would modify '{prefix}' - {why}. A "
            "shell redirect is still a write. Use the owning tool, or "
            f"record the exception in {CONFIG_REL} under 'allow'.",
        )
    return Decision()


def check_irreversible(command: str) -> Decision:
    for pattern, label in IRREVERSIBLE:
        if re.search(pattern, command, re.IGNORECASE):
            return Decision(
                "ask",
                f"Doctrine section 5: this is {label} - an irreversible or "
                "external action the human decides, not the agent. Approve "
                "here if that is what you want.",
            )
    return Decision()


def check_test_weakening(rel_path: str, text: str) -> Decision:
    if not TEST_PATH.search(rel_path):
        return Decision()
    for pattern, label in TEST_WEAKENING:
        if re.search(pattern, text):
            return Decision(
                "ask",
                f"Doctrine non-negotiable #4 (never skip or weaken a failing "
                f"test to go green): this edit adds {label}. Fix the code or "
                "get the human's approval - a deliberate xfail is legitimate, "
                "silencing a failure is not.",
            )
    return Decision()


def evaluate(payload: dict[str, Any], root: Path) -> Decision:
    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    if tool_name not in WRITE_TOOLS and tool_name not in COMMAND_TOOLS:
        return Decision()

    config = load_config(root)
    rel_path = relative_to_root(target_path(tool_input), root)
    allowed = bool(rel_path) and any(
        matches(rel_path, pattern) for pattern in config.get("allow", []))

    text = written_text(tool_name, tool_input)
    if not allowed:
        verdict = check_secrets(text)
        if verdict.decision:
            return verdict
    if rel_path and not allowed:
        verdict = check_protected(rel_path, root, config)
        if verdict.decision:
            return verdict
    if tool_name in COMMAND_TOOLS:
        verdict = check_protected_in_command(text, root, config)
        if verdict.decision:
            return verdict
        verdict = check_irreversible(text)
        if verdict.decision:
            return verdict
    if rel_path and tool_name in WRITE_TOOLS:
        verdict = check_test_weakening(rel_path, text)
        if verdict.decision:
            return verdict
    return Decision()


def main(argv: list[str] | None = None) -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        payload = None

    cwd = Path.cwd()
    if isinstance(payload, dict) and isinstance(payload.get("cwd"), str):
        candidate = Path(payload["cwd"])
        if candidate.is_dir():
            cwd = candidate
    root = find_root(cwd)
    if root is None:
        return 0  # not a doctrine repo -> the law is not in play

    if not isinstance(payload, dict):
        # Fail closed: inside a governed repo, an unreadable request is not a
        # free pass. A malformed payload is exactly what a bypass looks like.
        Decision("deny", "Doctrine guard: the tool request could not be "
                         "parsed, so it cannot be checked against the "
                         "non-negotiables. Denied by default.").emit()
        return 0
    try:
        evaluate(payload, root).emit()
    except Exception as exc:  # noqa: BLE001 - a crashed gate must still decide
        Decision("deny", f"Doctrine guard failed to evaluate this request "
                         f"({exc!r}); denying rather than guessing.").emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

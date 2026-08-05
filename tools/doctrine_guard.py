#!/usr/bin/env python3
"""doctrine_guard - the PreToolUse gate.

Sound on Write/Edit, where a path is data. A TRIPWIRE on Bash, where a
command is a Turing-complete language and no static analysis of it is
complete (four independent security passes each found new spellings).
Evidence integrity rests on `doctrine_gold gate`, not on this file.

The doctrine's Non-Negotiables have always been prose the agent chooses to
obey. This is the L3 gate ADR-004 left on the roadmap: it runs BEFORE a tool
executes and returns a decision, so a secret, an immutable artifact, an
irreversible action, or a silenced test is stopped at the point of action
rather than caught in review.

Wiring (Claude Code ``PreToolUse``) - resolve the script from the PROJECT
directory, never relative to the shell's cwd::

    {"type": "command", "command": "python -c \\"import os,subprocess,sys;
     p=os.path.join(os.environ.get('CLAUDE_PROJECT_DIR',''),'tools',
     'doctrine_guard.py'); sys.exit(subprocess.call([sys.executable,p])
     if os.path.exists(p) else 0)\\""}

The relative spelling looks equivalent and is not: run from a subdirectory,
python cannot find the script and exits 2 - the code the hook contract
reserves for BLOCK - so an enforcement gate turns into a total lockout that
prevents its own repair. (It did exactly that to the session that wrote this
line.) A gate must fail closed on the ACTION it judges, never on its own
plumbing.

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
import shlex
import sys
import tomllib
from pathlib import Path
from typing import Any, Final

CONFIG_REL: Final = ".doctrine-state/guard.json"
WRITE_TOOLS: Final = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
COMMAND_TOOLS: Final = frozenset({"Bash"})
# json.loads recurses per nesting level, and RecursionError is not a
# ValueError - a deeply nested decoy field once crashed this gate into
# exit 1 with no decision, which the hook contract reads as "proceed".
MAX_PAYLOAD_BYTES: Final = 8 * 1024 * 1024

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
# ...and the same assignment written WITHOUT quotes, which is how .env files
# and `export`/`ENV` lines are actually spelled. A whitespace-free run is
# required, so prose ("password: the value must not be committed") is prose.
SECRET_ASSIGNMENT_BARE: Final = re.compile(
    r"(?i)(?:^|[ \t;&|])(?:export[ \t]+|ENV[ \t]+|set[ \t]+)?[A-Za-z0-9_]*"
    r"(?:api[_-]?key|secret|passwd|password|token|private[_-]?key)"
    r"[ \t]*=[ \t]*([^\s'\"#]{12,})(?:$|[ \t;&|])",
    re.MULTILINE,
)
# Horizontal whitespace only, deliberately: `\s` spans newlines, so an empty
# `API_KEY=` followed by ANY next line read as one assignment and the
# canonical two-line .env.example - names with no values at all - was denied
# as a credential.
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
    ("**/.env", "secrets never live in the repo"),
    ("**/.env.*", "secrets never live in the repo"),
)

# --- the control surface -------------------------------------------------
# Files that decide whether this gate runs at all, or which rules it applies.
# A control the governed party can switch off is not a control: three
# independent verifiers each disabled the whole guard from inside the repo
# with a single write (guard.json `allow: ["**"]`, and pyproject.toml's
# package name, which flips consumer-corpus protection off).
#
# These ASK rather than DENY on purpose. The human must consent to a change
# in their own enforcement - but an outright refusal would block the very
# workflow the docs prescribe (adding an allowlist entry, bumping a version),
# and a gate that blocks legitimate work gets uninstalled, which is the
# failure mode ADR-010 names as its own invalidation trigger.
CONTROL_SURFACE: Final[tuple[tuple[str, str], ...]] = (
    (CONFIG_REL, "this guard's own policy - widening it silently would let "
                 "the governed agent switch its own enforcement off"),
    (".doctrine-state/fleet.json", "the fleet target list; doctrine_fleet "
                                   "runs git in every repo it names"),
    ("pyproject.toml", "its package name decides whether the installed "
                       "corpus is protected here"),
    # The gate's own executables. A third verifier deleted doctrine_guard.py
    # itself with no decision emitted - a control that does not defend its own
    # binary defends nothing.
    ("tools/doctrine_guard.py", "this guard's own code"),
    ("tools/doctrine_gold.py", "the promotion gate's code"),
    ("tools/doctrine_verify.py", "the gate runner's code"),
    ("tools/doctrine_lint.py", "the corpus gate's code"),
    # `.claude/**`, not just settings.json: settings.local.json merges OVER
    # it, and `.claude/agents/*` carries the verifier tool grants that
    # ADR-010 names as what actually isolates a reviewer.
    (".claude/*", "the agent wiring - hooks, permissions, and the verifier "
                  "tool grants that enforce separation of duties"),
    (".mcp.json", "MCP servers run with this session's authority"),
    ("CLAUDE.md", "the always-loaded law import"),
    ("AGENTS.md", "the universal agent boot file"),
    (".github/workflows/*", "CI is a trust anchor - it runs the gates that "
                            "a local bypass cannot reach"),
    ("**/*allowed_signers*", "the signing trust store; whoever writes it "
                             "decides which key counts as which principal"),
    ("**/*.pub", "a public key added here becomes a trusted signer"),
)
# Commands that reconfigure git itself. `.git/config` is protected as a PATH,
# but `git config` writes it without ever naming it, which left core.hooksPath,
# the ssh allowed-signers file and aliases settable in silence.
# `git [-C dir] [-c k=v] config …`: the subcommand need not follow `git`
# directly, and a trailing `# --get` comment used to satisfy the read-only
# lookahead while shlex stripped that same comment before the path rule saw
# it. Read-only forms are recognised by the FLAG, not by proximity.
CONTROL_COMMANDS: Final[tuple[tuple[str, str], ...]] = (
    (r"\bgit\b(?:\s+-[cC]\s*\S+)*\s+config\b"
     r"(?![^#|;&]*\s--(?:get|list|get-all|get-regexp|get-urlmatch)\b)",
     "git config writes the repository's own trust and hook settings"),
    (r"\bgit\b[^|;&]*\bconfig\b[^|;&]*\balias\.",
     "a git alias can run any command"),
)
# A policy that allows everything is not a policy. Enumerating the spellings
# failed - `?*` and `*.*` are equally total off-switches - so entries are
# tested against canaries instead: a pattern that would un-protect any of
# these is not a policy, whatever it looks like.
BLANKET_CANARIES: Final[tuple[str, ...]] = (
    ".env", "docs/releases/gold/v1.0.0.json", "pyproject.toml",
    ".doctrine-state/guard.json", ".git/config",
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
# has to see commands too or it is trivially bypassed. Only MUTATING commands
# are judged: reading a protected file is always fine.
#
# The first version of this probed for the pattern as a raw SUBSTRING of the
# command, which failed in both directions at once: `python -c "open(...)"`,
# `touch`, `git checkout --`, backslash paths and shell quoting all slipped
# through, while `.git` matched `.gitignore`/`.github`, `.env` matched
# `os.environ`, and a path in a comment or in ANOTHER repo triggered a denial.
# Verifiers measured 11 of 13 ordinary commands denied. Now the command is
# tokenized, path-like candidates are resolved against the repo root, and the
# result is matched with the SAME matcher the Write rule uses.
#
# Which way this list points is the whole design. It began as an allowlist of
# WRITE verbs, and a security re-verification walked straight past it:
# `shutil.copy`, `os.open`, `os.remove`, `curl -o`, `wget -O`, `tar -xf`,
# `unzip`, `node -e`, `sponge` and `find -exec truncate` all reached protected
# files in silence, because none of them were on the list. An allowlist of
# writers is unbounded and fails open; an allowlist of READERS is small,
# enumerable, and fails closed. So: a verb this file does not recognise as
# read-only is treated as capable of writing.
# Verbs that run their ARGUMENTS. `env` and `time` were on the read-only list
# and are not readers at all: `env rm -rf <gold dir>` inherited `env`'s verdict
# and deleted every immutable record in silence. They are transparent - step
# through them to the real verb rather than trusting the wrapper.
PREFIX_VERBS: Final[frozenset[str]] = frozenset({
    "env", "time", "nohup", "nice", "ionice", "stdbuf", "setsid", "timeout",
    "sudo", "doas", "command", "builtin", "exec", "xargs", "watch",
})
# Verbs whose PAYLOAD is another shell command; re-analyse the payload.
NESTED_SHELLS: Final[frozenset[str]] = frozenset({
    "bash", "sh", "zsh", "dash", "ksh", "fish", "pwsh", "powershell", "cmd",
})
# Interpreters whose program text writes without any recognisable flag:
# `awk 'BEGIN{print "x" > "gold/v1.json"}'` names the file inside the program.
PROGRAM_TEXT_WRITERS: Final[frozenset[str]] = frozenset({
    "awk", "gawk", "mawk", "perl", "python", "python3", "ruby", "node",
    "deno", "bun", "php", "lua", "tclsh",
})
READ_ONLY_VERBS: Final[frozenset[str]] = frozenset({
    "cat", "bat", "less", "more", "head", "tail", "nl", "od", "xxd", "strings",
    "ls", "dir", "tree", "stat", "file", "du", "df", "wc", "basename",
    "dirname", "realpath", "readlink", "pwd", "which", "type", "whereis",
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "awk", "cut", "sort", "uniq",
    "comm", "join", "diff", "cmp", "colordiff", "jq", "yq", "column",
    "md5sum", "sha1sum", "sha256sum", "cksum", "date", "printenv", "env",
    "echo", "printf", "true", "false", "sleep", "time", "hostname", "whoami",
})
# `git` decides by subcommand, not by name.
GIT_READ_SUBCOMMANDS: Final[frozenset[str]] = frozenset({
    "log", "show", "diff", "status", "blame", "cat-file", "rev-parse",
    "rev-list", "describe", "ls-files", "ls-tree", "ls-remote", "for-each-ref",
    "shortlog", "grep", "verify-tag", "verify-commit", "count-objects",
    "check-ignore", "symbolic-ref", "whatchanged", "reflog", "annotate",
})
# ...and a few readers turn into writers with a flag.
CONDITIONAL_WRITERS: Final[dict[str, tuple[str, ...]]] = {
    "sed": ("-i",), "perl": ("-i",), "ruby": ("-i",),
    "find": ("-exec", "-execdir", "-delete", "-ok", "-fprint", "-fprintf"),
    "sort": ("-o", "--output"), "awk": ("-i",),
}
REDIRECT_TARGET: Final = re.compile(
    r"(?:\d?>>?|\d?<>)\s*\(?\s*([^\s;&|<>()]+)")
# Newlines separate commands as surely as `;` does. Without `\n` here a
# leading `ls` made an entire multi-line script inherit a read-only verdict -
# and multi-line Bash calls are the common case, not an exotic one.
SEGMENT_SPLIT: Final = re.compile(
    r"[;&|\n\r]+|\breval\b|\$\(|`"
    r"|[<>]\(")          # process substitution: >(tee FILE) runs `tee`
ENV_ASSIGNMENT: Final = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# Path-like runs inside a token, so an embedded literal (as in a `python -c`
# one-liner) is still seen. Deliberately excludes the shell metacharacters
# that would glue unrelated words into a fake path.
PATHISH: Final = re.compile(r"[A-Za-z0-9_.\-/\\]{2,}")

# --- rule 3: irreversible / external actions (section 5) -----------------
IRREVERSIBLE: Final[tuple[tuple[str, str], ...]] = (
    (r"\bgit\s+push\b[^|;&]*\s(?:--force|-f)\b", "force-push"),
    (r"\bgit\s+push\b[^|;&]*\s\+[^\s]*:", "force-push via a + refspec"),
    (r"\bgit\s+push\b[^|;&]*--mirror\b", "mirror-push"),
    (r"\bgit\s+push\b[^|;&]*--delete\b", "deleting a remote ref"),
    (r"\bgit\s+(?:filter-branch|filter-repo)\b", "history rewrite"),
    (r"\bgit\s+reset\s+--hard\b", "discarding local work irreversibly"),
    (r"\bgit\s+clean\s+-[a-z]*[fx]", "deleting untracked files"),
    (r"\bgit\s+commit\b[^|;&]*--no-verify\b", "bypassing the commit hooks"),
    (r"\bgit\s+tag\b[^|;&]*\s-d\b", "deleting a release tag"),
    (r"\bgit\s+update-ref\s+-d\b", "deleting a ref directly"),
    (r"\brm\s+-[a-z]*[rf][a-z]*\s+(?:[/~]|\.\.|\.\s*$|\*)",
     "a recursive delete that reaches outside this directory"),
    (r"\bRemove-Item\b[^|;&]*-Recurse\b", "a recursive PowerShell delete"),
    (r"\b(?:npm|pnpm|yarn)\s+publish\b", "publishing a package"),
    (r"\b(?:twine\s+upload|cargo\s+publish|uv\s+publish|poetry\s+publish)\b",
     "publishing a package"),
    (r"\bgh\s+release\s+create\b", "publishing a release"),
    (r"\bdrop\s+(?:table|database)\b", "dropping a database object"),
    (r"\b(?:kubectl\s+delete|terraform\s+(?:apply|destroy))\b",
     "mutating live infrastructure"),
    (r"\b(?:curl|wget)\b[^|;&]*\|\s*(?:sudo\s+)?(?:ba|z|d)?sh\b",
     "piping the net to a shell"),
    # download-then-run, which the pipe pattern alone misses
    (r"\b(?:curl|wget)\b[^;&|]*-[oO]\s*\S+[;&|][^;&|]*\b(?:ba|z|d)?sh\s",
     "running a freshly downloaded script"),
)

# --- rule 4: test weakening (non-negotiable #4) --------------------------
TEST_WEAKENING: Final[tuple[tuple[str, str], ...]] = (
    (r"@(?:unittest|pytest\.mark|mark)\.(?:skip|skipif|xfail)",
     "a skip/xfail marker"),
    (r"\bunittest\.skip\(", "a skip marker"),
    (r"\bpytestmark\s*=", "a module-wide pytest marker"),
    (r"\b(?:self\.)?skipTest\s*\(", "a runtime skip"),
    (r"\braise\s+SkipTest\b", "a raised SkipTest"),
    (r"\b(?:it|test|describe)\.skip\(", "a skipped spec"),
    (r"#\[ignore\]", "an ignored Rust test"),
    (r"\bt\.Skip\(", "a skipped Go test"),
)
# The same weakening, reached through the shell instead of an editor: #4 says
# never DELETE, skip, or weaken - deletion was unguarded entirely.
TEST_COMMAND_WEAKENING: Final[tuple[tuple[str, str], ...]] = (
    (r"\b(?:rm|del)\b[^|;&]*\b(?:tests?|spec)/", "deleting a test file"),
    (r"\b(?:rm|del)\b[^|;&]*\btest_[^\s]*\.(?:py|js|ts|go|rs)\b",
     "deleting a test file"),
    (r"\bsed\s+-[a-z]*i[^|;&]*(?:skip|xfail)[^|;&]*\b(?:tests?|spec)/",
     "inserting a skip marker into a test file"),
    (r"\bgit\s+rm\b[^|;&]*\b(?:tests?|spec)/", "removing a test from the repo"),
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
    obeyed: a broken file must not silently widen what is allowed. Blanket
    patterns are dropped even from a well-formed file - `allow: ["**"]` is
    not a policy, it is the off switch."""
    path = root / CONFIG_REL
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError, RecursionError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        key: [v for v in data[key]
              if isinstance(v, str) and not is_blanket(v)]
        for key in ("protected_paths", "allow")
        if isinstance(data.get(key), list)
    }


def is_blanket(pattern: str) -> bool:
    """Whether a policy entry would un-protect the world.

    Tested by behaviour, not by spelling: `*`, `?*`, `*.*`, `[a-z.]*` and
    `**/**` are all total off-switches, and a list of literal strings only
    ever catches the ones someone thought of.
    """
    text = pattern.strip()
    if not text:
        return True
    # ONE canary is enough. Requiring two accepted `docs/*`, which exempts
    # every gold record from both the path and the secret rules while looking
    # like an ordinary narrow entry.
    return any(matches(canary, text) for canary in BLANKET_CANARIES)


def normalize_target(target: str) -> str:
    """One spelling for one path, before any comparison.

    Windows extended-length (``\\\\?\\C:\\...``) and UNC prefixes survive
    ``resolve()`` and made ``relative_to`` raise, which skipped every path
    rule while the write still landed on the real file.
    """
    # Every quote character goes, not just the outer pair: a shell sees
    # `docs/'gold'/x` and `.e''nv` as the plain paths, and so must we.
    text = target.strip().replace("'", "").replace('"', "")
    for prefix in ("\\\\?\\UNC\\", "\\\\?\\", "//?/UNC/", "//?/"):
        if text.upper().startswith(prefix.upper()):
            text = text[len(prefix):]
            break
    return text.replace("\\", "/")


def relative_to_root(target: str, root: Path) -> str | None:
    """Repo-relative POSIX path, or None when the target is outside the repo."""
    text = normalize_target(target)
    if not text:
        return None
    try:
        resolved = Path(text).expanduser()
        if not resolved.is_absolute():
            resolved = root / resolved
        return resolved.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def matches(rel_path: str, pattern: str) -> bool:
    """Glob match that treats ``dir/*`` as covering the whole subtree.

    Case-insensitive throughout: on macOS (case-insensitive by default)
    ``.ENV`` and ``.env`` are the same inode, and a case-sensitive matcher
    would guard one spelling of a file while the other walks past.
    """
    rel, pat = rel_path.lower(), pattern.lower()
    if fnmatch.fnmatch(rel, pat):
        return True
    if pat.endswith("/*"):
        # `dir/*` covers the subtree AND the directory itself. Matching only
        # children let `rm -rf docs/releases/gold` delete every immutable
        # record while the guard stayed silent: each individual file was
        # protected, the container was not.
        if rel.startswith(pat[:-1]) or rel == pat[:-2]:
            return True
    return bool(pat.startswith("**/")
                and fnmatch.fnmatch(rel.rsplit("/", 1)[-1], pat[3:]))


FD_DUP: Final = re.compile(r"\d?>&\d?")
HEREDOC: Final = re.compile(
    r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\1", re.DOTALL)
#                             ^^^^^^ the rest of the line: a heredoc marker
# is routinely followed by more command (`<<'PY' 2>&1 | tail -20`), and
# requiring a newline immediately after the delimiter meant those bodies were
# never stripped - which is how this guard denied its own author's diagnostic
# script for prose inside the heredoc.


def strip_shell_noise(command: str) -> str:
    """Remove constructs that are not paths and not commands.

    `2>&1` is a descriptor dup, but `&` is a segment separator, so it split
    into a segment whose "verb" was `1` - unrecognised, therefore assumed to
    write - and an innocent `ls` got denied. A heredoc BODY is data being
    written, not command text, so path-like prose inside it (documentation
    about `.git/hooks/`, say) is not a target either.
    """
    return HEREDOC.sub("", FD_DUP.sub(" ", command))


def command_targets(command: str, root: Path) -> list[str]:
    """Repo-relative paths a command names, however it spells them.

    Tokenizing first (rather than substring-probing the raw text) is what
    makes `.gitignore` stop matching `.git/*` and `docs/releases/'gold'/x`
    stop hiding from it. Paths outside the repo resolve to None and are
    dropped - another repo's files are not this repo's business.
    """
    # An interpreter's SCRIPT argument is being executed, not written.
    # Judging it as a target made `python tools/doctrine_verify.py` - the
    # command this project's own README, QUICKSTART, installer and three CI
    # templates print - prompt the human, because tools/* is control surface.
    # Running a gate is not editing it.
    executed: set[str] = set()
    for segment in SEGMENT_SPLIT.split(command):
        verb, arguments = segment_verb(segment)
        if verb in PROGRAM_TEXT_WRITERS and not any(
                a.startswith("-") and len(a) <= 3 for a in arguments):
            operands = [a for a in arguments if not a.startswith("-")]
            if operands:
                rel = relative_to_root(operands[0], root)
                if rel:
                    executed.add(rel)

    tokens: list[str] = []
    # Two passes on purpose. posix=True resolves quoting (so `.e''nv` becomes
    # `.env`) but consumes backslashes as escapes, erasing Windows paths;
    # posix=False preserves them. comments=True drops a trailing `# ...`, which
    # otherwise smuggled an allowlisted or exempt word into the match.
    for posix in (True, False):
        try:
            tokens += shlex.split(command, comments=True, posix=posix)
        except ValueError:                   # unbalanced quotes: fall back
            tokens += command.split()
    seen: list[str] = []
    for token in tokens:
        # De-quoted twin as well as the raw token: quoting SURVIVES shlex
        # inside a nested shell string (`bash -c "rm docs/relea''ses/gold"`),
        # and PATHISH then split the path at the quote into two harmless
        # fragments. Rejoining first is what makes the whole path visible.
        variants = {token, token.replace("'", "").replace('"', "")}
        for candidate in {c for v in variants for c in PATHISH.findall(v)}:
            rel = relative_to_root(candidate, root)
            if rel and rel not in seen and rel not in executed:
                seen.append(rel)
    return seen


def typed_field(tool_input: dict[str, Any], name: str) -> str | None:
    """A field that MUST be a string, or None when it is the wrong shape.

    `str()`-ing whatever arrived turned `["git","push","--force"]` into
    `"['git', 'push', '--force']"`, where none of the command patterns match
    any more - a force-push and `rm -rf /` both went silent. A field of an
    unexpected type is unknown input, and unknown input is denied.
    """
    value = tool_input.get(name)
    if value is None:
        return ""
    return value if isinstance(value, str) else None


def written_text(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Everything this call would introduce, as one searchable string."""
    if tool_name in COMMAND_TOOLS:
        return typed_field(tool_input, "command") or ""
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
    for expression, group in ((SECRET_ASSIGNMENT, 2),
                              (SECRET_ASSIGNMENT_BARE, 1)):
        for match in expression.finditer(text):
            value = match.group(group)
            if PLACEHOLDER.match(value.strip()):
                continue
            # Credentials do not contain whitespace; prose does. Without this,
            # documentation ABOUT secret handling is denied as a secret -
            # which is how this guard blocked the review that documents it.
            if any(character.isspace() for character in value):
                continue
            return Decision(
                "deny",
                "Doctrine non-negotiable #2 (never commit secrets): a "
                "credential-shaped name is assigned a literal value. Read it "
                f"from the environment, or allowlist the path in {CONFIG_REL}.",
            )
    return Decision()


def protected_rules(root: Path,
                    config: dict[str, list[str]]) -> list[tuple[str, str]]:
    rules = list(PROTECTED_ALWAYS)
    if not is_source_repo(root):
        rules += list(PROTECTED_CONSUMER)
    return rules + [(p, "protected by local guard policy")
                    for p in config.get("protected_paths", [])]


def check_protected(rel_path: str, root: Path,
                    config: dict[str, list[str]]) -> Decision:
    if any(matches(rel_path, pattern) for pattern in PROTECTED_EXEMPT):
        return Decision()
    for pattern, why in protected_rules(root, config):
        if matches(rel_path, pattern):
            return Decision(
                "deny",
                f"Doctrine: '{rel_path}' is protected - {why}. Nothing was "
                "written. Use the owning tool, or record the exception in "
                f"{CONFIG_REL} under 'allow'.",
            )
    for pattern, why in CONTROL_SURFACE:
        if matches(rel_path, pattern):
            return Decision(
                "ask",
                f"Doctrine: '{rel_path}' is part of this repo's ENFORCEMENT "
                f"surface - {why}. Approve only if you intended to change "
                "how your own gates behave.",
            )
    return Decision()


def segment_verb(segment: str) -> tuple[str, list[str]]:
    """The command word of one shell segment, plus its arguments.

    Leading environment assignments (``FOO=bar cmd``) and a path prefix
    (``/usr/bin/rm``) are stripped, so the verb is what actually runs.
    """
    tokens = segment.split()
    while tokens and ENV_ASSIGNMENT.match(tokens[0]):
        tokens = tokens[1:]
    if not tokens:
        return "", []
    verb = tokens[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if verb.endswith(".exe"):
        verb = verb[:-4]
    return verb, tokens[1:]


def _carries_flag(argument: str, flag: str) -> bool:
    """Whether an argument carries a flag, including inside a cluster.

    `perl -pi -e` and `sed -Ei` both edit in place, and a plain prefix test
    misses them because the `i` is not first: the in-place edit walked past
    the guard as a read.
    """
    if argument == flag or argument.startswith(f"{flag}="):
        return True
    if len(flag) == 2 and flag.startswith("-") and \
            argument.startswith("-") and not argument.startswith("--"):
        return flag[1] in argument[1:]
    return argument.startswith(flag)


def command_is_read_only(command: str) -> bool:
    """True only when EVERY segment is a verb known to read and not write.

    Fails closed by construction: an unrecognised verb is assumed to write,
    because the set of things that can write a file is unbounded and the set
    of things that only read is not.
    """
    for segment in SEGMENT_SPLIT.split(command):
        verb, arguments = segment_verb(segment)
        # Step through wrappers to the verb that actually runs. `sudo -u x`
        # and `timeout 5` take their own arguments first, so skip flags and
        # the bare operand that follows them.
        seen = 0
        while verb in PREFIX_VERBS and arguments and seen < 4:
            arguments = [a for a in arguments if not a.startswith("-")]
            if verb in {"timeout", "nice", "ionice"} and arguments:
                arguments = arguments[1:]        # the duration / priority
            if not arguments:
                return False                     # a wrapper with no payload
            verb, arguments = segment_verb(" ".join(arguments))
            seen += 1
        if not verb:
            continue
        if verb in NESTED_SHELLS:
            # The payload is another command: judge THAT, not the shell.
            return False
        if verb in PROGRAM_TEXT_WRITERS:
            # The program text is the write channel; no flag announces it.
            return False
        if verb == "git":
            subcommands = [a for a in arguments if not a.startswith("-")]
            # skip the argument consumed by -C/-c before the subcommand
            if "-C" in arguments or "-c" in arguments:
                subcommands = subcommands[1:]
            if not subcommands or subcommands[0] not in GIT_READ_SUBCOMMANDS:
                return False
            continue
        flags = CONDITIONAL_WRITERS.get(verb)
        if flags is not None:
            if any(_carries_flag(a, f) for a in arguments for f in flags):
                return False
            continue
        if verb not in READ_ONLY_VERBS:
            return False
    return True


def redirect_paths(command: str, root: Path) -> set[str]:
    """Repo-relative paths this command redirects OUTPUT into.

    Targets are trimmed of trailing shell punctuation before resolving: an
    `awk` program ends `> "file"}'`, and the ragged capture never compared
    equal to the clean path `command_targets` produced, so the write slipped
    between the two.
    """
    found = set()
    for target in REDIRECT_TARGET.findall(command):
        # The whole target first (normalize_target strips quoting, so
        # `docs/'gold'/x` resolves), then its path-like fragments, which is
        # what rescues a target glued to trailing program punctuation.
        for candidate in [target, *PATHISH.findall(target)]:
            rel = relative_to_root(candidate, root)
            if rel:
                found.add(rel)
    return found


def check_control_commands(command: str) -> Decision:
    """Commands that rewrite the repo's own trust settings without naming
    the file they write."""
    for pattern, why in CONTROL_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return Decision(
                "ask",
                f"Doctrine: this command changes this repo's ENFORCEMENT "
                f"configuration - {why}. Approve only if you meant to change "
                "how your own gates behave.",
            )
    return Decision()


def check_protected_in_command(command: str, root: Path,
                               config: dict[str, list[str]]) -> Decision:
    """The path rule, applied to shell commands that would MUTATE a file.

    Each path the command names is judged on its own, by the same matcher
    the Write rule uses. The previous substring probe judged the whole
    command text, so an allowlisted word or an exempt filename ANYWHERE in
    it - a trailing comment sufficed - disabled every rule for that call.
    """
    rules = protected_rules(root, config)
    allowed = config.get("allow", [])
    # Only the PATH analysis works on cleaned text; the secret rules still
    # scan the raw command, so a credential inside a heredoc is still caught.
    command = strip_shell_noise(command)
    read_only = command_is_read_only(command)
    redirected = redirect_paths(command, root)
    for rel_path in command_targets(command, root):
        # A read-only verb may name a protected path freely - `cat` a gold
        # record, `git log` the checkpoint - unless the path is where its
        # output is being redirected, which is a write however benign the
        # verb looks (`echo x > gold/v1.json`).
        if read_only and rel_path not in redirected:
            continue
        if any(matches(rel_path, pattern) for pattern in PROTECTED_EXEMPT):
            continue
        if any(matches(rel_path, pattern) for pattern in allowed):
            continue
        for pattern, why in rules:
            if matches(rel_path, pattern):
                return Decision(
                    "deny",
                    f"Doctrine: this command would modify '{rel_path}' - "
                    f"{why}. A shell redirect is still a write. Use the "
                    f"owning tool, or record the exception in {CONFIG_REL} "
                    "under 'allow'.",
                )
        for pattern, why in CONTROL_SURFACE:
            if matches(rel_path, pattern):
                return Decision(
                    "ask",
                    f"Doctrine: this command would modify '{rel_path}', part "
                    f"of this repo's ENFORCEMENT surface - {why}. Approve "
                    "only if you meant to change how your own gates behave.",
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


def check_test_weakening_command(command: str) -> Decision:
    for pattern, label in TEST_COMMAND_WEAKENING:
        if re.search(pattern, command, re.IGNORECASE):
            return Decision(
                "ask",
                f"Doctrine non-negotiable #4 (never delete, skip, or weaken a "
                f"failing test to go green): this command is {label}. Fix the "
                "code, or get the human's approval - removing an obsolete "
                "test is legitimate, silencing a failure is not.",
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
    raw_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(raw_name, str):
        return Decision("deny", "Doctrine guard: this request has no readable "
                                "tool name, so it cannot be checked against "
                                "the non-negotiables. Denied by default.")
    tool_name = raw_name
    if tool_name not in WRITE_TOOLS and tool_name not in COMMAND_TOOLS:
        return Decision()
    if not isinstance(tool_input, dict):
        # A governed tool with an unreadable body is exactly what a bypass
        # looks like; coercing it to {} used to sail past every rule.
        return Decision("deny", f"Doctrine guard: the input to {tool_name} "
                                "could not be read, so it cannot be checked. "
                                "Denied by default.")

    for field in (("command",) if tool_name in COMMAND_TOOLS
                  else ("file_path", "notebook_path")):
        if typed_field(tool_input, field) is None:
            return Decision(
                "deny",
                f"Doctrine guard: '{field}' is not a string in this "
                f"{tool_name} request, so it cannot be checked against the "
                "non-negotiables. Denied by default.")

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
        verdict = check_control_commands(text)
        if verdict.decision:
            return verdict
        verdict = check_irreversible(text)
        if verdict.decision:
            return verdict
        verdict = check_test_weakening_command(text)
        if verdict.decision:
            return verdict
    if rel_path and tool_name in WRITE_TOOLS:
        verdict = check_test_weakening(rel_path, text)
        if verdict.decision:
            return verdict
    return Decision()


def governed_root(payload: object) -> Path | None:
    """The doctrine repo this request touches, if any.

    Anchoring on the session's cwd alone let a write INTO a governed repo go
    unjudged whenever the session started one directory up (a monorepo or a
    multi-repo workspace), so the target path is consulted too - and the
    stricter of the two wins.
    """
    candidates: list[Path] = []
    if isinstance(payload, dict):
        tool_input = payload.get("tool_input")
        if isinstance(tool_input, dict):
            target = target_path(tool_input)
            if target:
                text = normalize_target(target)
                try:
                    where = Path(text)
                    candidates.append(where if where.is_absolute()
                                      else Path.cwd() / where)
                except (OSError, ValueError):
                    pass
        if isinstance(payload.get("cwd"), str):
            candidates.append(Path(payload["cwd"]))
    candidates.append(Path.cwd())
    for candidate in candidates:
        try:
            start = candidate if candidate.is_dir() else candidate.parent
            root = find_root(start)
        except OSError:
            continue
        if root is not None:
            return root
    return None


def main(argv: list[str] | None = None) -> int:
    # Read BYTES and decode ourselves. sys.stdin.read() decodes with the
    # interpreter's stdin codec, and under a strict one (PYTHONIOENCODING,
    # LANG=C, most POSIX CI) one invalid byte raised UnicodeDecodeError from
    # OUTSIDE any try - exit 1, no decision, which the hook contract reads as
    # "proceed". The gate's own plumbing must never decide the outcome.
    try:
        stream = getattr(sys.stdin, "buffer", None)
        if sys.stdin.isatty():
            raw = ""
        elif stream is not None:
            raw = stream.read(MAX_PAYLOAD_BYTES).decode("utf-8", "replace")
        else:
            raw = sys.stdin.read(MAX_PAYLOAD_BYTES)
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:  # noqa: BLE001 - RecursionError is not a ValueError, and
        payload = None  # an un-parsed payload must never mean "no opinion"

    root = governed_root(payload)
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

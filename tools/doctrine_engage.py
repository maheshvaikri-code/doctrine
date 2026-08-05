#!/usr/bin/env python3
"""doctrine_engage: the per-turn awakening reminder (Layer 1).

Wired as a Claude Code ``UserPromptSubmit`` hook, this re-arms the Engagement
Protocol on EVERY user message: it prints a compact reminder that Claude Code
injects into the agent's context, so the doctrine is triggered per-task rather
than merely loaded once at session start and forgotten mid-session.

Repo-safe and consumer-safe: if no ``.Doctrine.md`` is found at (or above) the
working directory, it prints nothing and exits 0 -- a no-op outside a doctrine
repo. Output is ASCII-only (Windows cp1252 pipes crash on stray Unicode
punctuation) per the v0.6.10->v0.6.18 self-evolution retrospective.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

STALE_BANNER = (
    "[Doctrine STALE] The corpus on disk CHANGED since this session started, so "
    "the .Doctrine.md in your context is out of date -- CLAUDE.md's `@` import "
    "is resolved once, at session start, and editing the file on disk does not "
    "reload it. Roles or skills you believe exist may have been removed. "
    "RESTART THIS SESSION (/clear, or reopen) before trusting the loaded law; "
    "read any role or skill card fresh from disk until you do."
)

REMINDER = (
    "[Doctrine active] This repo runs on the Engineering Doctrine (.Doctrine.md). "
    "Before acting on the request above:\n"
    "  1. Open your reply with the [DOCTRINE ENGAGED] block.\n"
    "  2. Classify the task (S / M / L / HOTFIX) and name the role hat.\n"
    "  3. Read the routed skills/roles from the .Doctrine.md Section 6 routing "
    "table for whatever the task touches -- do not work from memory of them.\n"
    "  4. At G4/G5, DISPATCH the verifier subagents (code-reviewer, "
    "security-reviewer, qa-engineer) -- do not review your own build by "
    "switching hats. No subagents available? Say so in the artifact.\n"
    "  5. If docs/brief.md says 'Delivery profile: solobuilder' (or the legacy "
    "'Delivery profile: personal'), THE FULL ROLE SET "
    "STILL APPLIES -- wear the same craft hat an enterprise repo would "
    "('[ROLE: Interop Engineer]' for a CLI or API contract, "
    "'[ROLE: Database Engineer]' for a schema), then DevOps verification "
    "(creative build -> deterministic verification). This profile relaxes "
    "GATING ONLY: fewer artifacts, self-review instead of a dispatched panel. "
    "There is NO 'Solo Builder' role -- naming a profile where a role belongs "
    "is a defect. Otherwise execute the class gate path. Stop at every "
    "Section 5 escalation.\n"
    "Right-size the ceremony: a Class S task earns the one-line block."
)


def find_root(start: Path) -> Path | None:
    """Nearest ancestor (including ``start``) that contains ``.Doctrine.md``."""
    for d in (start, *start.parents):
        if (d / ".Doctrine.md").is_file():
            return d
    return None


def corpus_fingerprint(root: Path) -> str | None:
    """Fingerprint exactly what a session SNAPSHOTS at start and can go stale.

    That is `.Doctrine.md` (CLAUDE.md `@`-imports it once) plus the role and
    skill INVENTORY -- a deleted role card is the failure that motivated this.
    Card bodies are deliberately excluded: they are Read on demand mid-session,
    so they are always current and hashing them would fire on every edit.

    Returns None on any I/O trouble, so the caller stays silent rather than
    guessing.
    """
    try:
        h = hashlib.sha256()
        h.update((root / ".Doctrine.md").read_bytes())
        for sub in ("roles", "skills"):
            names = sorted(p.name
                           for p in (root / ".Doctrine" / sub).glob("*.md"))
            h.update(("\n".join(names) + "\n").encode("utf-8"))
        return h.hexdigest()[:12]
    except OSError:
        return None


def _session_id(raw: bytes) -> str | None:
    """Session id from the hook payload, or None. Decodes with replacement:
    one bad byte under a strict locale must not take the hook down (a hook
    that raises blocks the turn)."""
    try:
        payload = json.loads(raw.decode("utf-8", "replace") or "{}")
        sid = payload.get("session_id")
    except (ValueError, AttributeError):
        return None
    if not isinstance(sid, str):
        return None
    keep = "".join(c for c in sid if c.isalnum() or c in "-_")
    return keep[:64] or None


def drift_notice(root: Path, session_id: str | None) -> str:
    """"" normally; the STALE banner once the corpus moves under a session.

    The first turn of a session records the fingerprint; later turns compare.
    It keeps warning until the session is restarted, because until then the
    session really is still stale.
    """
    if session_id is None:
        return ""
    current = corpus_fingerprint(root)
    if current is None:
        return ""
    marker = (root / ".doctrine-state" / "local" / "sessions"
              / f"{session_id}.corpus")
    try:
        if marker.exists():
            return "" if marker.read_text("utf-8").strip() == current \
                else STALE_BANNER + "\n\n"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(current + "\n", encoding="utf-8")
    except OSError:
        return ""      # never let bookkeeping break the turn
    return ""


def main(argv: list[str] | None = None) -> int:
    # No arguments are needed; tolerate any (hook robustness).
    root = find_root(Path.cwd())
    if root is None:
        return 0  # not a doctrine repo -> silent no-op
    notice = ""
    try:
        raw = sys.stdin.buffer.read() if not sys.stdin.isatty() else b""
        notice = drift_notice(root, _session_id(raw))
    except Exception:  # noqa: BLE001 - the reminder must print regardless
        notice = ""
    sys.stdout.write(notice + REMINDER + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

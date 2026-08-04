#!/usr/bin/env python3
"""doctrine_fleet - one view of every repo the doctrine governs.

Every other artifact in this system is per-repo. A portfolio running Doctrine
in N repositories has no way to answer "which of these drifted?" without
visiting all N by hand - so nobody does, and the fleet silently diverges.

    python tools/doctrine_fleet.py status ../repo-a ../repo-b
    python tools/doctrine_fleet.py status --root .. --json
    python tools/doctrine_fleet.py status            # reads fleet.json

Repos come from arguments, from ``--root DIR`` (scanned one level deep), or
from ``.doctrine-state/fleet.json`` (``{"repos": ["../a", "../b"]}``).

STRICTLY READ-ONLY: this tool never writes to a repository it inspects. Exit
0 when every repo matches the source, 1 when any has drifted - so a
scheduled CI job can watch the fleet. Output is ASCII (Windows cp1252 pipes
crash on stray Unicode punctuation).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

FLEET_CONFIG_REL: Final = ".doctrine-state/fleet.json"
VERSION_RE: Final = re.compile(r"v(\d+\.\d+\.\d+)")
GIT_TIMEOUT_SECONDS: Final = 10
# Scanned repos are untrusted input: read a bounded amount of any file rather
# than whatever a hostile (or merely broken) repo happens to put there.
MAX_HEADER_BYTES: Final = 4096
MAX_CARRIER_BYTES: Final = 4 * 1024 * 1024
# The files whose drift breaks a consumer's own lint/packaging - the same
# consistency carriers doctrine_install refuses to update piecemeal.
CARRIERS: Final = (".Doctrine.md", ".Doctrine/README.md",
                   "tools/doctrine_install.py")


def is_doctrine_repo(path: Path) -> bool:
    """Whether a directory carries the law - never raising on the answer.

    An unreadable sibling under ``--root`` used to take the whole fleet view
    down with a PermissionError traceback, while every other failure in this
    module degrades to "unknown".
    """
    try:
        return (path / ".Doctrine.md").is_file()
    except OSError:
        return False


def skip_reason(path: Path) -> str:
    """Why a named path produced no row."""
    try:
        (path / ".Doctrine.md").is_file()
    except OSError as exc:
        return f"unreadable ({exc.__class__.__name__})"
    try:
        if not path.exists():
            return "no such path"
        if not path.is_dir():
            return "not a directory"
    except OSError as exc:
        return f"unreadable ({exc.__class__.__name__})"
    return "no .Doctrine.md"


def read_version(root: Path) -> str | None:
    """The doctrine version from a repo's ``.Doctrine.md`` header line."""
    law = root / ".Doctrine.md"
    if not is_doctrine_repo(root):
        return None
    try:
        with law.open("r", encoding="utf-8", errors="replace") as handle:
            first = handle.readline(MAX_HEADER_BYTES)
    except OSError:
        return None
    match = VERSION_RE.search(first)
    return match.group(1) if match else None


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def run_git(root: Path, *args: str) -> str | None:
    """Read-only git query; None when git or the repo is unavailable.

    Every flag here earns its place from a real finding:

    * ``--no-optional-locks`` - plain ``git status`` refreshes and rewrites
      the index whenever the stat cache is stale (i.e. after any fresh
      clone), so a "read-only" scan both mutated the repo and took
      ``index.lock`` in someone else's working tree.
    * ``core.fsmonitor=`` and ``core.hooksPath`` - both are read from the
      SCANNED repo's config and name a command git will execute. Inspecting
      an untrusted repo must not run its code; a security pass proved
      ``core.fsmonitor`` firing during a fleet scan.
    """
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks",
             "-c", "core.fsmonitor=",
             "-c", f"core.hooksPath={os.devnull}",
             *args],
            cwd=root, capture_output=True, text=True,
            check=False, timeout=GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def describe_drift(root: Path, source: Path, version: str | None,
                   source_version: str | None) -> str:
    """How this install differs from the source tree, most severe first."""
    if version is None:
        return "no-doctrine"
    if source_version is None:
        return "unknown"
    if version != source_version:
        try:
            behind = version_tuple(version) < version_tuple(source_version)
        except ValueError:
            return "unknown"
        return f"behind v{source_version}" if behind else "ahead"
    for rel in CARRIERS:
        installed, original = root / rel, source / rel
        try:
            if not original.is_file():
                continue
            if not installed.is_file():
                return "incomplete"
            if installed.stat().st_size > MAX_CARRIER_BYTES:
                return "unreadable"      # a scanned repo does not get to
            with installed.open("rb") as new, original.open("rb") as old:
                if new.read(MAX_CARRIER_BYTES) != old.read(MAX_CARRIER_BYTES):
                    return "modified"    # decide how much memory we spend
        except OSError:
            return "unreadable"
    return "current"


def describe_state(root: Path) -> str:
    """State-plane posture, read straight off disk (never mutated here)."""
    checkpoint = root / ".doctrine-state" / "checkpoint.json"
    try:
        if not checkpoint.is_file():
            return "none"
        data = json.loads(checkpoint.read_text("utf-8"))
    except (OSError, ValueError, RecursionError):
        return "unreadable"
    if not isinstance(data, dict):
        return "unreadable"
    seq = data.get("seq")
    return f"seq {seq}" if seq is not None else "present"


def describe_release(root: Path) -> str:
    """Latest tag and how far HEAD has travelled past it."""
    tag = run_git(root, "describe", "--tags", "--abbrev=0")
    if not tag:
        return "untagged"
    ahead = run_git(root, "rev-list", "--count", f"{tag}..HEAD")
    if ahead and ahead != "0":
        return f"{tag} +{ahead}"
    return tag


def inspect(path: Path, source: Path, source_version: str | None) -> dict[str, Any]:
    root = path.resolve()
    version = read_version(root)
    status = run_git(root, "status", "--porcelain")
    gold_dir = root / "docs" / "releases" / "gold"
    return {
        "repo": root.name,
        "path": root.as_posix(),
        "doctrineVersion": version,
        "drift": describe_drift(root, source, version, source_version),
        "state": describe_state(root),
        "worktree": ("unknown" if status is None
                     else ("dirty" if status else "clean")),
        "release": describe_release(root),
        "goldRecords": count_gold_records(gold_dir),
    }


def count_gold_records(gold_dir: Path) -> int:
    try:
        return len(list(gold_dir.glob("*.json"))) if gold_dir.is_dir() else 0
    except OSError:
        return 0


def discover(root: Path) -> list[Path]:
    """Doctrine repos one level under ``root`` (plus ``root`` itself).

    One unreadable sibling must not take down the whole fleet view - a scan
    is a survey, and a directory it cannot open is a row it cannot fill, not
    a reason to abandon the other repos.
    """
    found = [root] if is_doctrine_repo(root) else []
    try:
        children = sorted(root.iterdir())
    except OSError:
        return found
    for child in children:
        try:
            if child.is_dir() and is_doctrine_repo(child):
                found.append(child)
        except OSError:
            continue
    return found


def from_config(start: Path) -> list[Path]:
    config = start / FLEET_CONFIG_REL
    try:
        if not config.is_file():
            return []
        data = json.loads(config.read_text("utf-8"))
    except (OSError, ValueError, RecursionError):
        return []
    repos = data.get("repos") if isinstance(data, dict) else None
    if not isinstance(repos, list):
        return []
    return [(start / str(entry)).resolve() for entry in repos
            if isinstance(entry, str)]


def render_table(rows: list[dict[str, Any]]) -> str:
    headers = ("REPO", "DOCTRINE", "DRIFT", "STATE", "WORKTREE", "RELEASE")
    table = [headers] + [
        (row["repo"], row["doctrineVersion"] or "-", row["drift"],
         row["state"], row["worktree"], row["release"])
        for row in rows
    ]
    widths = [max(len(str(r[i])) for r in table) for i in range(len(headers))]
    lines = []
    for index, row in enumerate(table):
        lines.append("  ".join(str(cell).ljust(widths[i])
                               for i, cell in enumerate(row)).rstrip())
        if index == 0:
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines)


def cmd_status(paths: list[Path], source: Path, as_json: bool) -> int:
    # Repo names come from the filesystem, so the output can carry any
    # character the OS allows. A Windows cp1252 console raised
    # UnicodeEncodeError on a CJK or emoji directory name and took the whole
    # command down; ASCII-only source strings never protected this path.
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError, OSError):
            stream.reconfigure(errors="backslashreplace")

    source_version = read_version(source)
    rows, skipped_paths = [], []
    for path in paths:
        if is_doctrine_repo(path):
            rows.append(inspect(path, source, source_version))
        else:
            # Distinguish "not a doctrine repo" from "could not look": an
            # operator told a permission-denied directory has no .Doctrine.md
            # draws exactly the wrong conclusion about their fleet.
            skipped_paths.append((path, skip_reason(path)))
    skipped = len(skipped_paths)

    if as_json:
        json.dump({"source": source.as_posix(),
                   "sourceVersion": source_version,
                   "repos": rows, "skipped": skipped},
                  sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    elif not rows:
        print("doctrine_fleet: no Doctrine repos found. Name them as "
              "arguments, pass --root DIR, or list them in "
              f"{FLEET_CONFIG_REL}.")
    else:
        print(f"source: {source.as_posix()} (v{source_version or '?'})")
        print(render_table(rows))
        for path, reason in skipped_paths:
            print(f"(skipped {path.name}: {reason})")

    drifted = [r for r in rows if r["drift"] != "current"]
    if drifted and not as_json:
        print(f"\n{len(drifted)} repo(s) differ from the source: "
              + ", ".join(f"{r['repo']} ({r['drift']})" for r in drifted))
        print("update one with: python tools/doctrine_install.py "
              "--target <path> --force")
    return 1 if drifted else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="doctrine_fleet", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status", help="posture of every governed repo")
    status.add_argument("repos", nargs="*", type=Path,
                        help="repo paths; omit to use --root or fleet.json")
    status.add_argument("--root", type=Path, default=None,
                        help="scan this directory one level deep")
    status.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().parent.parent,
                        help="the doctrine source tree to compare against")
    status.add_argument("--json", action="store_true",
                        help="machine-readable output")
    args = parser.parse_args(argv)

    paths = [p.resolve() for p in args.repos]
    if not paths and args.root is not None:
        paths = discover(args.root.resolve())
    if not paths:
        paths = from_config(Path.cwd())
    return cmd_status(paths, args.source.resolve(), args.json)


if __name__ == "__main__":
    raise SystemExit(main())

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
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

FLEET_CONFIG_REL: Final = ".doctrine-state/fleet.json"
VERSION_RE: Final = re.compile(r"v(\d+\.\d+\.\d+)")
GIT_TIMEOUT_SECONDS: Final = 10
# The files whose drift breaks a consumer's own lint/packaging - the same
# consistency carriers doctrine_install refuses to update piecemeal.
CARRIERS: Final = (".Doctrine.md", ".Doctrine/README.md",
                   "tools/doctrine_install.py")


def read_version(root: Path) -> str | None:
    """The doctrine version from a repo's ``.Doctrine.md`` header line."""
    law = root / ".Doctrine.md"
    if not law.is_file():
        return None
    try:
        first = law.read_text("utf-8", "replace").splitlines()[0]
    except (OSError, IndexError):
        return None
    match = VERSION_RE.search(first)
    return match.group(1) if match else None


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def run_git(root: Path, *args: str) -> str | None:
    """Read-only git query; None when git or the repo is unavailable."""
    try:
        proc = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True,
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
        if not original.is_file():
            continue
        if not installed.is_file():
            return "incomplete"
        try:
            if installed.read_bytes() != original.read_bytes():
                return "modified"
        except OSError:
            return "unreadable"
    return "current"


def describe_state(root: Path) -> str:
    """State-plane posture, read straight off disk (never mutated here)."""
    checkpoint = root / ".doctrine-state" / "checkpoint.json"
    if not checkpoint.is_file():
        return "none"
    try:
        data = json.loads(checkpoint.read_text("utf-8"))
    except (OSError, ValueError):
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
        "goldRecords": (len(list(gold_dir.glob("*.json")))
                        if gold_dir.is_dir() else 0),
    }


def discover(root: Path) -> list[Path]:
    """Doctrine repos one level under ``root`` (plus ``root`` itself)."""
    found = [root] if (root / ".Doctrine.md").is_file() else []
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if (child / ".Doctrine.md").is_file():
            found.append(child)
    return found


def from_config(start: Path) -> list[Path]:
    config = start / FLEET_CONFIG_REL
    if not config.is_file():
        return []
    try:
        data = json.loads(config.read_text("utf-8"))
    except (OSError, ValueError):
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
    source_version = read_version(source)
    rows = [inspect(p, source, source_version) for p in paths
            if (p / ".Doctrine.md").is_file()]
    skipped = len(paths) - len(rows)

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
        if skipped:
            print(f"({skipped} path(s) skipped: no .Doctrine.md)")

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

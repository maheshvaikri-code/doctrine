#!/usr/bin/env python3
"""doctrine_verify — the one-command gate suite, cross-platform.

`make verify` requires GNU Make, which stock Windows lacks; this runner
is the same sequence with no dependency beyond Python:

    python tools/doctrine_verify.py

Scope adapts to where it runs:
  * Doctrine SOURCE repo (declares the `doctrineos` package): the full dev
    suite - corpus lint -> ruff -> the unittest suite -> state verify.
  * CONSUMER repo (Doctrine installed alongside the host's own code): only
    Doctrine's own surface - corpus lint -> state verify. The host's own
    code is the host's tooling's job: `doctrine_verify` must NOT ruff the
    host's files or run the host's test suite. (Run Doctrine's own tool
    tests explicitly with `unittest discover -s tests -p "test_doctrine_*.py"`.)

State verify is skipped when no state plane exists yet. Exit 0 only when
every executed gate passes; each gate's REAL output streams through
untouched.
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path


def run_gate(name: str, cmd: list[str], cwd: Path) -> bool:
    print(f"=== {name}: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    print(f"=== {name}: {'PASS' if result.returncode == 0 else 'FAIL'}\n")
    return result.returncode == 0


def is_source_repo(root: Path) -> bool:
    """True only in Doctrine's own source repo. The installer never copies
    pyproject.toml, and only the source declares the `doctrineos` package;
    a consumer either has no pyproject or names its own package. Source runs
    the full dev suite; a consumer verifies only its installed Doctrine
    surface (corpus lint + state) and leaves ruff/pytest of the host's own
    code to the host's own tooling."""
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return False
    try:
        with pyproject.open("rb") as fh:
            project = tomllib.load(fh).get("project", {})
        return isinstance(project, dict) and project.get("name") == "doctrineos"
    except (OSError, tomllib.TOMLDecodeError):
        return False


def git_knows_gold(root: Path) -> bool:
    """Whether git has ever tracked a gold record here.

    Consulted so that deleting the whole directory cannot make the gate
    disappear: git remembers what the working tree no longer shows.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "docs/releases/gold"],
            cwd=root, capture_output=True, check=False, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0 and bool(proc.stdout.strip())


def ruff_available(root: Path) -> bool:
    """Return whether the source repo's required Ruff gate can execute."""
    try:
        import ruff  # noqa: F401
        return True
    except ImportError:
        return subprocess.run(
            [sys.executable, "-m", "ruff", "--version"], cwd=root,
            capture_output=True).returncode == 0


def main(argv: list[str] | None = None) -> int:
    # `--help` used to be taken as a directory name and crash with
    # NotADirectoryError. A gate runner that cannot explain itself is a
    # gate runner people work around.
    arguments = list(argv or [])
    if arguments and arguments[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    root = Path(arguments[0]).resolve() if arguments else Path.cwd()
    py = sys.executable
    results: list[tuple[str, bool]] = []

    results.append(("lint", run_gate(
        "lint", [py, "tools/doctrine_lint.py"], root)))

    if is_source_repo(root):
        if ruff_available(root):
            results.append(("ruff", run_gate(
                "ruff", [py, "-m", "ruff", "check", "tools", "tests"], root)))
        else:
            print("=== ruff: FAIL - required source-repo gate is unavailable "
                  "(install the pinned CI version: pip install ruff==0.15.15)\n")
            results.append(("ruff", False))
        results.append(("tests", run_gate(
            "tests", [py, "-m", "unittest", "discover", "-s", "tests"], root)))
    else:
        print("=== ruff + tests: consumer repo - skipped. Your own tooling "
              "owns linting your code and running your tests; Doctrine "
              "verifies its corpus (lint) and state here. Doctrine's own "
              "tool tests, if you want them: "
              'python -m unittest discover -s tests -p "test_doctrine_*.py"\n')

    # Evidence integrity, checked by hash rather than by intercepting whoever
    # wrote it. The PreToolUse guard is a best-effort tripwire on shell
    # commands; THIS is the gate that holds, because a tampered record fails
    # here regardless of which primitive modified it.
    # Run whenever the directory OR its manifest exists. Gating on the
    # directory alone meant `mv docs/releases lib` deleted every record and
    # the gate simply vanished from the run - VERIFY OK, one fewer gate, no
    # warning. An absence must be checked, not used as a reason to skip.
    gold_dir = root / "docs" / "releases" / "gold"
    if gold_dir.is_dir() or (gold_dir / "MANIFEST.json").exists() or \
            git_knows_gold(root):
        results.append(("gold", run_gate(
            "gold", [py, "tools/doctrine_gold.py", "gate"], root)))
    else:
        # Announced, like every other skip. A gate that vanishes without
        # a word is indistinguishable from a gate that passed.
        print("=== gold: no gold records and git has never tracked any "
              "- skipped (nothing promoted yet)\n")

    if (root / ".doctrine-state" / "checkpoint.json").exists():
        results.append(("state", run_gate(
            "state", [py, "tools/doctrine_state.py", "verify"], root)))
    else:
        print("=== state: no state plane yet - skipped "
              "(python tools/doctrine_state.py init)\n")

    failed = [name for name, ok in results if not ok]
    if failed:
        print(f"VERIFY FAILED: {', '.join(failed)}")
        return 1
    print(f"VERIFY OK: {len(results)} gate(s) green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

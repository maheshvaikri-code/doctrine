#!/usr/bin/env python3
"""doctrine_features - read the repo's FEATURES.md toggles.

FEATURES.md is the repo's autonomy/behaviour switchboard: `on` / `off` only,
deliberately not an allowlist of permitted commands. A blessed-strings list
goes stale, grows forever, and implies a precision it does not have; a switch
is honest about what it does.

Read once per session by the agent (CLAUDE.md `@`-imports it) and re-read on
demand via `/features`. Tools that must HONOUR a toggle -- rather than merely
describe one -- call `is_on()` here, so the table is not decorative.

Fail-open by design: an unreadable, missing, or malformed FEATURES.md yields
the default (on). A toggle file that silently disables behaviour when it fails
to parse would be a worse failure than not having one.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FEATURES_FILE = "FEATURES.md"
# `| `name` | on | ...` / `| `name` | **off** | ...` - state cell, bold or not.
_ROW = re.compile(
    r"^\|\s*`(?P<name>[a-z0-9-]+)`\s*\|\s*\*{0,2}(?P<state>on|off)\*{0,2}\s*\|",
    re.IGNORECASE | re.MULTILINE)


def find_root(start: Path) -> Path | None:
    """Nearest ancestor (including `start`) holding `.Doctrine.md`."""
    for d in (start, *start.parents):
        if (d / ".Doctrine.md").is_file():
            return d
    return None


def read_features(root: Path) -> dict[str, bool]:
    """{name: is_on} parsed from FEATURES.md. Empty dict if unreadable."""
    try:
        text = (root / FEATURES_FILE).read_bytes().decode("utf-8", "replace")
    except OSError:
        return {}
    return {m.group("name").lower(): m.group("state").lower() == "on"
            for m in _ROW.finditer(text)}


def is_on(root: Path, name: str, default: bool = True) -> bool:
    """True unless FEATURES.md explicitly says `off`.

    Default-on matters: a repo installed before a toggle existed, or one whose
    FEATURES.md a user deleted, must keep working exactly as before rather
    than silently losing behaviour.
    """
    return read_features(root).get(name.lower(), default)


def main(argv: list[str] | None = None) -> int:
    root = find_root(Path.cwd())
    if root is None:
        print("not a doctrine repo (no .Doctrine.md found)", file=sys.stderr)
        return 1
    features = read_features(root)
    if not features:
        print(f"no readable {FEATURES_FILE} at {root} - "
              "every feature defaults to ON")
        return 0
    width = max(len(n) for n in features)
    print(f"{FEATURES_FILE} at {root}:")
    for name, on in sorted(features.items()):
        print(f"  {name:<{width}}  {'on' if on else 'OFF'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

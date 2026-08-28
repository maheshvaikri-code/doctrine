"""Locate the Go binary and the Python reference, in either repo layout.

These oracles hold the Go implementation to the Python one, so they need BOTH.
That is fine while doctrineos lives inside the doctrine tree and awkward the
moment it does not - and it should not become a reason to drop the oracles,
because they are the only evidence the port is faithful.

Two layouts are supported, and the same files work in both:

    in-tree      <doctrine>/doctrineos/oracles/     reference at ../../tools
    standalone   <doctrineos>/oracles/              reference found, or skipped

The Go binary is at `parents[1]/dos` either way, because `oracles/` always sits
directly under the Go module.

The reference is searched in this order, and the search is EXPLICIT rather than
clever: a harness that silently compares against the wrong thing is worse than
one that refuses to run.

    1. $DOCTRINE_REF          - an explicit path to a doctrine checkout
    2. ../../tools            - the in-tree layout
    3. ../../doctrine/tools   - a sibling checkout beside doctrineos

When none is found, `require_reference()` exits with a message naming what to
do. It does NOT fall back to comparing Go against itself.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE = HERE.parent                      # the Go module root, either layout
EXE = ".exe" if os.name == "nt" else ""
GO = MODULE / ("dos" + EXE)
CONTROL = MODULE / ("preschema" + EXE)    # optional pre-schema control binary


def _candidates():
    if env := os.environ.get("DOCTRINE_REF"):
        yield Path(env)
    yield MODULE.parent                   # in-tree: <doctrine>/
    yield MODULE.parent / "doctrine"      # sibling checkout


def find_reference():
    """The doctrine checkout holding tools/ and .Doctrine/, or None."""
    for c in _candidates():
        try:
            if (c / "tools" / "doctrine_state.py").is_file():
                return c.resolve()
        except OSError:
            continue
    return None


def require_reference():
    """The reference checkout, or exit 2 saying exactly how to supply one."""
    ref = find_reference()
    if ref is None:
        print(
            "error: no doctrine reference checkout found.\n"
            "  These oracles compare the Go implementation against the Python\n"
            "  one; without the reference there is nothing to compare to, and\n"
            "  a harness that quietly compares Go against itself would report\n"
            "  perfect agreement while proving nothing.\n"
            "\n"
            "  Supply one with:\n"
            "    DOCTRINE_REF=/path/to/doctrine python " + Path(sys.argv[0]).name + "\n"
            "  or clone it beside this repo as ../doctrine",
            file=sys.stderr)
        raise SystemExit(2)
    return ref


def reference_tools():
    """Put the reference's tools/ on sys.path and return the checkout root."""
    ref = require_reference()
    tools = str(ref / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    return ref


def require_binary():
    """The built Go binary, or exit 2 with the build command."""
    if not GO.exists():
        print(f"error: {GO.name} not built.\n  build it with: cd {MODULE} && go build -o dos .",
              file=sys.stderr)
        raise SystemExit(2)
    return GO

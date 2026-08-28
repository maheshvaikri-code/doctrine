"""Differential oracle for HYDRATION - the bundle a fresh session actually reads.

The bundle body is deterministic by design: no timestamps, no map iteration,
nothing that varies between two runs over identical state. That makes it the
one artifact here that can be compared the strictest possible way - byte for
byte - so this oracle does exactly that and nothing weaker.

Why it matters that this is exact rather than "close enough": the bundle is
what the next agent believes. A section trimmed in one implementation and not
the other, a staleness marker present in one and missing in the other, and two
agents resume the same repo with different pictures of it - while both report
success. There is no later gate that catches that.

The real repo's own plane is the most valuable case and is checked first: it
carries 31 checkpoints, real distillates, and (usefully) enough content to
trigger BOTH the degradation and staleness paths, which synthetic fixtures
reach only by construction.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXE = ".exe" if os.name == "nt" else ""
GO = REPO / "doctrineos" / ("dos" + EXE)
PY = REPO / "tools" / "doctrine_state.py"

sys.path.insert(0, str(REPO / "tools"))
import doctrine_state as ds  # the reference implementation


def go_body(root):
    p = subprocess.run([str(GO), "hydrate", "--body"], cwd=str(root),
                       capture_output=True, timeout=300)
    return p.stdout if p.returncode == 0 else None


def py_body(root):
    try:
        body, trimmed, stale = ds.build_bundle_body(ds.Plane(root))
        return body.encode("utf-8"), trimmed, stale
    except Exception as exc:
        return None, [f"ERROR:{exc}"], []


def compare(label, root):
    pb, trimmed, stale = py_body(root)
    gb = go_body(root)
    if pb is None:
        return False, f"python failed: {trimmed}"
    if gb is None:
        return False, "go failed to emit a body"
    same = pb == gb
    detail = f"{len(pb)} bytes"
    if trimmed:
        detail += f", trimmed={','.join(trimmed)}"
    if stale:
        detail += f", stale={','.join(stale)}"
    if not same:
        import difflib
        diff = list(difflib.unified_diff(
            pb.decode("utf-8", "replace").splitlines(),
            gb.decode("utf-8", "replace").splitlines(),
            "python", "go", lineterm=""))[:10]
        detail += "\n" + "\n".join("      " + d[:130] for d in diff)
    return same, detail


def make_repo():
    d = Path(tempfile.mkdtemp())
    (d / ".Doctrine.md").write_text(
        "# law\n\n## 1. Prime Directive\nShip honestly.\n\n"
        "## 7. Non-Negotiables\nNever fabricate.\n", encoding="utf-8")
    shutil.copytree(REPO / ".Doctrine" / "state-plane", d / ".Doctrine" / "state-plane")
    for cmd in (("git", "init", "-q"),
                ("git", "config", "user.email", "t@example.invalid"),
                ("git", "config", "user.name", "T"),
                ("git", "add", "."), ("git", "commit", "-qm", "seed")):
        subprocess.run(cmd, cwd=d, capture_output=True)
    return d


def checkpoint(root, n, *, intents=None, learned=None, dead_ends=None,
               open_threads=None, session="s-hyd"):
    p = {
        "session_id": session,
        "control": {"role": "backend-engineer", "phase": "build",
                    "brevity_mode": "full",
                    "active_intents": intents or []},
        "distillate": {
            "task_refs": intents or [],
            "learned": learned if learned is not None else [],
            "dead_ends": dead_ends if dead_ends is not None else [],
            "open_threads": open_threads or [],
            "next_actions": [],
        },
    }
    f = root / f"prop-{n}.json"
    f.write_bytes(json.dumps(p, indent=2).encode("utf-8"))
    r = subprocess.run([sys.executable, str(PY), "checkpoint", "--proposal", str(f)],
                       cwd=str(root), capture_output=True, text=True, timeout=300)
    return r


# --- synthetic cases, each reaching a branch the previous one does not -------
def case_minimal(root):
    checkpoint(root, 0)
    return "empty distillate, no intents"


def case_with_content(root):
    checkpoint(root, 0,
               learned=[{"kind": "fact", "claim": "retries need a cap",
                         "evidence": "test", "confidence": "verified"}],
               dead_ends=[{"approach": "unbounded retry",
                           "why_failed": "thrashed for an hour"}],
               open_threads=["decide the cap"])
    return "learned + dead_ends + open_threads"


def case_missing_intent(root):
    """An active intent whose file does not exist.

    The bundle must say MISSING rather than omit the line: an intent that
    silently vanishes from the bundle is one the next session stops working on
    without ever being told.
    """
    checkpoint(root, 0, intents=["intent-that-does-not-exist"])
    return "active intent with no file -> MISSING"


def case_trimming(root):
    """Content past the distillate budget, forcing degrade-then-clip.

    The degraded form keeps dead_ends and open_threads only - the
    anti-thought-drift payload survives a squeeze, because repeating a
    known-failed approach is the expensive failure.
    """
    ends = [{"approach": f"approach number {i} " + "x" * 120,
             "why_failed": f"reason number {i} " + "y" * 120}
            for i in range(8)]
    learned = [{"kind": "fact", "claim": f"claim {i} " + "z" * 200,
                "evidence": "e" * 100, "confidence": "inferred"}
               for i in range(6)]
    checkpoint(root, 0, learned=learned, dead_ends=ends)
    return "over budget -> degrade + clip"


def case_stale(root):
    """A checkpoint recorded at a commit that is no longer HEAD."""
    checkpoint(root, 0)
    (root / "later.txt").write_text("moved on\n", encoding="utf-8")
    for cmd in (("git", "add", "."), ("git", "commit", "-qm", "advance")):
        subprocess.run(cmd, cwd=root, capture_output=True)
    return "HEAD advanced -> STALE markers"


def case_chain_of_three(root):
    """Dead ends merge across ALL retained distillates, newest first."""
    for i in range(3):
        checkpoint(root, i, dead_ends=[{"approach": f"a{i}", "why_failed": f"w{i}"}])
    return "3 checkpoints, dead_ends merged across retained"


CASES = [case_minimal, case_with_content, case_missing_intent,
         case_trimming, case_stale, case_chain_of_three]

if __name__ == "__main__":
    print(f"{'case':<44} {'ok':<5} detail")
    print("-" * 96)
    passed = total = 0

    # The real repo first - the most valuable fixture, and not synthetic.
    ok, detail = compare("this repo", REPO)
    passed += ok
    total += 1
    print(f"{'THIS REPO (31 checkpoints, real state)':<44} {'yes' if ok else 'NO':<5} {detail}")

    for case in CASES:
        root = make_repo()
        try:
            label = case(root)
            ok, detail = compare(label, root)
            passed += ok
            total += 1
            print(f"{label:<44} {'yes' if ok else 'NO':<5} {detail}")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    print("-" * 96)
    print(f"bundle bodies byte-identical {passed}/{total}")

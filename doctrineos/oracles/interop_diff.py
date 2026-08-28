"""Cross-implementation INTEROP for the state-chain write path.

Message-diffing is the right test for a reader. For a WRITER it is far too
weak: two implementations can describe a checkpoint identically and still emit
bytes the other refuses, and the cost of that is asymmetric. A reader that is
wrong reports one bad verdict; a writer that is wrong corrupts the evidence
every future reader depends on.

So this oracle never compares messages. It compares ACCEPTANCE:

  * Go writes a chain      -> Python's verifier must accept it
  * Python writes a chain  -> Go's verifier must accept it
  * they INTERLEAVE        -> both must accept the result

The interleaved case is the one that matters. A repo does not get to promise
that the same binary writes every checkpoint forever: an agent may run Go
today, Python on a colleague's machine tomorrow, and the chain has to survive
the handover. Each link hashes its predecessor's exact bytes, so a single
byte of encoder drift anywhere in the chain breaks every link after it - and
breaks it in the way that is indistinguishable from tampering.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import _locate

REPO = _locate.reference_tools()      # doctrine checkout (also puts tools/ on path)
GO = _locate.require_binary()
PY = REPO / "tools" / "doctrine_state.py"


def make_repo():
    """A real git repo with the corpus schemas - both writers need HEAD."""
    d = Path(tempfile.mkdtemp())
    (d / ".Doctrine.md").write_text("# law\n", encoding="utf-8")
    shutil.copytree(REPO / ".Doctrine" / "state-plane",
                    d / ".Doctrine" / "state-plane")
    for cmd in (("git", "init", "-q"),
                ("git", "config", "user.email", "t@example.invalid"),
                ("git", "config", "user.name", "T"),
                ("git", "add", "."),
                ("git", "commit", "-qm", "seed")):
        subprocess.run(cmd, cwd=d, capture_output=True)
    return d


def proposal(root, n, *, secret=None, marker=None, session="s-interop"):
    """A schema-valid proposal. `secret`/`marker` inject text that MUST be
    refused, to check both writers fail closed on the same input.

    `session` is constant across a sequence ON PURPOSE. The first version of
    this harness varied it per checkpoint, and every sequence failed at seq 1
    with "state plane is leased by session s-interop-0" - the lease working
    exactly as designed, on a scenario that does not occur: one session writes
    a run of checkpoints. Varying it tested the lease, not interop.
    """
    claim = secret or marker or f"decision number {n}"
    p = {
        "session_id": session,
        "control": {
            "role": "backend-engineer",
            "phase": "build",
            "brevity_mode": "full",
            "active_intents": [],
        },
        "distillate": {
            "task_refs": [],
            "learned": [{"kind": "decision_ref", "claim": claim,
                         "evidence": f"evidence {n}",
                         "confidence": "verified"}],
            "dead_ends": [{"approach": f"approach {n}",
                           "why_failed": f"why {n}"}],
            "open_threads": [],
            "next_actions": [],
        },
    }
    f = root / f"proposal-{n}.json"
    f.write_bytes(json.dumps(p, indent=2).encode("utf-8"))
    return f


def write_go(root, prop):
    return subprocess.run([str(GO), "checkpoint", "--proposal", str(prop)],
                          cwd=str(root), capture_output=True, text=True, timeout=300)


def write_py(root, prop):
    return subprocess.run([sys.executable, str(PY), "checkpoint", "--proposal", str(prop)],
                          cwd=str(root), capture_output=True, text=True, timeout=300)


def verify_go(root):
    return subprocess.run([str(GO), "verify"], cwd=str(root),
                          capture_output=True, text=True, timeout=300)


def verify_py(root):
    return subprocess.run([sys.executable, str(PY), "verify"], cwd=str(root),
                          capture_output=True, text=True, timeout=300)


def both_accept(root):
    g, p = verify_go(root), verify_py(root)
    ok = g.returncode == 0 and p.returncode == 0
    detail = ""
    if not ok:
        detail = (f"\n      go  ({g.returncode}): {(g.stdout + g.stderr).strip()[:200]}"
                  f"\n      py  ({p.returncode}): {(p.stdout + p.stderr).strip()[:200]}")
    return ok, detail


SEQUENCES = {
    "go writes 3":            ["go", "go", "go"],
    "python writes 3":        ["py", "py", "py"],
    "go then python":         ["go", "py"],
    "python then go":         ["py", "go"],
    "interleaved g/p/g/p":    ["go", "py", "go", "py"],
    "python seeds, go extends": ["py", "py", "go", "go"],
}


def run_sequence(name, writers):
    root = make_repo()
    try:
        for i, w in enumerate(writers):
            prop = proposal(root, i, session="s-interop")
            r = write_go(root, prop) if w == "go" else write_py(root, prop)
            if r.returncode != 0:
                return False, f"{w} writer failed at seq {i}: {(r.stdout + r.stderr).strip()[:200]}"
        ok, detail = both_accept(root)
        n = len(list((root / ".doctrine-state" / "checkpoints").glob("*.json")))
        return ok, (f"{n} checkpoints, both verifiers accept" if ok
                    else f"REFUSED{detail}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run_refusal(label, kwargs):
    """Both writers must refuse the same poisoned proposal."""
    root = make_repo()
    try:
        prop = proposal(root, 0, **kwargs)
        g, p = write_go(root, prop), write_py(root, prop)
        agree = (g.returncode != 0) == (p.returncode != 0)
        both_refused = g.returncode != 0 and p.returncode != 0
        state = (root / ".doctrine-state")
        # fail closed means NOTHING was written, not "written then complained"
        clean = not state.exists() or not any(state.rglob("*.json"))
        return (agree and both_refused and clean,
                f"go={g.returncode} py={p.returncode} plane_clean={clean}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run_lease_refusal():
    """A SECOND session must be refused - by both, with nothing written.

    Kept because the first harness hit this by accident. Two writers racing a
    chain is the failure the lease exists for: concurrent writes fork it, and
    a fork is expensive to unpick precisely because both halves look valid.
    """
    root = make_repo()
    try:
        first = proposal(root, 0, session="session-A")
        r = write_go(root, first)
        if r.returncode != 0:
            return False, f"setup write failed: {(r.stdout + r.stderr).strip()[:120]}"
        before = sorted(p.name for p in (root / ".doctrine-state" / "checkpoints").glob("*.json"))
        second = proposal(root, 1, session="session-B")
        g, py = write_go(root, second), write_py(root, second)
        after = sorted(p.name for p in (root / ".doctrine-state" / "checkpoints").glob("*.json"))
        both_refused = g.returncode != 0 and py.returncode != 0
        return (both_refused and before == after,
                f"go={g.returncode} py={py.returncode} chain_unchanged={before == after}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    print(f"{'sequence':<30} {'ok':<5} detail")
    print("-" * 92)
    passed = total = 0
    for name, writers in SEQUENCES.items():
        ok, detail = run_sequence(name, writers)
        passed += ok
        total += 1
        print(f"{name:<30} {'yes' if ok else 'NO':<5} {detail}")

    print()
    print("fail-closed on poisoned input (both must refuse, nothing written)")
    print("-" * 92)
    REFUSALS = {
        "AWS key in a claim":   {"secret": "key = AKIA" + "IOSFODNN7EXAMPLE"},
        "token assignment":     {"secret": "api_key: hunter2hunter2"},
        "HTML comment escape":  {"marker": "note --> out of the block"},
        "state marker token":   {"marker": "doctrine:state:begin here"},
    }
    for label, kwargs in REFUSALS.items():
        ok, detail = run_refusal(label, kwargs)
        passed += ok
        total += 1
        print(f"{label:<30} {'yes' if ok else 'NO':<5} {detail}")

    ok, detail = run_lease_refusal()
    passed += ok
    total += 1
    print(f"{'second session refused':<30} {'yes' if ok else 'NO':<5} {detail}")

    print("-" * 92)
    print(f"interop {passed}/{total}")

"""Differential oracle for the GOLD LADDER's topology and content-pinning rules.

The gold chain decides which builds are promotable and on what evidence, so
its refusals are the product. This repo has no gold records to mutate, so every
chain below is SYNTHESISED - which is the only way to reach the topologies that
matter (fork, dangling link, two roots, an island) without waiting for one to
occur naturally.

Each case builds a chain, runs both implementations, and compares the message,
not just pass/fail. Two tools that refuse the same ladder while describing it
differently teach a reader to trust neither.
"""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


import _locate

REPO = _locate.reference_tools()      # doctrine checkout (also puts tools/ on path)
GO = _locate.require_binary()
import doctrine_gold as G  # noqa: E402 - needs _locate's sys.path first


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rec_bytes(tag, prev):
    """A gold record's bytes. prev=None means genesis."""
    return (json.dumps({"tag": tag, "prev_gold_sha256": prev},
                       ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


class Raw:
    """Write these exact bytes as the record, bypassing the record builder.

    Needed because a case labelled "non-object record" was, on inspection, a
    perfectly ordinary object carrying a bogus prev - a third copy of the
    dangling-link case wearing a different name. Reaching the non-object and
    unparseable branches means writing the file directly.
    """

    def __init__(self, data):
        self.data = data


def build(chain):
    """Write a chain into a fresh repo. `chain` is a list of (name, prev_spec).

    prev_spec is None for genesis, an int index of a previously written record,
    a Raw(bytes) to write verbatim, or a literal string used as prev (for
    dangling links).
    """
    d = Path(tempfile.mkdtemp())
    (d / ".Doctrine.md").write_text("# law\n", encoding="utf-8")
    gold = d / "docs" / "releases" / "gold"
    gold.mkdir(parents=True)
    written = []
    for name, prev_spec in chain:
        if isinstance(prev_spec, Raw):
            blob = prev_spec.data
        else:
            if prev_spec is None:
                prev = None
            elif isinstance(prev_spec, int):
                prev = written[prev_spec]
            else:
                prev = prev_spec
            blob = rec_bytes(name.removesuffix(".json"), prev)
        (gold / name).write_bytes(blob)
        written.append(sha(blob))
    return d


def norm(s):
    """Normalise a verdict for comparison.

    Two things are deliberately relaxed, and ONLY these two:

    * the parenthetical detail of a parse error - "Expecting property name
      enclosed in double quotes: line 1 column 2" is CPython's json module
      describing its own failure, and no Go port can reproduce that wording.
      What must match is the CLASSIFICATION ("unparseable") and WHICH FILE.
    * absolute temp paths, which differ per run and, on Windows, between the
      long and 8.3 spellings of the same directory depending on which process
      resolved it.

    Everything else is compared verbatim. Relaxing more than this would let a
    real divergence hide inside the normalisation, which is how an oracle
    quietly stops being one.
    """
    # Greedy to the final ")": CPython nests parens inside its own parse
    # message ("... line 1 column 2 (char 1))"), which a non-nesting pattern
    # silently fails to strip - leaving the case reported as a mismatch it
    # is not.
    s = re.sub(r" \(.*\)$", "", s)
    return re.sub(r"[A-Za-z]:\\[^\s:]*[\\/]", "<path>/", s)


def run_python(root):
    try:
        return "OK:" + ",".join(p.name for p in G.load_chain(root))
    except Exception as exc:
        return f"ERR:{exc}"


def run_go(root):
    p = subprocess.run([str(GO), "gold-chain"], cwd=str(root),
                       capture_output=True, text=True, timeout=300)
    out = (p.stdout + p.stderr).strip()
    if p.returncode == 0:
        names = [ln.strip() for ln in out.splitlines() if ln.strip()
                 and ln.strip() != "no gold records"]
        return "OK:" + ",".join(names)
    return "ERR:" + out.replace("error: ", "", 1).strip()


CASES = [
    ("empty gold dir",            []),
    ("single genesis",            [("v1.0.0.json", None)]),
    ("linear chain of three",     [("v1.0.0.json", None), ("v1.1.0.json", 0),
                                   ("v1.2.0.json", 1)]),
    # --- the topologies that must be REFUSED --------------------------------
    ("two genesis records",       [("v1.0.0.json", None), ("v2.0.0.json", None)]),
    ("no genesis (all linked)",   [("v1.0.0.json", "a" * 64), ("v1.1.0.json", "b" * 64)]),
    ("dangling prev",             [("v1.0.0.json", None), ("v1.1.0.json", "f" * 64)]),
    ("fork: two claim one parent", [("v1.0.0.json", None), ("v1.1.0.json", 0),
                                    ("v1.2.0.json", 0)]),
    ("prev is not a hash",        [("v1.0.0.json", None), ("bad.json", "NOT-A-HASH")]),
    # --- malformed records, which reach different branches entirely ---------
    ("non-object record (array)", [("v1.0.0.json", None),
                                   ("bad.json", Raw(b"[1, 2, 3]\n"))]),
    ("unparseable JSON",          [("v1.0.0.json", None),
                                   ("bad.json", Raw(b"{not json\n"))]),
    ("oversized record",          [("v1.0.0.json", None),
                                   ("big.json", Raw(b'{"x":"' + b"a" * 6_000_000 + b'"}'))]),
]

# The "unreachable from genesis" branch is NOT covered, and deliberately so.
#
# An earlier case here was labelled "island unreachable" and proved nothing:
# the dangling-prev check fires first, so it was a duplicate of case 6 wearing
# a different name. Reaching the reachability branch requires every prev to
# resolve, exactly one genesis, and no forks - which makes the graph a set of
# disjoint paths where the only unreachable shape is a CYCLE among non-genesis
# records. A cycle needs record A to contain the hash of B while B contains the
# hash of A, so constructing one means inverting SHA-256.
#
# That branch is therefore defensive, not reachable by construction. Saying so
# is better than a case that dresses up a different error as coverage.


def run_go_pin(root, rel):
    p = subprocess.run([str(GO), "gold-pin", rel], cwd=str(root),
                       capture_output=True, text=True, timeout=300)
    if p.returncode == 0:
        return "OK:" + json.loads(p.stdout)["sha256"][:12]
    return "ERR:" + (p.stdout + p.stderr).strip().replace("error: ", "", 1).strip()


def run_python_pin(root, rel):
    try:
        return "OK:" + G.hashed_ref(root, rel, "sign-off")["sha256"][:12]
    except Exception as exc:
        return f"ERR:{exc}"


if __name__ == "__main__":
    print(f"{'case':<34} {'agree':<6} verdict")
    print("-" * 96)
    agree = 0
    rows = []
    for label, chain in CASES:
        root = build(chain)
        pv, gv = run_python(root), run_go(root)
        same = norm(pv) == norm(gv)
        agree += same
        rows.append((label, pv, gv, same))
        print(f"{label:<34} {'yes' if same else 'NO':<6} {pv[:52]}")
        shutil.rmtree(root, ignore_errors=True)

    # --- content pinning: existence is not evidence -------------------------
    print()
    print("hashed_ref (content pinning)")
    print("-" * 96)
    pin_cases = [
        ("real content",      b"security sign-off: approved\n", "signoff.md"),
        ("EMPTY file",        b"",                              "signoff.md"),
        ("whitespace only",   b"   \n\t\n",                     "signoff.md"),
        ("escapes repo root", b"x",                             "../outside.md"),
        ("absent",            None,                             "missing.md"),
    ]
    pin_agree = 0
    for label, content, rel in pin_cases:
        d = Path(tempfile.mkdtemp())
        (d / ".Doctrine.md").write_text("# law\n", encoding="utf-8")
        if content is not None and not rel.startswith(".."):
            (d / rel).write_bytes(content)
        if rel.startswith(".."):
            (d.parent / "outside.md").write_bytes(b"x")
        pv, gv = run_python_pin(d, rel), run_go_pin(d, rel)
        same = pv == gv
        pin_agree += same
        rows.append((f"hashed_ref: {label}", pv, gv, same))
        print(f"{'hashed_ref: ' + label:<34} {'yes' if same else 'NO':<6} {pv[:52]}")
        shutil.rmtree(d, ignore_errors=True)

    print("-" * 96)
    chain_agree = sum(1 for r in rows[:len(CASES)] if r[3])
    print(f"chain topology agree {chain_agree}/{len(CASES)}   "
          f"content pinning agree {pin_agree}/{len(pin_cases)}")
    for label, pv, gv, same in rows:
        if not same:
            print(f"\n--- MISMATCH {label} ---\n  python: {pv}\n  go    : {gv}")

"""Differential oracle for chain verification, under TAMPERING.

Both implementations agreeing that a healthy 31-checkpoint chain is intact
proves very little - two functions that always return OK would agree too. A
verifier earns trust by what it REFUSES, so every case below is a real
mutation of a real chain, and the two implementations must reach the same
verdict on each.

Each case copies this repo's genuine .doctrine-state/ into a temp repo,
mutates it one way, and runs both verifiers.

Cases 10-12 exist because cases 1-9 all broke a HASH. Go had no schema check
at all, and a hash break alone is enough to refuse - so the two agreed for the
wrong reason, and 9/9 looked like proof when it was coincidence. A record that
is structurally invalid while every hash still agrees is the only case that
isolates the schema rule, so it is now tested directly, and against a binary
built WITHOUT the rule to confirm the case can actually fail.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Repo root derived from this file's own location, never hardcoded: an
# oracle that only runs on the machine that wrote it verifies nothing for
# anyone else.
REPO = Path(__file__).resolve().parents[2]
EXE = ".exe" if os.name == "nt" else ""
GO = REPO / "doctrineos" / ("dos" + EXE)
PY = REPO / "tools" / "doctrine_state.py"
CP_RE = re.compile(r"^(\d+)-[0-9a-f]{12}\.json$")

# Optional control: a Go binary built WITHOUT the schema rule. When present,
# the schema-only cases must come back OK from it, proving they are genuine
# regression tests rather than cases that pass no matter what.
CONTROL = REPO / "doctrineos" / ("preschema" + EXE)


def fresh():
    """A temp repo carrying a real copy of the state plane."""
    d = Path(tempfile.mkdtemp())
    (d / ".Doctrine.md").write_text("# law\n", encoding="utf-8")
    shutil.copytree(REPO / ".doctrine-state", d / ".doctrine-state")
    # Python validates each checkpoint against a JSON Schema and refuses
    # to run without it. Omitting this made every case report "schema not
    # found" instead of a verdict - a harness bug, not a port defect.
    shutil.copytree(REPO / ".Doctrine" / "state-plane",
                    d / ".Doctrine" / "state-plane")
    return d


def checkpoints(root):
    cps = sorted((root / ".doctrine-state" / "checkpoints").glob("*.json"),
                 key=lambda p: int(p.name.split("-", 1)[0]))
    return [p for p in cps if CP_RE.match(p.name)]


def run(cmd, root):
    p = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=300)
    out = (p.stdout + p.stderr).strip()
    if "VERIFY FAILED" in out or "FAILED" in out:
        return "FAIL", out
    if "verify OK" in out:
        return "OK", out
    if "nothing to verify" in out:
        return "EMPTY", out
    return "?", out[:120]


def findings_of(out):
    """The individual findings, not just the pass/fail verdict.

    Comparing verdicts alone is too weak, and this harness proved it: with seq
    as a string both implementations said FAIL, so the oracle reported perfect
    agreement while Go was printing `seq 0` for a checkpoint whose seq was
    `30`. The verdict was right and the explanation was wrong, which sends a
    reader after a defect that is not there. Findings are compared as an
    ordered list because their order is part of the ported contract.
    """
    return [ln.strip()[2:].strip() for ln in out.splitlines()
            if ln.strip().startswith("- ")]


def write_canonical(path, obj):
    """Write canonical bytes, defeating Windows newline translation.

    Path.write_text opens in TEXT mode, so every LF becomes CRLF on this
    platform. That is invisible in a diff and turns a surgical mutation into a
    blunt one: cases meant to leave the bytes canonical were also tripping the
    canonical-bytes check, so each proved less than its label claimed. Writing
    bytes is the only way to mean exactly what these mutations say.
    """
    blob = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_bytes(blob.encode("utf-8"))


# --- mutations, each returning a label -------------------------------------
def untouched(root):
    return "healthy chain (control)"


def edit_middle(root):
    cps = checkpoints(root)
    t = cps[len(cps) // 2]
    d = json.loads(t.read_text("utf-8"))
    d["worktree"] = "TAMPERED"
    write_canonical(t, d)
    return f"edited {t.name} (content changed, still canonical)"


def break_canonical(root):
    cps = checkpoints(root)
    t = cps[len(cps) // 2]
    t.write_bytes(t.read_bytes() + b"\n")  # one extra byte, nothing else
    return f"{t.name} no longer canonical bytes"


def delete_middle(root):
    cps = checkpoints(root)
    t = cps[len(cps) // 2]
    t.unlink()
    return f"deleted {t.name} (seq gap)"


def fork_chain(root):
    cps = checkpoints(root)
    t = cps[len(cps) // 2]
    dup = t.with_name(t.name.split("-", 1)[0] + "-ffffffffffff.json")
    shutil.copy(t, dup)
    return f"duplicate seq -> fork ({dup.name})"


def stray_file(root):
    (root / ".doctrine-state" / "checkpoints" / "notes.txt").write_text("x", encoding="utf-8")
    return "stray file in checkpoints/"


def head_mismatch(root):
    head = root / ".doctrine-state" / "checkpoint.json"
    d = json.loads(head.read_text("utf-8"))
    d["worktree"] = "DIFFERENT"
    write_canonical(head, d)
    return "checkpoint.json != latest history copy"


def decisions_desync(root):
    dec = root / ".doctrine-state" / "decisions" / "DECISIONS.ndjson"
    if not dec.exists():
        dec.parent.mkdir(parents=True, exist_ok=True)
    dec.write_text('{"forged":"entry"}\n', encoding="utf-8")
    return "decisions ledger hash desync"


def wipe_history(root):
    shutil.rmtree(root / ".doctrine-state" / "checkpoints")
    return "history wiped, checkpoint.json remains"


def _rewrite_tail_and_head(root, mutate):
    """Mutate the TAIL checkpoint and checkpoint.json identically, canonically.

    Mutating the TAIL is what makes these cases hash-clean: nothing links
    forward from it, so no prev_sha256 breaks; head and tail are rewritten
    together, so they still match; state_index is untouched; and the bytes are
    re-canonicalised. Every hash check therefore passes, and the ONLY thing
    left that can refuse the record is the schema.
    """
    tail = checkpoints(root)[-1]
    d = json.loads(tail.read_text("utf-8"))
    mutate(d)
    write_canonical(tail, d)
    write_canonical(root / ".doctrine-state" / "checkpoint.json", d)
    return tail


def unknown_field(root):
    _rewrite_tail_and_head(root, lambda d: d.__setitem__("forged", True))
    return "SCHEMA-ONLY: unknown field, hashes intact"


def drop_required(root):
    _rewrite_tail_and_head(root, lambda d: d.pop("worktree", None))
    return "SCHEMA-ONLY: required field dropped, hashes intact"


def wrong_type(root):
    """Type confusion on a field NOTHING else inspects.

    The first version of this case retyped `seq`, and the control caught the
    mistake: the pre-schema binary refused it too, because the seq check reads
    that field independently. So the case was passing without the schema rule
    and proved nothing about it, despite being labelled SCHEMA-ONLY.

    The verify logic only ever reads seq, prev_sha256, state_index and the raw
    bytes. session_id is inert to all of them, so retyping it is refused by the
    schema or by nothing at all.
    """
    _rewrite_tail_and_head(root, lambda d: d.__setitem__("session_id", 12345))
    return "SCHEMA-ONLY: session_id as integer, hashes intact"


def seq_type_confusion(root):
    """Not schema-only - the seq check catches this too, and deliberately so.

    Kept because it is what exposed a real port divergence: with seq as a
    string, Go's float64 type assertion failed to zero and reported
    `seq 0 != expected 30` where Python reported `seq 30 != expected 30`. Both
    refused the record, so verdict-level agreement hid it. A message that
    points at a wrong number sends the reader after the wrong defect.
    """
    _rewrite_tail_and_head(root, lambda d: d.__setitem__("seq", str(d["seq"])))
    return "seq as string (schema AND seq check; message parity)"


MUTATIONS = [untouched, edit_middle, break_canonical, delete_middle,
             fork_chain, stray_file, head_mismatch, decisions_desync, wipe_history,
             unknown_field, drop_required, wrong_type, seq_type_confusion]

SCHEMA_ONLY = {"unknown_field", "drop_required", "wrong_type"}

if __name__ == "__main__":
    has_control = CONTROL.exists()
    hdr = f"{'mutation':<50} {'Python':<8} {'Go':<8}"
    if has_control:
        hdr += " pre-schema"
    print(hdr)
    print("-" * (len(hdr) + 2))

    agree = 0
    text_agree = 0
    mismatches = []
    text_mismatches = []
    control_notes = []
    for mut in MUTATIONS:
        root = fresh()
        label = mut(root)
        pv, pout = run([sys.executable, str(PY), "verify"], root)
        gv, gout = run([str(GO), "verify"], root)
        same = pv == gv
        agree += same
        if not same:
            mismatches.append((label, pout, gout))

        pf, gf = findings_of(pout), findings_of(gout)
        if pf == gf:
            text_agree += 1
        else:
            text_mismatches.append((label, pf, gf))

        line = f"{label:<50} {pv:<8} {gv:<8}"
        if has_control:
            cv, _ = run([str(CONTROL), "verify"], root)
            line += f" {cv}"
            # A schema-only case is only a real test if the pre-schema binary
            # WAVES IT THROUGH. If it fails there too, something else is
            # catching the mutation and the case proves nothing about schema.
            if mut.__name__ in SCHEMA_ONLY and cv != "OK":
                control_notes.append(
                    f"{label}: pre-schema binary said {cv}, expected OK - "
                    f"case is not isolating the schema rule")
        print(line + ("" if same else "   <-- MISMATCH"))
        shutil.rmtree(root, ignore_errors=True)

    print("-" * (len(hdr) + 2))
    print(f"verdicts agree {agree}/{len(MUTATIONS)}   "
          f"findings text identical {text_agree}/{len(MUTATIONS)}")
    for label, pout, gout in mismatches:
        print(f"\n--- VERDICT {label} ---\n  python: {pout[:300]}\n  go    : {gout[:300]}")
    for label, pf, gf in text_mismatches:
        print(f"\n--- FINDINGS DIFFER: {label} ---")
        for a, b in zip(pf + [""] * len(gf), gf + [""] * len(pf)):
            if a != b:
                print(f"    python: {a}\n    go    : {b}")
    if has_control:
        if control_notes:
            print("\nCONTROL PROBLEMS:")
            for n in control_notes:
                print("  -", n)
        else:
            print("control: pre-schema binary passed all 3 schema-only cases, "
                  "so they genuinely exercise the new rule")
    else:
        print(f"control: {CONTROL.name} absent - schema-only cases unproven as "
              f"regression tests")

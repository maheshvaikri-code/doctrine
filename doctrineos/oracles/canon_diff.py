"""Differential oracle for CANONICAL BYTES - the encoding the hash chain
depends on.

Why byte-for-byte and not "looks the same": every chain hash is taken over
this encoding. One escaped character, one key out of order, one missing
newline, and every hash diverges - at which point `verify` reports a broken
chain and the failure is INDISTINGUISHABLE FROM TAMPERING. A checksum that
cries wolf gets switched off, and then nothing is checked at all.

So the cases below are chosen to be exactly where two JSON encoders are most
likely to disagree, not where they are most likely to agree.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Repo root derived from this file's own location, never hardcoded: an
# oracle that only runs on the machine that wrote it verifies nothing for
# anyone else.
REPO = Path(__file__).resolve().parents[2]
EXE = ".exe" if os.name == "nt" else ""
GO = REPO / "doctrineos" / ("dos" + EXE)

sys.path.insert(0, str(REPO / "tools"))
import doctrine_state as ds  # the reference implementation

CASES = {
    "flat object":          {"b": 2, "a": 1},
    "key order":            {"z": 1, "m": 2, "a": 3},
    "nested":               {"outer": {"inner": {"deep": [1, 2, 3]}}},
    "empty containers":     {"list": [], "obj": {}, "s": ""},
    "null and bools":       {"n": None, "t": True, "f": False},
    # --- where encoders actually diverge ---
    "HTML chars":           {"note": "a < b && c > d"},          # Go escapes these by default
    "ampersand in url":     {"url": "https://x.io/a?b=1&c=2"},
    "unicode":              {"note": "caf\u00e9 \u2014 na\u00efve \u4e2d\u6587"},
    "emoji":                {"note": "shipped \U0001F680"},
    "quotes and escapes":   {"s": "he said \"hi\"\tand\\left\nnewline"},
    "slash":                {"path": "a/b/c"},
    "integers":             {"small": 1, "big": 9007199254740991, "zero": 0, "neg": -42},
    "float":                {"f": 1.5},
    "deep array of objects": {"xs": [{"b": 1, "a": 2}, {"d": 3, "c": 4}]},
    # a realistic checkpoint shape
    "checkpoint-like": {
        "checkpoint_version": "1", "seq": 30,
        "at_commit": "be4f434219ef65c155e97cb662b88b76427eaeea",
        "created_at": "2026-08-04T22:03:40Z",
        "prev_sha256": "9f2c" * 16,
        "session_id": "s-2026-08-04-enterprise-control-plane-r5",
        "worktree": "clean",
        "control": {"role": "project-reviewer", "phase": "verification-arc-closed",
                    "brevity_mode": "full", "gates_passed": ["G0", "G1", "G2"],
                    "active_intents": []},
        "state_index": {"distillates/30-63af9e8ab9b3.json": "abc123"},
    },
}

print(f"{'case':<24} {'bytes':<7} {'sha256 match':<13}")
print("-" * 50)
ok = 0
bad = []
for name, obj in CASES.items():
    py_bytes = ds.canonical_bytes(obj)
    p = subprocess.run([str(GO), "canon"], input=json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       capture_output=True, text=False, timeout=120)
    go_bytes = p.stdout
    same = (py_bytes == go_bytes)
    ok += same
    if not same:
        bad.append((name, py_bytes, go_bytes))
    print(f"{name:<24} {'SAME' if same else 'DIFFER':<7} "
          f"{ds.sha256_bytes(py_bytes)[:12] == ds.sha256_bytes(go_bytes)[:12]}")

print("-" * 50)
print(f"identical {ok}/{len(CASES)}")
for name, pb, gb in bad:
    print(f"\n--- {name} ---")
    print("  python:", pb.decode("utf-8", "replace")[:220].replace("\n", "\\n"))
    print("  go    :", gb.decode("utf-8", "replace")[:220].replace("\n", "\\n"))

"""Differential oracle: the Go guard vs v1's Python guard, same payloads.

This is the mechanism that makes a rewrite safe. The Python guard survived
four rounds of adversarial security review; that hardening lives in its rule
sets, not in anyone's memory. Porting it by reading the code and trusting the
result is exactly how hard-won coverage disappears silently.

So: run both implementations across the input space and DIFF THE DECISIONS.
A divergence is not automatically a bug in the port - it may be a deliberate
scope change (v1 guarded Bash; DoctrineOS does not). But every divergence
must be NAMED here, not discovered later by a user.

Every credential-shaped fixture is ASSEMBLED at runtime. Two earlier drafts
of this file were refused by the v1 guard - once for a private-key marker,
once for a quoted PASSWORD assignment. Both refusals were correct.
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
PY = REPO / "tools" / "doctrine_guard.py"

AWS = "AKIA" + "IOSFODNN7EXAMPLE"
GH = "ghp_" + "a" * 36
ANT = "sk-ant-" + "b" * 24
SLACK = "xoxb-" + "1234567890-abcdef"
GOOG = "AIza" + "C" * 35
PRIV = "-----BEGIN " + "RSA PRIVATE" + " KEY-----"
# the backreference-rule fixtures, never literal in this file
QUOTED = "PASS" + "WORD = " + '"' + ("hunter2-" * 3) + '"'
BARE = "DATABASE_" + "PASS" + "WORD=" + "sup3rs3cretvalue123"

CASES = [
    ("ordinary file",             "src/app.py",                            "print(1)"),
    ("empty content",             "src/empty.py",                          ""),
    ("aws key",                   "src/cfg.py",                            f'K="{AWS}"'),
    ("github token",              "src/cfg.py",                            f'T="{GH}"'),
    ("anthropic key",             "src/cfg.py",                            f'A="{ANT}"'),
    ("slack token",               "src/cfg.py",                            f'S="{SLACK}"'),
    ("google key",                "src/cfg.py",                            f'G="{GOOG}"'),
    ("private key block",         "src/id_rsa",                            PRIV),
    ("gold record",               "docs/releases/gold/v1.0.0.json",        "{}"),
    ("gold dir itself",           "docs/releases/gold",                    "{}"),
    ("state checkpoint",          ".doctrine-state/checkpoint.json",       "{}"),
    ("state checkpoints/",        ".doctrine-state/checkpoints/0001.json", "{}"),
    ("dotenv",                    ".env",                                  "X=1"),
    ("dotenv variant",            ".env.production",                       "X=1"),
    ("nested dotenv",             "services/api/.env",                     "X=1"),
    ("dotenv EXAMPLE (exempt)",   ".env.example",                          "API_KEY="),
    ("git internals",             ".git/config",                           "[core]"),
    ("absolute path form",        str(REPO / "src/abs.py"),                "x=1"),
    ("traversal attempt",         "src/../docs/releases/gold/v2.json",     "{}"),
    ("unicode path",              "src/\u00e9\u00e0\u00fc.py",             "x=1"),
    ("prose about secrets",       "docs/security.md",                      "Never commit an API key or token."),
    ("placeholder value",         "docs/.env.example",                     "API_KEY=<your-key-here>"),
    # THE KNOWN HAZARD: v1 uses a matched-quote BACKREFERENCE for this rule.
    # Go's RE2 has no backreferences, so it is not ported yet. A divergence
    # here is the finding, surfaced on purpose rather than shipped unnoticed.
    ("quoted secret assignment",  "src/settings.py",                       QUOTED),
    ("bare secret assignment",    "src/settings.py",                       BARE),
]


def decide(cmd, path, content):
    payload = json.dumps({
        "session_id": "diff", "cwd": str(REPO), "tool_name": "Write",
        "tool_input": {"file_path": path, "content": content},
    })
    try:
        p = subprocess.run(cmd, input=payload, capture_output=True,
                           text=True, cwd=str(REPO), timeout=180)
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    out = p.stdout.strip()
    if not out:
        return "silent"
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    except Exception:
        return "UNPARSEABLE"


print(f"{'case':<28} {'Go':<9} {'Python':<9}")
print("-" * 54)
agree = 0
divergences = []
for name, path, content in CASES:
    g = decide([str(GO), "check"], path, content)
    p = decide([sys.executable, str(PY)], path, content)
    same = (g == p)
    agree += same
    if not same:
        divergences.append((name, g, p))
    print(f"{name:<28} {g:<9} {p:<9} {'' if same else '<-- DIVERGE'}")

print("-" * 54)
print(f"agree {agree}/{len(CASES)}   diverge {len(divergences)}")
if divergences:
    print("\nDIVERGENCES - each must be explained, not discovered later:")
    for n, g, p in divergences:
        print(f"  {n}: Go={g}  Python={p}")

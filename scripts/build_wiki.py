#!/usr/bin/env python3
"""Build the Engineering Doctrine wiki from the DESIGNATED SOURCE (.Doctrine/
roles + skills), one-way, with fail-closed gates -- an instance of
`skills/web-publishing.md` applied to this repo itself.

Called by `.github/workflows/wiki.yml` on push (opt-in), and runnable locally to
produce a pushable bundle:

    python scripts/build_wiki.py <out_dir>

Discipline (from the skill): publishes a DESIGNATED SOURCE only (never the whole
repo); the secret-scan looks for credential PATTERNS, not the word "secret"
(which the doctrine's prose uses constantly, so scanning the word would
false-block its own security playbook); exits non-zero if the gate blocks, so a
broken or leaky build is never published. ASCII-only output (Windows cp1252).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private-key"),
    (r"AKIA[0-9A-Z]{16}", "aws-access-key"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "github-token"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "slack-token"),
]


def build(src: Path, out: Path) -> list[str]:
    """One-way: (re)build the wiki so it mirrors the source. Returns page names."""
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.md"):
        stale.unlink()
    roles = sorted((src / ".Doctrine" / "roles").glob("*.md"))
    skills = sorted((src / ".Doctrine" / "skills").glob("*.md"))
    pages: list[str] = []
    for f in roles:
        (out / f"role-{f.stem}.md").write_text(f.read_text("utf-8"), "utf-8")
        pages.append(f"role-{f.stem}.md")
    for f in skills:
        (out / f"skill-{f.stem}.md").write_text(f.read_text("utf-8"), "utf-8")
        pages.append(f"skill-{f.stem}.md")
    home = ["# Engineering Doctrine -- Wiki\n\n",
            "One-way auto-sync from `.Doctrine/` in the source repo. "
            "Edit the source, not here.\n\n", "## Roles\n"]
    home += [f"- [[role-{f.stem}]]\n" for f in roles]
    home += ["\n## Skills\n"] + [f"- [[skill-{f.stem}]]\n" for f in skills]
    (out / "Home.md").write_text("".join(home), "utf-8")
    (out / "_Sidebar.md").write_text("## Doctrine\n[[Home]]\n", "utf-8")
    return pages + ["Home.md", "_Sidebar.md"]


def gate(out: Path) -> list[str]:
    """Fail-closed checks. Returns blocking findings (empty list = PASS)."""
    findings: list[str] = []
    md = list(out.glob("*.md"))
    names = {p.stem for p in md}
    for p in md:
        text = p.read_text("utf-8")
        if not text.strip():
            findings.append(f"empty page: {p.name}")
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, text):
                findings.append(f"secret ({label}) in {p.name}")
        for link in re.findall(r"\[\[([^\]]+)\]\]", text):
            if link not in names:
                findings.append(f"broken [[link]] '{link}' in {p.name}")
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: build_wiki.py <out_dir>", file=sys.stderr)
        return 2
    src = Path(__file__).resolve().parents[1]  # repo root
    out = Path(argv[0])
    pages = build(src, out)
    findings = gate(out)
    print(f"built: {len(pages)} pages (designated source: .Doctrine/ roles + skills)")
    if findings:
        print(f"FAIL-CLOSED GATE: BLOCK -- {len(findings)} finding(s), not publishing")
        for f in findings[:20]:
            print(f"  - {f}")
        return 1
    print("FAIL-CLOSED GATE: PASS -- safe to publish")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

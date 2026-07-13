#!/usr/bin/env python3
"""doctrine_lint — CI gate for the Doctrine corpus itself.

Checks (all mechanical, all cheap):
  1. Every backtick path reference under .Doctrine/ resolves on disk.
  2. Role cards: frontmatter name+description, a **Mission.** line.
  3. Skills: '# Skill:' heading OR frontmatter name (integration shims).
  4. Every .claude/agents/<n>.md has a matching .Doctrine/roles/<n>.md.
  5. Numeric claims match reality (role cards, playbooks, subagents).
  6. .Doctrine.md header version == newest CHANGELOG release.
  7. Templates carry their gate tag comment (<!-- G<n> artifact ... -->).
  8. state-plane examples validate against their schemas AND are
     byte-canonical per the pack-wide canonicalization rules.

Exit 0 clean; exit 1 with findings listed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from doctrine_state import SchemaError, canonical_bytes, validate  # noqa: E402

# References that intentionally point outside this repo (upstream docs).
ALLOWED_EXTERNAL = {
    "skills/ponytail/SKILL.md",  # upstream ponytail repo path
}

REF_RE = re.compile(
    r"`((?:skills|standards|roles|templates|rubrics|schemas|examples|"
    r"integrations|state-plane|adapters|languages)/[A-Za-z0-9._/-]+)`")


def check_references(root: Path, findings: list[str]) -> None:
    doctrine = root / ".Doctrine"
    scan = [root / ".Doctrine.md", *doctrine.rglob("*.md"),
            *(root / ".claude" / "agents").glob("*.md")]
    for f in scan:
        text = f.read_text("utf-8")
        for ref in set(REF_RE.findall(text)):
            if "<" in ref or ref in ALLOWED_EXTERNAL:
                continue
            if not ((doctrine / ref).exists()
                    or (doctrine / "standards" / ref).exists()):
                findings.append(f"{f.relative_to(root)}: broken reference "
                                f"`{ref}`")


def check_roles(root: Path, findings: list[str]) -> None:
    for f in sorted((root / ".Doctrine" / "roles").glob("*.md")):
        text = f.read_text("utf-8")
        if not text.startswith("---"):
            findings.append(f"{f.name}: missing YAML frontmatter")
            continue
        front = text.split("---", 2)[1]
        for key in ("name:", "description:"):
            if key not in front:
                findings.append(f"{f.name}: frontmatter missing '{key}'")
        if "**Mission.**" not in text:
            findings.append(f"{f.name}: no **Mission.** line")


def check_skills(root: Path, findings: list[str]) -> None:
    for f in sorted((root / ".Doctrine" / "skills").glob("*.md")):
        text = f.read_text("utf-8")
        if not (text.startswith("# Skill:")
                or (text.startswith("---") and "name:" in
                    text.split("---", 2)[1])):
            findings.append(f"{f.name}: neither '# Skill:' heading nor "
                            "frontmatter name")


def check_agents(root: Path, findings: list[str]) -> None:
    roles = {p.stem for p in (root / ".Doctrine" / "roles").glob("*.md")}
    for f in sorted((root / ".claude" / "agents").glob("*.md")):
        if f.stem not in roles:
            findings.append(f".claude/agents/{f.name}: no matching role "
                            f"card .Doctrine/roles/{f.stem}.md")


def check_counts(root: Path, findings: list[str]) -> None:
    actual = {
        "role cards": len(list((root / ".Doctrine" / "roles").glob("*.md"))),
        "discipline playbooks":
            len(list((root / ".Doctrine" / "skills").glob("*.md"))),
        "ready subagents":
            len(list((root / ".claude" / "agents").glob("*.md"))),
    }
    for f in (root / ".Doctrine" / "README.md", root / ".Doctrine.md"):
        text = f.read_text("utf-8")
        for label, real in actual.items():
            for claim in re.findall(rf"(\d+) {re.escape(label)}", text):
                if int(claim) != real:
                    findings.append(f"{f.name}: claims {claim} {label}, "
                                    f"filesystem has {real}")


def check_version(root: Path, findings: list[str]) -> None:
    head = (root / ".Doctrine.md").read_text("utf-8").splitlines()[0]
    m_doc = re.search(r"v(\d+\.\d+\.\d+)", head)
    m_log = re.search(r"^## \[(\d+\.\d+\.\d+)\]",
                      (root / "CHANGELOG.md").read_text("utf-8"),
                      re.MULTILINE)
    if not m_doc or not m_log:
        findings.append("version: header or CHANGELOG release not found")
    elif m_doc.group(1) != m_log.group(1):
        findings.append(f"version desync: .Doctrine.md v{m_doc.group(1)} "
                        f"!= CHANGELOG {m_log.group(1)}")


def check_templates(root: Path, findings: list[str]) -> None:
    for f in sorted((root / ".Doctrine" / "templates").glob("*.md")):
        if not re.search(r"<!-- G\d ", f.read_text("utf-8")):
            findings.append(f"templates/{f.name}: no gate tag comment")


def check_plugin_parity(root: Path, findings: list[str]) -> None:
    """The Claude Code plugin ships byte-copies of the repo wiring; two
    synced copies are a drift hazard, so parity is a hard gate."""
    pairs = [(root / ".claude" / "agents", root / "plugin" / "agents"),
             (root / ".claude" / "commands" / "checkpoint.md",
              root / "plugin" / "commands" / "checkpoint.md")]
    for canonical, copy in pairs:
        if not copy.exists():
            findings.append(f"plugin parity: {copy.relative_to(root)} "
                            "missing")
            continue
        if canonical.is_dir():
            canon_files = {p.name: p for p in canonical.glob("*.md")}
            copy_files = {p.name: p for p in copy.glob("*.md")}
            for name in sorted(canon_files.keys() | copy_files.keys()):
                if name not in copy_files:
                    findings.append(f"plugin parity: agents/{name} "
                                    "missing from plugin")
                elif name not in canon_files:
                    findings.append(f"plugin parity: agents/{name} exists "
                                    "only in plugin")
                elif canon_files[name].read_bytes() != \
                        copy_files[name].read_bytes():
                    findings.append(f"plugin parity: agents/{name} "
                                    "drifted from .claude/agents")
        elif canonical.read_bytes() != copy.read_bytes():
            findings.append("plugin parity: plugin/commands/checkpoint.md "
                            "drifted from .claude/commands/checkpoint.md")
    for ref in ("plugin/.claude-plugin/plugin.json",
                ".claude-plugin/marketplace.json",
                "plugin/hooks/hooks.json", "plugin/.mcp.json"):
        p = root / ref
        if not p.exists():
            findings.append(f"plugin parity: {ref} missing")
            continue
        try:
            json.loads(p.read_text("utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(f"{ref}: invalid JSON ({exc})")


def check_state_plane(root: Path, findings: list[str]) -> None:
    plane = root / ".Doctrine" / "state-plane"
    for name in ("checkpoint", "distillate"):
        schema = json.loads(
            (plane / "schemas" / f"{name}.schema.json").read_text("utf-8"))
        example = plane / "examples" / f"{name}.example.json"
        raw = example.read_bytes()
        data = json.loads(raw.decode("utf-8"))
        try:
            validate(data, schema)
        except SchemaError as exc:
            findings.append(f"examples/{example.name}: schema: {exc}")
        if raw != canonical_bytes(data):
            findings.append(f"examples/{example.name}: not canonical bytes "
                            "(UTF-8/LF/sorted/no trailing ws/single \\n)")


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0]) if argv else Path.cwd()
    findings: list[str] = []
    for check in (check_references, check_roles, check_skills, check_agents,
                  check_counts, check_version, check_templates,
                  check_state_plane, check_plugin_parity):
        check(root, findings)
    if findings:
        print(f"doctrine_lint: {len(findings)} finding(s):")
        for msg in findings:
            print(f"  - {msg}")
        return 1
    print("doctrine_lint: corpus clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

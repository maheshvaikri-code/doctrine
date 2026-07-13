#!/usr/bin/env python3
"""doctrine_install — install the Doctrine System into any target repo.

Copies the committed law (.Doctrine.md + .Doctrine/), the enforcement
tools, the Claude Code wiring, and the adapter overlays for the tools you
name. Idempotent: unchanged files are skipped; files that exist with
DIFFERENT content are never silently clobbered (skipped with a warning
unless --force). An existing CLAUDE.md gets the import lines APPENDED,
never replaced; an existing AGENTS.md is left alone (use
`doctrine_state.py hydrate --emit-agents` for the state block).

Usage:
  python tools/doctrine_install.py --target ../my-repo --tool claude
  python tools/doctrine_install.py --target . --tool claude,cursor,codex
  python tools/doctrine_install.py --target ../svc --tool all --enterprise

Publishing/registry distribution stays human-gated (.Doctrine.md section 5).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# tool -> [(source under .Doctrine/adapters/, dest under target root)]
ADAPTERS: dict[str, list[tuple[str, str]]] = {
    "claude": [],  # native wiring copied separately (.claude/, CLAUDE.md)
    "codex": [],   # AGENTS.md is native; MCP registration is documented
    "cursor": [("cursor-doctrine.mdc", ".cursor/rules/doctrine.mdc")],
    "windsurf": [("windsurf-doctrine.md", ".windsurf/rules/doctrine.md")],
    "copilot": [("copilot-instructions.md",
                 ".github/copilot-instructions.md")],
    "gemini": [("GEMINI.md", "GEMINI.md")],
    "cline": [("cline-doctrine.md", ".clinerules/doctrine.md")],
    "roo": [("roo-doctrine.md", ".roo/rules/doctrine.md")],
    "amazonq": [("amazonq-doctrine.md", ".amazonq/rules/doctrine.md")],
    "continue": [("continue-doctrine.md", ".continue/rules/doctrine.md")],
    "junie": [("junie-doctrine.md", ".junie/guidelines.md")],
}
CLAUDE_IMPORTS = ["@.Doctrine.md",
                  "@.doctrine-state/local/hydration.bundle.md"]
TOOL_FILES = ["doctrine_state.py", "doctrine_lint.py", "doctrine_gold.py",
              "doctrine_mcp.py", "doctrine_install.py"]
GITIGNORE_LINES = [".doctrine-state/local/", "__pycache__/"]


class Report:
    def __init__(self) -> None:
        self.copied: list[str] = []
        self.skipped_same: int = 0
        self.skipped_diff: list[str] = []

    def show(self) -> None:
        print(f"installed: {len(self.copied)} file(s), "
              f"unchanged: {self.skipped_same}")
        if self.skipped_diff:
            print(f"SKIPPED {len(self.skipped_diff)} file(s) that exist "
                  "with different content (rerun with --force to "
                  "overwrite):")
            for rel in self.skipped_diff:
                print(f"  - {rel}")


def copy_file(src: Path, dest: Path, target: Path, report: Report,
              force: bool) -> None:
    data = src.read_bytes()
    if dest.exists():
        if dest.read_bytes() == data:
            report.skipped_same += 1
            return
        if not force:
            report.skipped_diff.append(dest.relative_to(target).as_posix())
            return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    report.copied.append(dest.relative_to(target).as_posix())


def copy_tree(src_dir: Path, dest_dir: Path, target: Path, report: Report,
              force: bool) -> None:
    for src in sorted(src_dir.rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts:
            continue
        copy_file(src, dest_dir / src.relative_to(src_dir), target,
                  report, force)


def append_lines(path: Path, lines: list[str], header: str | None,
                 report: Report, target: Path) -> None:
    """Append only the missing lines; never rewrite existing content."""
    existing = path.read_text("utf-8") if path.exists() else ""
    missing = [ln for ln in lines if ln not in existing.splitlines()]
    if not missing:
        report.skipped_same += 1
        return
    block = ("" if not existing else "\n") if existing.endswith("\n") or \
        not existing else "\n"
    text = existing + block
    if header and header not in existing:
        text += header + "\n"
    text += "\n".join(missing) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    report.copied.append(path.relative_to(target).as_posix())


def install(source: Path, target: Path, tools: list[str],
            enterprise: bool, ci: bool, force: bool) -> int:
    if not (source / ".Doctrine.md").exists():
        print(f"error: {source} is not a doctrine source tree "
              "(.Doctrine.md missing)", file=sys.stderr)
        return 2
    if source.resolve() == target.resolve():
        print("error: target is the source tree itself", file=sys.stderr)
        return 2
    unknown = [t for t in tools if t not in ADAPTERS and t != "all"]
    if unknown:
        print(f"error: unknown tool(s) {unknown}; choose from "
              f"{sorted(ADAPTERS)} or 'all'", file=sys.stderr)
        return 2
    if "all" in tools:
        tools = sorted(ADAPTERS)
    target.mkdir(parents=True, exist_ok=True)
    report = Report()

    # the law
    copy_file(source / ".Doctrine.md", target / ".Doctrine.md", target,
              report, force)
    copy_tree(source / ".Doctrine", target / ".Doctrine", target, report,
              force)
    # the enforcement suite + its tests
    for name in TOOL_FILES:
        copy_file(source / "tools" / name, target / "tools" / name,
                  target, report, force)
    for test in sorted((source / "tests").glob("test_doctrine_*.py")):
        copy_file(test, target / "tests" / test.name, target, report, force)
    if not (target / "Makefile").exists():
        copy_file(source / "Makefile", target / "Makefile", target,
                  report, force)
    if ci:
        copy_file(source / ".github" / "workflows" / "doctrine.yml",
                  target / ".github" / "workflows" / "doctrine.yml",
                  target, report, force)

    # AGENTS.md universal boot (never overwrite an existing one)
    agents = target / "AGENTS.md"
    if not agents.exists():
        copy_file(source / ".Doctrine" / "adapters" / "AGENTS.md", agents,
                  target, report, force)

    if "claude" in tools:
        copy_tree(source / ".claude", target / ".claude", target, report,
                  force)
        append_lines(target / "CLAUDE.md", CLAUDE_IMPORTS, None, report,
                     target)
    for tool in tools:
        for src_name, dest_rel in ADAPTERS[tool]:
            copy_file(source / ".Doctrine" / "adapters" / src_name,
                      target / dest_rel, target, report, force)

    append_lines(target / ".gitignore", GITIGNORE_LINES,
                 "# doctrine state plane (machine-local only)", report,
                 target)
    if enterprise:
        append_lines(target / "docs" / "brief.md",
                     ["Merge profile: enterprise"],
                     "<!-- G0 artifact - complete via "
                     ".Doctrine/templates/project-brief.md -->", report,
                     target)

    report.show()
    print("next steps: python tools/doctrine_state.py init && "
          "make verify; MCP + per-tool wiring: .Doctrine/05-packaging.md")
    return 1 if report.skipped_diff else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doctrine_install",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--tool", default="claude",
                        help="comma-separated: "
                             f"{','.join(sorted(ADAPTERS))} or 'all'")
    parser.add_argument("--enterprise", action="store_true",
                        help="seed 'Merge profile: enterprise' in the brief")
    parser.add_argument("--ci", action="store_true",
                        help="also install the GitHub Actions workflow")
    parser.add_argument("--force", action="store_true",
                        help="overwrite files that exist with different "
                             "content")
    args = parser.parse_args(argv)
    tools = [t.strip() for t in args.tool.split(",") if t.strip()]
    return install(args.source.resolve(), args.target.resolve(), tools,
                   args.enterprise, args.ci, args.force)


if __name__ == "__main__":
    raise SystemExit(main())

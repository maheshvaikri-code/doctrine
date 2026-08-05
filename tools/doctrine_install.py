#!/usr/bin/env python3
"""doctrine_install — install the Doctrine System into any target repo.

Copies the committed law (.Doctrine.md + .Doctrine/), the enforcement
tools and their companion artifacts, the Claude Code wiring, and the
adapter overlays for the tools you name. Idempotent: unchanged files are
skipped; files that exist with DIFFERENT content are never silently
clobbered (skipped with a warning unless --force). An existing CLAUDE.md
gets the import lines APPENDED, never replaced; an existing AGENTS.md is
left alone (use `doctrine_state.py hydrate --emit-agents` for the state
block).

Usage:
  python tools/doctrine_install.py --target ../my-repo --tool claude
  python tools/doctrine_install.py --target . --tool claude,cursor,codex
  python tools/doctrine_install.py --target ../svc --tool all --enterprise
  python tools/doctrine_install.py --target ../app --tool codex --solobuilder
  python tools/doctrine_install.py --target . --verify   # turnkey: one command

--verify makes it turnkey: after copying, it initializes the state plane
and runs the gate suite in the target, so a single command ends in a
proven-green install. MAPLE is the default workforce runtime; the legacy
--maple flag remains accepted as an idempotent compatibility alias.
--personal and --solo are aliases for the solo-builder delivery profile:
creative reversible work, deterministic verification.

--local writes a single marker-delimited managed block into the target
.gitignore that covers the WHOLE installed framework (corpus, tools, tests,
adapters, MCP registration) instead of just machine-local state, so Doctrine
stays out of the repo's history and toggling it is one block. Your docs/
gate artifacts (briefs, ADRs, reviews) are never ignored -- they are the
repo's own work product. Delete the block to un-ignore.

Publishing/registry distribution stays human-gated (.Doctrine.md section 5).
"""

from __future__ import annotations

import argparse
import contextlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import doctrine_features  # noqa: E402

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
CLAUDE_IMPORTS = ["@.Doctrine.md", "@FEATURES.md",
                  "@.doctrine-state/local/hydration.bundle.md"]
# The canonical brief marker. "personal" is the LEGACY spelling and is still
# recognised, because 15+ installed repos carry it; only the new one is written.
DELIVERY_MARKER = "Delivery profile: solobuilder"
DELIVERY_MARKERS = (DELIVERY_MARKER, "Delivery profile: personal")

TOOL_FILES = ["doctrine_state.py", "doctrine_lint.py", "doctrine_gold.py",
              "doctrine_mcp.py", "doctrine_install.py",
              "doctrine_metrics.py", "doctrine_verify.py",
              "doctrine_engage.py", "doctrine_awaken.py",
              "doctrine_signature.py", "doctrine_dashboard.py",
              "doctrine_guard.py", "doctrine_fleet.py",
              "doctrine_features.py"]
COMPANION_FILES = [
    "docs/contracts/doctrine-control-room.openapi.json",
]
# CI wiring per provider: (source file, dest under the target root). GitHub
# ships as a live workflow; the others ship as templates under .Doctrine/ so
# they land at each provider's canonical path.
CI_PROVIDERS: dict[str, tuple[str, str]] = {
    "github": (".github/workflows/doctrine.yml",
               ".github/workflows/doctrine.yml"),
    "gitlab": (".Doctrine/templates/ci/gitlab-ci.yml", ".gitlab-ci.yml"),
    "azure": (".Doctrine/templates/ci/azure-pipelines.yml",
              "azure-pipelines.yml"),
}
GITIGNORE_LINES = [".doctrine-state/local/", "__pycache__/"]
GITIGNORE_BEGIN = ("# >>> doctrine (managed by doctrine_install; "
                   "delete this block to un-ignore) >>>")
GITIGNORE_END = "# <<< doctrine <<<"


def gitignore_block(tools: list[str], local: bool) -> list[str]:
    """Lines for the managed .gitignore block.

    Default (no --local): only machine-local state + bytecode, so the corpus
    stays committable (today's behavior). With --local: the whole installed
    framework footprint, computed for the SELECTED tools so the variable
    per-adapter paths (.cursor/, .windsurf/, GEMINI.md, ...) are covered too.
    docs/ artifacts (briefs, ADRs, reviews) are deliberately never listed --
    they are the repo's OWN work product, authored via Doctrine but about the
    repo. Makefile is framework-installed but a generic name the repo may own,
    so it is offered commented rather than silently hiding the user's own.
    """
    if not local:
        return list(GITIGNORE_LINES)
    lines = [
        ".Doctrine.md", ".Doctrine/", ".doctrine-state/", "__pycache__/",
        ".mcp.json", "AGENTS.md",
        "tools/doctrine_*.py", "tests/test_doctrine_*.py",
    ]
    if "claude" in tools:
        lines += [".claude/agents/", "CLAUDE.md"]
    for tool in tools:
        lines += [dest for _src, dest in ADAPTERS.get(tool, [])]
    lines.append("# Makefile   # uncomment if Doctrine created it (generic name)")
    return lines


def write_managed_block(path: Path, lines: list[str], report: Report,
                        target: Path) -> None:
    """Write or replace ONE marker-delimited managed block, preserving all
    content outside the markers byte-exactly (a CRLF file stays CRLF -- raw
    bytes, no universal-newline translation). Idempotent."""
    existing = path.read_bytes().decode("utf-8") if path.exists() else ""
    nl = "\r\n" if "\r\n" in existing else "\n"
    block = nl.join([GITIGNORE_BEGIN, *lines, GITIGNORE_END])
    b = existing.find(GITIGNORE_BEGIN)
    e = existing.find(GITIGNORE_END)
    if b != -1 and e > b:                      # replace the existing block
        new = existing[:b] + block + existing[e + len(GITIGNORE_END):]
    else:                                      # append a fresh block
        new = existing
        if new and not new.endswith("\n"):
            new += nl
        if new:
            new += nl                          # blank line before the block
        new += block + nl
    if new == existing:
        report.skipped_same += 1
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(new.encode("utf-8"))
    report.copied.append(path.relative_to(target).as_posix())


class Report:
    def __init__(self) -> None:
        self.copied: list[str] = []
        self.skipped_same: int = 0
        self.skipped_diff: list[str] = []
        self.pruned: list[str] = []
        self.prune_backup: Path | None = None

    def show(self) -> None:
        print(f"installed: {len(self.copied)} file(s), "
              f"unchanged: {self.skipped_same}")
        if self.pruned:
            print(f"pruned {len(self.pruned)} corpus file(s) removed upstream "
                  f"(backed up to {self.prune_backup}):")
            for rel in self.pruned:
                print(f"  - {rel}")
        if self.skipped_diff:
            print(f"SKIPPED {len(self.skipped_diff)} file(s) that exist "
                  "with different content (rerun with --force to "
                  "overwrite):")
            for rel in self.skipped_diff:
                print(f"  - {rel}")


def prune_corpus(source: Path, target: Path, report: Report,
                 force: bool) -> None:
    """Delete installed corpus files that no longer exist upstream.

    The installer used to only ever COPY, so a role or skill deleted from the
    doctrine survived forever in every consumer: garagebox kept offering
    `[ROLE: Solo Builder]` after a --force reinstall that had removed it.

    Deliberately narrow, because deleting from someone else's repo is the
    dangerous direction:
      * ONLY under --force. A plain install never deletes anything.
      * ONLY inside `.Doctrine/` - the installed corpus, which the guard
        already declares a read-only snapshot owned by the installer.
        `.claude/commands/` and `.claude/agents/` are excluded even though the
        installer seeds them, because a consumer may legitimately add its own.
      * NEVER `.doctrine-state/` - that is the repo's memory, and it is not
        under `.Doctrine/` anyway. A separate test pins that.
      * Every pruned file is COPIED TO A BACKUP FIRST, so the operation is
        recoverable rather than merely careful, and the location is printed.
    """
    installed_corpus = target / ".Doctrine"
    if not force or not installed_corpus.is_dir():
        return
    # The target's own FEATURES.md decides. Default-on, so a repo installed
    # before the toggle existed behaves exactly as before.
    if not doctrine_features.is_on(target, "prune-on-force"):
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = target / ".doctrine-state" / "local" / "prune-backup" / stamp
    for path in sorted(installed_corpus.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(installed_corpus)
        if (source / ".Doctrine" / rel).exists():
            continue
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())     # back up BEFORE deleting
        path.unlink()
        report.pruned.append((Path(".Doctrine") / rel).as_posix())
        report.prune_backup = backup
    # leave no empty directories behind
    for d in sorted((p for p in installed_corpus.rglob("*") if p.is_dir()),
                    key=lambda p: len(p.parts), reverse=True):
        with contextlib.suppress(OSError):
            d.rmdir()


def copy_file(src: Path, dest: Path, target: Path, report: Report,
              force: bool) -> None:
    data = src.read_bytes()
    if dest.is_symlink():
        # never write through a link we didn't create
        if not force:
            report.skipped_diff.append(dest.relative_to(target).as_posix()
                                       + " (symlink)")
            return
        dest.unlink()
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


# Machine-local files that must NEVER travel from the source repo into a
# consumer. `*.local.json` is Claude Code's personal override layer: it MERGES
# OVER settings.json (the guard's own CONTROL_SURFACE note says so), it is
# untracked by convention, and it accumulates whatever that operator happened
# to approve. Shipping it silently grants every consumer the source machine's
# standing permissions - and leaks its absolute paths.
#
# This is the FALLBACK only. The primary rule is `source_manifest` below: ship
# what the source repo TRACKS. A denylist of known-bad names is the shape this
# project already learned loses - the guard's write-verb blocklist had to be
# inverted to a read-only allowlist after four rounds of new spellings - and
# the same applies here: `settings.local.json` was the leak we found,
# `scheduled_tasks.lock` was sitting right beside it, and the next runtime
# file Claude Code adds would leak too.
LOCAL_ONLY_SUFFIX = ".local.json"
LOCAL_ONLY_NAMES = ("settings.local.json", "scheduled_tasks.lock")


def is_machine_local(src: Path) -> bool:
    return (src.name in LOCAL_ONLY_NAMES
            or src.name.endswith(LOCAL_ONLY_SUFFIX))


def source_manifest(source: Path) -> set[str] | None:
    """Posix paths git TRACKS in the source tree, or None if git cannot say.

    Tracked-ness is the honest definition of "part of the framework": if the
    doctrine's own repo does not commit a file, it is not something to install
    into somebody else's. Returns None (not an empty set) when git is absent or
    the source is not a repo, so the caller can fall back rather than install
    nothing.
    """
    try:
        out = subprocess.run(["git", "-C", str(source), "ls-files", "-z"],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    paths = {p for p in out.stdout.split("\0") if p}
    return paths or None


def copy_tree(src_dir: Path, dest_dir: Path, target: Path, report: Report,
              force: bool, source: Path | None = None,
              tracked: set[str] | None = None) -> None:
    for src in sorted(src_dir.rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts:
            continue
        if tracked is not None and source is not None:
            if src.relative_to(source).as_posix() not in tracked:
                continue          # untracked in the source = not framework
        elif is_machine_local(src):
            continue              # no git: fall back to the denylist
        copy_file(src, dest_dir / src.relative_to(src_dir), target,
                  report, force)


def append_lines(path: Path, lines: list[str], header: str | None,
                 report: Report, target: Path) -> None:
    """Append only the missing lines; existing content is preserved
    byte-exactly, including its newline style (CRLF files stay CRLF)."""
    existing = path.read_bytes().decode("utf-8") if path.exists() else ""
    nl = "\r\n" if "\r\n" in existing else "\n"
    present = {ln.strip("\r") for ln in existing.splitlines()}
    missing = [ln for ln in lines if ln not in present]
    if not missing:
        report.skipped_same += 1
        return
    text = existing
    if text and not text.endswith(("\n",)):
        text += nl
    if text:
        text += nl  # one blank line before the appended block
    if header and header not in existing:
        text += header + nl
    text += nl.join(missing) + nl
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    report.copied.append(path.relative_to(target).as_posix())


def run_post_install(target: Path) -> int:
    """Turnkey --verify: initialize the state plane, then run the gate
    suite in the freshly installed target. Argv list only, no shell,
    sys.executable — cross-platform. Returns the worst exit code."""
    py = sys.executable
    print("=== turnkey: initializing state plane ===")
    init = subprocess.run([py, "tools/doctrine_state.py", "init"], cwd=target)
    print("=== turnkey: running the gate suite (doctrine_verify) ===")
    verify = subprocess.run([py, "tools/doctrine_verify.py"], cwd=target)
    return init.returncode or verify.returncode


def install(source: Path, target: Path, tools: list[str],
            enterprise: bool, ci: bool, force: bool,
            startup: bool = False, verify: bool = False,
            maple: bool = False, local: bool = False,
            personal: bool = False, ci_provider: str = "github") -> int:
    if not (source / ".Doctrine.md").exists():
        print(f"error: {source} is not a doctrine source tree "
              "(.Doctrine.md missing)", file=sys.stderr)
        return 2
    src_res, tgt_res = source.resolve(), target.resolve()
    if src_res == tgt_res:
        print("error: target is the source tree itself", file=sys.stderr)
        return 2
    if src_res in tgt_res.parents or tgt_res in src_res.parents:
        print("error: source and target must not nest (installing into a "
              "subdirectory of the source re-ingests itself on rerun)",
              file=sys.stderr)
        return 2
    if ci_provider not in CI_PROVIDERS:
        print(f"error: unknown CI provider {ci_provider!r}; choose from "
              f"{sorted(CI_PROVIDERS)}", file=sys.stderr)
        return 2
    unknown = [t for t in tools if t not in ADAPTERS and t != "all"]
    if unknown:
        print(f"error: unknown tool(s) {unknown}; choose from "
              f"{sorted(ADAPTERS)} or 'all'", file=sys.stderr)
        return 2
    if "all" in tools:
        tools = sorted(ADAPTERS)
    brief_path = target / "docs" / "brief.md"
    existing_brief = (brief_path.read_text("utf-8", "replace")
                      if brief_path.is_file() else "")
    if personal and (enterprise
                     or "Merge profile: enterprise" in existing_brief):
        print("error: personal/solo and enterprise delivery profiles are "
              "mutually exclusive", file=sys.stderr)
        return 2
    if enterprise and any(m in existing_brief for m in DELIVERY_MARKERS):
        print("error: enterprise and personal/solo delivery profiles are "
              "mutually exclusive", file=sys.stderr)
        return 2
    # Atomic-update guard. copy_file preserves (skips) different-content files
    # without --force -- fine for a locally-edited playbook, but if the skipped
    # set includes a framework CONSISTENCY CARRIER (the README that states the
    # role/skill counts, the installer manifest, or the law itself) the framework
    # goes internally inconsistent: new files land while the counts/manifest stay
    # stale, and the consumer's own doctrine_lint/packaging then fail (the
    # a consumer repo's drift, 2026-07-16). Refuse before touching the target; --force
    # updates the whole framework atomically. A generic differing file still
    # skips-with-a-warning as before.
    if not force:
        carriers = [".Doctrine/README.md",        # role/skill counts
                    "tools/doctrine_install.py",   # the file manifest (TOOL_FILES)
                    ".Doctrine.md"]                # the law / version
        drifted = [rel for rel in carriers
                   if (target / rel).exists()
                   and (source / rel).read_bytes() != (target / rel).read_bytes()]
        if drifted:
            print("error: updating an existing Doctrine, but framework "
                  "consistency carrier(s) " + ", ".join(drifted) + " differ. A "
                  "non-force update would copy new files while leaving these "
                  "stale, drifting the README counts / installer manifest and "
                  "breaking the consumer's own doctrine_lint/packaging. Re-run "
                  "with --force to update the framework atomically.",
                  file=sys.stderr)
            return 2
    target.mkdir(parents=True, exist_ok=True)
    report = Report()

    # the law
    copy_file(source / ".Doctrine.md", target / ".Doctrine.md", target,
              report, force)
    tracked = source_manifest(source)
    copy_tree(source / ".Doctrine", target / ".Doctrine", target, report,
              force, source, tracked)
    # ...and, under --force only, remove corpus files deleted upstream, after
    # backing each one up. Copy-only upgrades left deleted roles installed and
    # selectable forever.
    prune_corpus(source, target, report, force)
    # the enforcement suite + its tests
    for name in TOOL_FILES:
        copy_file(source / "tools" / name, target / "tools" / name,
                  target, report, force)
    for test in sorted((source / "tests").glob("test_doctrine_*.py")):
        copy_file(test, target / "tests" / test.name, target, report, force)
    for rel in COMPANION_FILES:
        copy_file(source / rel, target / rel, target, report, force)
    if not (target / "Makefile").exists():
        copy_file(source / "Makefile", target / "Makefile", target,
                  report, force)
    if ci:
        src_rel, dest_rel = CI_PROVIDERS[ci_provider]
        copy_file(source / src_rel, target / dest_rel, target, report, force)

    # FEATURES.md - the repo's toggle switchboard. CONSUMER-OWNED policy, so
    # it is seeded when absent and NEVER overwritten, not even under --force:
    # clobbering it would silently re-enable something the human turned off.
    features = target / "FEATURES.md"
    if not features.exists():
        copy_file(source / "FEATURES.md", features, target, report, force)

    # AGENTS.md universal boot. Seeded when absent; when it exists and differs,
    # copy_file SKIPS it and reports it in skipped_diff unless --force. It used
    # to be `if not agents.exists()`, which exempted it from --force entirely -
    # so the boot file governing every non-Claude agent went permanently stale
    # after the first install, still prescribing roles the corpus had removed,
    # and said nothing about it. Silent staleness in the ignition file is worse
    # than a reported skip.
    copy_file(source / ".Doctrine" / "adapters" / "AGENTS.md",
              target / "AGENTS.md", target, report, force)

    # .mcp.json local MCP registration (never overwrite - the consumer may run
    # its own MCP servers). Registers the doctrineos server so any MCP-capable
    # agent gets the doctrine tools locally: no marketplace, no publish. The
    # MCP client still gates activation with its own approval prompt.
    mcp = target / ".mcp.json"
    if not mcp.exists() and (source / ".mcp.json").exists():
        copy_file(source / ".mcp.json", mcp, target, report, force)

    if "claude" in tools:
        copy_tree(source / ".claude", target / ".claude", target, report,
                  force, source, tracked)
        append_lines(target / "CLAUDE.md", CLAUDE_IMPORTS, None, report,
                     target)
    for tool in tools:
        for src_name, dest_rel in ADAPTERS[tool]:
            copy_file(source / ".Doctrine" / "adapters" / src_name,
                      target / dest_rel, target, report, force)

    write_managed_block(target / ".gitignore", gitignore_block(tools, local),
                        report, target)
    # MAPLE is the universal workforce selection. The legacy ``maple``
    # argument is intentionally accepted for API/CLI compatibility; append_lines
    # keeps the marker singular on both old and new invocations.
    brief_lines = ["Workforce runtime: maple"]
    if enterprise:
        brief_lines.append("Merge profile: enterprise")
    if startup:
        brief_lines.append("Company profile: startup")
    if personal:
        brief_lines.append(DELIVERY_MARKER)
        has_agent_latitude = any(
            line.strip().startswith("Agent latitude:")
            or "**Agent latitude:**" in line
            for line in existing_brief.splitlines()
        )
        if not has_agent_latitude:
            brief_lines.append("Agent latitude: creative")
    # A project may keep these canonical markers inside a richer Markdown
    # profile line (for example, wrapped in backticks). Treat the exact marker
    # text anywhere in the existing brief as already selected. Reinstall must
    # not append a duplicate block or rewrite repository-owned planning data.
    brief_lines = [line for line in brief_lines if line not in existing_brief]
    if brief_lines:
        append_lines(brief_path, brief_lines,
                     "<!-- G0 artifact - complete via "
                     ".Doctrine/templates/project-brief.md -->", report,
                     target)

    report.show()
    rc = 1 if report.skipped_diff else 0
    if verify:
        # SECURITY (G5 MAJOR-1): run_post_install executes the target's
        # tool files. copy_file SKIPS (does not overwrite) a tool that
        # already exists with different content unless --force, so running
        # --verify then would execute code this installer did not write and
        # could print a false "gates green". Refuse instead.
        conflicted = [r for r in report.skipped_diff
                      if any(tf in r for tf in TOOL_FILES)]
        if conflicted:
            print("refusing --verify: the target has different-content "
                  "enforcement tools that were not overwritten "
                  f"({', '.join(conflicted)}); running them would execute "
                  "code this installer did not write. Resolve the conflict "
                  "or rerun with --force.", file=sys.stderr)
            return 2
        vc = run_post_install(target)
        if vc == 0:
            print("turnkey: installed and verified - gates green. "
                  "Engage with: doctrine: <task>")
        else:
            print("turnkey: install done, but the gate suite did NOT pass "
                  "- see the gate output above (nothing was weakened to "
                  "go green; fix and rerun verify).")
        rc = vc or rc
    else:
        print("next steps: python tools/doctrine_state.py init, then "
              "python tools/doctrine_verify.py (= make verify, no Make "
              "needed); MCP + per-tool wiring: .Doctrine/05-packaging.md")
    return rc


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
    parser.add_argument("--startup", action="store_true",
                        help="seed 'Company profile: startup' in the brief "
                             "(activates the founder-ops roles)")
    parser.add_argument("--solobuilder", dest="personal",
                        action="store_true",
                        help="solo-builder delivery: relaxed GATING, full role "
                             "set, creative build then deterministic DevOps "
                             "verification ('Delivery profile: solobuilder')")
    parser.add_argument("--ci", action="store_true",
                        help="also install the CI gate suite (see "
                             "--ci-provider)")
    parser.add_argument("--ci-provider", default="github",
                        choices=sorted(CI_PROVIDERS),
                        help="which CI system to wire the gates into "
                             "(default: github)")
    parser.add_argument("--maple", action="store_true",
                        help="deprecated compatibility alias; MAPLE is the "
                             "default workforce runtime (see "
                             ".Doctrine/integrations/maple.md)")
    parser.add_argument("--verify", action="store_true",
                        help="turnkey: after install, initialize state and "
                             "run the gate suite in the target so one "
                             "command ends verified")
    parser.add_argument("--force", action="store_true",
                        help="overwrite files that exist with different "
                             "content, and prune .Doctrine/ files deleted "
                             "upstream (each is backed up to "
                             ".doctrine-state/local/prune-backup/ first)")
    parser.add_argument("--local", action="store_true",
                        help="keep the WHOLE framework out of git: the managed "
                             ".gitignore block lists every installed framework "
                             "path (corpus, tools, tests, adapters, MCP) rather "
                             "than just machine-local state. docs/ artifacts "
                             "stay committable; delete the block to un-ignore")
    args = parser.parse_args(argv)
    tools = [t.strip() for t in args.tool.split(",") if t.strip()]
    return install(args.source.resolve(), args.target.resolve(), tools,
                   args.enterprise, args.ci, args.force, args.startup,
                   verify=args.verify, maple=args.maple, local=args.local,
                   personal=args.personal, ci_provider=args.ci_provider)


if __name__ == "__main__":
    raise SystemExit(main())

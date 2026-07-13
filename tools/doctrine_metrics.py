#!/usr/bin/env python3
"""doctrine_metrics — bridge the doctrine's review artifacts to CodeMonk.

Git history alone reads HITL as zero. This tool scans the doctrine's
review/QA/merge artifacts (docs/reviews/, docs/qa/, docs/merges/) for
commit references, verifies each against the repository, and emits a
CodeMonk enrichment overlay marking those commits as reviewed:

  python tools/doctrine_metrics.py enrich
  python -m codemonk analyze --repo . --enrich docs/metrics/enrichment.json

Fidelity note (stated in the output too): in a doctrine repo the review
loop is the fresh-context VERIFIER fan-out (adversarial agent review,
human-arbitrated) — the enrichment flags coverage by that loop via
CodeMonk's review field. Quote the resulting HITL with that label.

Only hex tokens that resolve to real commits reachable from HEAD are
emitted; tokens are regex-validated before ever reaching git argv.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from doctrine_state import StateError, git  # noqa: E402

ARTIFACT_DIRS = ["docs/reviews", "docs/qa", "docs/merges"]
DEFAULT_OUT = Path("docs") / "metrics" / "enrichment.json"
# word-bounded 7-40 hex; a 64-hex sha256 is one word and cannot match
HEX_RE = re.compile(r"\b[0-9a-f]{7,40}\b")


def resolve_commit(repo: Path, token: str) -> str | None:
    """Full sha if the token names a commit reachable from HEAD."""
    try:
        full = git(repo, "rev-parse", "--verify", "--quiet",
                   f"{token}^{{commit}}")
    except subprocess.CalledProcessError:
        return None
    try:
        git(repo, "merge-base", "--is-ancestor", full, "HEAD")
    except subprocess.CalledProcessError:
        return None
    return full


def collect(repo: Path, dirs: list[str]) -> tuple[dict[str, list[str]], int]:
    """commit -> artifact paths that reference it, plus files scanned."""
    referenced: dict[str, set[str]] = {}
    scanned = 0
    cache: dict[str, str | None] = {}
    for rel in dirs:
        base = repo / rel
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.md")):
            scanned += 1
            text = f.read_text("utf-8", errors="replace")
            for token in set(HEX_RE.findall(text)):
                if token not in cache:
                    cache[token] = resolve_commit(repo, token)
                full = cache[token]
                if full:
                    referenced.setdefault(full, set()).add(
                        f.relative_to(repo).as_posix())
    return {sha: sorted(files) for sha, files in referenced.items()}, scanned


def cmd_enrich(repo: Path, dirs: list[str], out_rel: Path) -> int:
    if not (repo / ".git").exists():
        raise StateError(f"{repo} is not a git repository")
    referenced, scanned = collect(repo, dirs)
    if not scanned:
        print("no review artifacts found under "
              f"{', '.join(dirs)} - nothing to enrich", file=sys.stderr)
        return 1
    entries = [{"id": sha, "human_reviewed": True}
               for sha in sorted(referenced)]
    out = repo / out_rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(entries, indent=2, sort_keys=True) + "\n")
                    .encode("utf-8"))
    print(f"enrichment written: {out_rel.as_posix()} - {len(entries)} "
          f"reviewed commit(s) from {scanned} artifact file(s)")
    print("fidelity: 'reviewed' = referenced by the doctrine's verifier "
          "fan-out artifacts (adversarial agent review, human-arbitrated) "
          "- label HITL accordingly when quoting")
    for sha, files in sorted(referenced.items()):
        print(f"  {sha[:12]} <- {', '.join(files)}")
    print("consume: python -m codemonk analyze --repo . "
          f"--enrich {out_rel.as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doctrine_metrics",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    p_en = sub.add_parser("enrich")
    p_en.add_argument("--dirs", nargs="*", default=ARTIFACT_DIRS)
    p_en.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        if args.command == "enrich":
            return cmd_enrich(args.root.resolve(), list(args.dirs),
                              args.out)
    except StateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"git failed: {exc.stderr.strip()}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""doctrine_gold — Gold Build promotion for the enterprise merge profile
(.Doctrine/standards/merge-and-promotion.md).

Commands:
  record --input F   promote a candidate: validate the proposal, stamp
                     at_commit from the tag, hash the artifacts, chain to
                     the previous gold record, REFUSE without the council
                     verdict + all sign-offs + human approval on disk.
                     Nothing is written until everything validates.
  check --tag vX.Y.Z re-verify a gold record: schema, artifact re-hash,
                     chain link, referenced files exist, tag -> commit
                     match. Deploy pipelines run this and refuse on exit 1.

Gold records are immutable canonical JSON at docs/releases/gold/<tag>.json,
hash-chained via prev_gold_sha256 - the chain is the rollback ladder.

Terminal output is ASCII-only. Exit codes: 0 ok / 1 verification failed /
2 usage or validation error.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from doctrine_state import (  # noqa: E402
    SchemaError,
    StateError,
    canonical_bytes,
    git,
    load_json,
    now_utc,
    sha256_bytes,
    sha256_file,
    validate,
)

GOLD_DIR = Path("docs") / "releases" / "gold"


def load_gold_schema(repo: Path) -> dict:
    path = (repo / ".Doctrine" / "schemas" / "gold-build.schema.json")
    if not path.exists():
        raise StateError(f"schema not found: {path}")
    return load_json(path, "schema")


def safe_repo_path(repo: Path, rel: str, what: str) -> Path:
    """Resolve a record-referenced path, refusing escapes from the repo."""
    candidate = (repo / rel).resolve()
    root = repo.resolve()
    if root != candidate and root not in candidate.parents:
        raise StateError(f"{what} '{rel}' escapes the repo root")
    return candidate


def tag_commit(repo: Path, tag: str) -> str:
    """Full commit sha the annotated tag points at."""
    return git(repo, "rev-list", "-n", "1", tag)


def _gold_records(repo: Path) -> list[Path]:
    gold = repo / GOLD_DIR
    if not gold.exists():
        return []
    return sorted(gold.glob("v*.json"), key=lambda p: p.stat().st_mtime)


def _latest_gold(repo: Path) -> Path | None:
    records = _gold_records(repo)
    return records[-1] if records else None


def cmd_record(repo: Path, input_path: Path) -> int:
    proposal = load_json(input_path, "gold proposal")
    for field in ("tag", "merge_verdict", "signoffs", "artifacts", "soak",
                  "human_approval"):
        if field not in proposal:
            raise StateError(f"gold proposal missing '{field}'")
    tag = proposal["tag"]

    # ---- dispose: every claim verified before anything is written ----
    at_commit = tag_commit(repo, tag)

    verdict = safe_repo_path(repo, proposal["merge_verdict"],
                             "merge verdict")
    if not verdict.exists():
        raise StateError(f"council verdict not on disk: "
                         f"{proposal['merge_verdict']} - no verdict, "
                         "no gold")
    for name, rel in proposal["signoffs"].items():
        p = safe_repo_path(repo, rel, f"sign-off '{name}'")
        if not p.exists():
            raise StateError(f"sign-off '{name}' not on disk: {rel}")

    artifacts = []
    for entry in proposal["artifacts"]:
        rel = entry["path"] if isinstance(entry, dict) else entry
        p = safe_repo_path(repo, rel, "artifact")
        if not p.exists():
            raise StateError(f"artifact not on disk: {rel}")
        artifacts.append({"path": rel, "sha256": sha256_file(p)})

    prev = _latest_gold(repo)
    record = {
        "gold_version": "1", "tag": tag, "at_commit": at_commit,
        "created_at": now_utc(),
        "merge_verdict": proposal["merge_verdict"],
        "signoffs": proposal["signoffs"],
        "artifacts": artifacts,
        "soak": proposal["soak"],
        "human_approval": proposal["human_approval"],
        "prev_gold_sha256": sha256_file(prev) if prev else None,
    }
    validate(record, load_gold_schema(repo))

    out = repo / GOLD_DIR / f"{tag}.json"
    if out.exists():
        raise StateError(f"gold record already exists for {tag} - records "
                         "are immutable; a correction is a NEW tag")

    # ---- write phase ----
    out.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_bytes(record)
    out.write_bytes(data)
    print(f"GOLD: {tag} at {at_commit[:12]} "
          f"({sha256_bytes(data)[:12]}); {len(artifacts)} artifact(s)"
          + (f"; chained to {prev.name}" if prev else "; genesis record"))
    print(f"remember: git add {out.relative_to(repo).as_posix()} && "
          f"git commit -m \"release: gold {tag}\"")
    return 0


def cmd_check(repo: Path, tag: str) -> int:
    findings: list[str] = []
    path = repo / GOLD_DIR / f"{tag}.json"
    if not path.exists():
        print(f"CHECK FAILED: no gold record for {tag} - do not deploy")
        return 1
    record = load_json(path, "gold record")
    try:
        validate(record, load_gold_schema(repo))
    except SchemaError as exc:
        findings.append(f"schema: {exc}")

    if record.get("tag") != tag:
        findings.append(f"record tag {record.get('tag')!r} != {tag!r}")
    try:
        actual = tag_commit(repo, tag)
        if record.get("at_commit") != actual:
            findings.append(f"tag now points at {actual[:12]}, record says "
                            f"{str(record.get('at_commit'))[:12]} - "
                            "the tag moved")
    except subprocess.CalledProcessError:
        findings.append(f"git tag {tag} does not exist")

    for entry in record.get("artifacts", []):
        try:
            p = safe_repo_path(repo, entry["path"], "artifact")
        except StateError as exc:
            findings.append(str(exc))
            continue
        if not p.exists():
            findings.append(f"artifact missing: {entry['path']}")
        elif sha256_file(p) != entry["sha256"]:
            findings.append(f"artifact hash mismatch: {entry['path']} - "
                            "the artifact changed after promotion")

    refs = [("merge verdict", record.get("merge_verdict"))]
    refs += [(f"sign-off '{k}'", v)
             for k, v in (record.get("signoffs") or {}).items()]
    for what, rel in refs:
        if not rel:
            continue
        try:
            if not safe_repo_path(repo, rel, what).exists():
                findings.append(f"{what} missing: {rel}")
        except StateError as exc:
            findings.append(str(exc))

    prev_sha = record.get("prev_gold_sha256")
    others = [p for p in _gold_records(repo) if p.name != path.name]
    if prev_sha is not None:
        if not any(sha256_file(p) == prev_sha for p in others):
            findings.append("prev_gold_sha256 matches no gold record on "
                            "disk - broken rollback chain")
    elif others and min(o.stat().st_mtime for o in others) \
            < path.stat().st_mtime:
        findings.append("genesis record (prev null) but older gold "
                        "records exist")

    if findings:
        print(f"CHECK FAILED ({len(findings)}) - do not deploy {tag}:")
        for msg in findings:
            print(f"  - {msg}")
        return 1
    print(f"check OK: {tag} is GOLD - schema valid, artifacts match, "
          "chain intact, sign-offs on disk")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doctrine_gold",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    p_rec = sub.add_parser("record")
    p_rec.add_argument("--input", type=Path, required=True)
    p_chk = sub.add_parser("check")
    p_chk.add_argument("--tag", required=True)
    args = parser.parse_args(argv)

    repo = args.root.resolve()
    try:
        if args.command == "record":
            return cmd_record(repo, args.input)
        if args.command == "check":
            return cmd_check(repo, args.tag)
    except (SchemaError, StateError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"git failed: {exc.stderr.strip()}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

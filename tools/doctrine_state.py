#!/usr/bin/env python3
"""doctrine_state — stdlib-only reference implementation of the Doctrine
state plane (.Doctrine/state-plane/STATE.md + hydration/HYDRATION.md).

Commands:
  init                    create .doctrine/state/ layout (local/ gitignored)
  checkpoint --proposal F model proposes, this validator disposes: stamps
                          at_commit/seq/created_at, chains prev_sha256,
                          writes checkpoint + history copy + distillate,
                          appends decision_ref claims to DECISIONS.ndjson,
                          prunes old distillates (dead_ends merge forward)
  verify                  walk the checkpoint chain (prev_sha256 links,
                          monotonic seq) and re-hash state_index targets
  hydrate [--check]       compile the bounded hydration bundle (markdown);
                          --check compiles twice and asserts identical
                          bundle_sha256 (determinism gate)
  prune [--keep N]        prune distillates beyond N (default 5)
  status                  one-screen summary

Design decision (documented per plan): dead_ends of pruned distillates are
merged into the NEW distillate at checkpoint time, deduped, oldest dropped
first when the schema cap (8) overflows — stored artifacts stay immutable.

Canonicalization (pack-wide): UTF-8, LF, lexicographically sorted keys,
no trailing whitespace, single trailing newline.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_KEEP = 5
TOKEN_CHARS = 4  # 1 token ~ 4 chars, per HYDRATION.md budget accounting
BUDGETS = [  # (section, tokens, never_trim)
    ("invariants", 800, True),
    ("control", 200, True),
    ("intents", 1200, False),
    ("distillate", 1600, False),
    ("decisions", 800, False),
    ("graph", 1000, False),
    ("effects", 400, False),
]


# ---------------------------------------------------------------- canonical

def canonical_bytes(obj) -> bytes:
    """Serialize per the pack-wide canonicalization rules."""
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2,
                      separators=(",", ": "))
    return (text + "\n").encode("utf-8")


def canonical_line(obj) -> str:
    """One canonical NDJSON line (no indent, sorted keys)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


# ------------------------------------------------------- minimal validator

class SchemaError(ValueError):
    pass


def validate(instance, schema, root=None, path="$"):
    """Minimal JSON-Schema validator covering exactly the constructs used
    by checkpoint.schema.json / distillate.schema.json. Raises SchemaError
    with a JSON-path on first failure."""
    if root is None:
        root = schema
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise SchemaError(f"{path}: unsupported $ref {ref}")
        schema = root["$defs"][ref.split("/")[-1]]

    if "anyOf" in schema:
        errors = []
        for sub in schema["anyOf"]:
            try:
                validate(instance, sub, root, path)
                break
            except SchemaError as exc:
                errors.append(str(exc))
        else:
            raise SchemaError(f"{path}: matched no anyOf branch "
                              f"({'; '.join(errors)})")
        return

    if "const" in schema and instance != schema["const"]:
        raise SchemaError(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaError(f"{path}: {instance!r} not in {schema['enum']}")

    stype = schema.get("type")
    if stype == "object":
        if not isinstance(instance, dict):
            raise SchemaError(f"{path}: expected object")
        for req in schema.get("required", []):
            if req not in instance:
                raise SchemaError(f"{path}: missing required '{req}'")
        props = schema.get("properties", {})
        addl = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], root, f"{path}.{key}")
            elif isinstance(addl, dict):
                validate(value, addl, root, f"{path}.{key}")
            elif addl is False:
                raise SchemaError(f"{path}: unknown field '{key}' rejected "
                                  "(additionalProperties: false)")
    elif stype == "array":
        if not isinstance(instance, list):
            raise SchemaError(f"{path}: expected array")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            raise SchemaError(f"{path}: {len(instance)} items exceeds "
                              f"maxItems {schema['maxItems']}")
        for i, item in enumerate(instance):
            if "items" in schema:
                validate(item, schema["items"], root, f"{path}[{i}]")
    elif stype == "string":
        if not isinstance(instance, str):
            raise SchemaError(f"{path}: expected string")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise SchemaError(f"{path}: shorter than {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            raise SchemaError(f"{path}: longer than {schema['maxLength']}")
        if "pattern" in schema and not re.fullmatch(schema["pattern"],
                                                    instance):
            raise SchemaError(f"{path}: does not match {schema['pattern']}")
        if schema.get("format") == "date-time" and not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?"
                r"(Z|[+-]\d{2}:\d{2})", instance):
            raise SchemaError(f"{path}: not an RFC3339 date-time")
    elif stype == "integer":
        if not isinstance(instance, int) or isinstance(instance, bool):
            raise SchemaError(f"{path}: expected integer")
        if "minimum" in schema and instance < schema["minimum"]:
            raise SchemaError(f"{path}: below minimum {schema['minimum']}")
    elif stype == "null":
        if instance is not None:
            raise SchemaError(f"{path}: expected null")


# ------------------------------------------------------------------ layout

class Plane:
    """Paths of one repo's state plane."""

    def __init__(self, repo_root: Path):
        self.repo = repo_root
        self.state = repo_root / ".doctrine" / "state"
        self.checkpoint = self.state / "checkpoint.json"
        self.checkpoints = self.state / "checkpoints"
        self.intents = self.state / "intent"
        self.decisions = self.state / "decisions" / "DECISIONS.ndjson"
        self.effects = self.state / "effects"
        self.distillates = self.state / "distillates"
        self.local = self.state / "local"

    def schemas_dir(self) -> Path:
        return self.repo / ".Doctrine" / "state-plane" / "schemas"

    def load_schema(self, name: str) -> dict:
        return json.loads(
            (self.schemas_dir() / f"{name}.schema.json").read_text("utf-8"))


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                         text=True, check=True)
    return out.stdout.strip()


def head_commit(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD")


def worktree_state(repo: Path) -> str:
    return "dirty" if git(repo, "status", "--porcelain") else "clean"


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- commands

def cmd_init(plane: Plane) -> int:
    for d in (plane.checkpoints, plane.intents, plane.decisions.parent,
              plane.effects, plane.distillates, plane.local):
        d.mkdir(parents=True, exist_ok=True)
    ignore = plane.local / ".gitignore"
    if not ignore.exists():
        ignore.write_bytes(b"*\n!.gitignore\n")
    print(f"state plane initialized at {plane.state}")
    return 0


def _distillate_files(plane: Plane) -> list[Path]:
    if not plane.distillates.exists():
        return []
    files = [p for p in plane.distillates.iterdir()
             if p.suffix == ".json" and re.match(r"^\d+-", p.name)]
    return sorted(files, key=lambda p: int(p.name.split("-", 1)[0]))


def _decisions_sha(plane: Plane) -> str:
    if plane.decisions.exists():
        return sha256_file(plane.decisions)
    return sha256_bytes(b"")


def _unresolved_effects(plane: Plane) -> int:
    count = 0
    if plane.effects.exists():
        for f in plane.effects.glob("*.effects.ndjson"):
            for line in f.read_text("utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    count += 1  # malformed = unresolved by definition
                    continue
                if entry.get("status") not in ("confirmed", "compensated"):
                    count += 1
    return count


def _graph_index(plane: Plane, at_commit: str) -> dict:
    graph = plane.repo / "graphify-out" / "graph.json"
    if not graph.exists():
        return {"built_at_commit": None}
    entry: dict = {"sha256": sha256_file(graph)}
    try:
        built = json.loads(graph.read_text("utf-8")).get("built_at_commit")
    except (json.JSONDecodeError, UnicodeDecodeError):
        built = None
    entry["built_at_commit"] = built if built else at_commit
    return entry


def _merge_dead_ends(new_ends: list, pruned_files: list[Path],
                     cap: int = 8) -> tuple[list, int]:
    """Dedupe (approach, why_failed) across new + pruned; newest-first
    priority; returns (merged ≤ cap, dropped_count)."""
    seen, merged = set(), []
    pruned_ends: list = []
    for f in pruned_files:
        try:
            pruned_ends.extend(json.loads(f.read_text("utf-8"))
                               .get("dead_ends", []))
        except json.JSONDecodeError:
            continue
    for end in list(new_ends) + pruned_ends:
        key = (end.get("approach"), end.get("why_failed"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(end)
    return merged[:cap], max(0, len(merged) - cap)


def cmd_checkpoint(plane: Plane, proposal_path: Path,
                   keep: int = DEFAULT_KEEP) -> int:
    proposal = json.loads(proposal_path.read_text("utf-8"))
    for field in ("session_id", "control", "distillate"):
        if field not in proposal:
            print(f"proposal missing '{field}'", file=sys.stderr)
            return 2

    at_commit = head_commit(plane.repo)
    created = now_utc()
    session = proposal["session_id"]

    prev_sha, seq = None, 0
    if plane.checkpoint.exists():
        prev_sha = sha256_file(plane.checkpoint)
        seq = json.loads(plane.checkpoint.read_text("utf-8"))["seq"] + 1

    # prune BEFORE writing, so pruned dead_ends merge into the new one
    existing = _distillate_files(plane)
    cut = len(existing) - max(keep - 1, 0)
    pruned = existing[:cut] if cut > 0 else []
    pending = plane.distillates / "pending-dead-ends.json"

    dist_body = dict(proposal["distillate"])
    pending_ends = json.loads(pending.read_text("utf-8")).get(
        "dead_ends", []) if pending.exists() else []
    merged, dropped = _merge_dead_ends(
        list(dist_body.get("dead_ends", [])) + pending_ends, pruned)
    dist_body["dead_ends"] = merged
    if dropped:
        print(f"note: {dropped} merged dead_end(s) dropped at the schema "
              "cap of 8 (oldest first)", file=sys.stderr)

    distillate = {
        "distillate_version": "1", "seq": seq, "session_id": session,
        "created_at": created, "at_commit": at_commit, **dist_body,
    }
    validate(distillate, plane.load_schema("distillate"))
    dist_bytes = canonical_bytes(distillate)
    dist_sha = sha256_bytes(dist_bytes)

    # decisions: append decision_ref claims (append-only, never rewritten)
    for claim in distillate.get("learned", []):
        if claim.get("kind") == "decision_ref":
            plane.decisions.parent.mkdir(parents=True, exist_ok=True)
            line = canonical_line({
                "at_commit": at_commit, "claim": claim["claim"],
                "created_at": created, "evidence": claim["evidence"],
                "intents": distillate.get("task_refs", []),
                "seq": seq, "session_id": session,
            })
            with plane.decisions.open("a", encoding="utf-8", newline="\n") \
                    as fh:
                fh.write(line + "\n")

    intents_index = {
        p.name.removesuffix(".intent.json"): sha256_file(p)
        for p in sorted(plane.intents.glob("*.intent.json"))
    } if plane.intents.exists() else {}

    checkpoint = {
        "checkpoint_version": "1", "seq": seq, "prev_sha256": prev_sha,
        "created_at": created, "at_commit": at_commit,
        "session_id": session, "worktree": worktree_state(plane.repo),
        "control": proposal["control"],
        "state_index": {
            "intents": intents_index,
            "decisions_sha256": _decisions_sha(plane),
            "latest_distillate_sha256": dist_sha,
            "graph": _graph_index(plane, at_commit),
            "unresolved_effects": _unresolved_effects(plane),
        },
    }
    validate(checkpoint, plane.load_schema("checkpoint"))
    cp_bytes = canonical_bytes(checkpoint)
    cp_sha = sha256_bytes(cp_bytes)

    # write phase (all validations passed)
    plane.distillates.mkdir(parents=True, exist_ok=True)
    (plane.distillates / f"{seq}-{dist_sha[:12]}.json").write_bytes(
        dist_bytes)
    for f in pruned:
        f.unlink()
    if pending.exists():
        pending.unlink()
    plane.checkpoints.mkdir(parents=True, exist_ok=True)
    plane.checkpoint.write_bytes(cp_bytes)
    (plane.checkpoints / f"{seq}-{cp_sha[:12]}.json").write_bytes(cp_bytes)

    print(f"checkpoint {seq} written at {at_commit[:12]} "
          f"({cp_sha[:12]}); distillate {dist_sha[:12]}"
          + (f"; pruned {len(pruned)} distillate(s)" if pruned else ""))
    return 0


def cmd_verify(plane: Plane) -> int:
    failures: list[str] = []
    files = sorted(
        (p for p in plane.checkpoints.glob("*.json")),
        key=lambda p: int(p.name.split("-", 1)[0]),
    ) if plane.checkpoints.exists() else []
    if not files:
        print("nothing to verify: no checkpoints")
        return 0

    schema = plane.load_schema("checkpoint")
    prev_file: Path | None = None
    for f in files:
        data = json.loads(f.read_text("utf-8"))
        try:
            validate(data, schema)
        except SchemaError as exc:
            failures.append(f"{f.name}: schema: {exc}")
        expected_seq = 0 if prev_file is None else \
            int(prev_file.name.split("-", 1)[0]) + 1
        if data["seq"] != expected_seq:
            failures.append(f"{f.name}: seq {data['seq']} != expected "
                            f"{expected_seq}")
        expected_prev = None if prev_file is None else sha256_file(prev_file)
        if data["prev_sha256"] != expected_prev:
            failures.append(f"{f.name}: broken chain — prev_sha256 does "
                            "not match predecessor's canonical bytes")
        if f.read_bytes() != canonical_bytes(data):
            failures.append(f"{f.name}: not canonical bytes")
        prev_file = f

    if not plane.checkpoint.exists():
        failures.append("checkpoint.json missing while history exists")
    elif plane.checkpoint.read_bytes() != prev_file.read_bytes():
        failures.append("checkpoint.json != latest history copy")
    else:
        current = json.loads(plane.checkpoint.read_text("utf-8"))
        idx = current["state_index"]
        if idx["decisions_sha256"] != _decisions_sha(plane):
            failures.append("state_index.decisions_sha256 desync")
        want = idx["latest_distillate_sha256"]
        dists = _distillate_files(plane)
        have = sha256_file(dists[-1]) if dists else None
        if want != have:
            failures.append("state_index.latest_distillate_sha256 desync")
        for intent, sha in (idx.get("intents") or {}).items():
            p = plane.intents / f"{intent}.intent.json"
            if not p.exists():
                failures.append(f"intent '{intent}' indexed but missing")
            elif sha256_file(p) != sha:
                failures.append(f"intent '{intent}' hash desync")

    if failures:
        print(f"VERIFY FAILED ({len(failures)}):")
        for msg in failures:
            print(f"  - {msg}")
        return 1
    print(f"verify OK: {len(files)} checkpoint(s), chain intact, "
          "state_index hashes match")
    return 0


# ---------------------------------------------------------------- hydrate

def _clip(text: str, tokens: int) -> tuple[str, bool]:
    limit = tokens * TOKEN_CHARS
    if len(text) <= limit:
        return text, False
    return text[:limit].rsplit("\n", 1)[0] + "\n", True


def _extract_sections(md: str, headings: list[str]) -> str:
    """Extract '## <heading>' sections from a markdown file."""
    out: list[str] = []
    lines = md.splitlines()
    keep = False
    for line in lines:
        if line.startswith("## "):
            keep = any(h in line for h in headings)
        if keep:
            out.append(line)
    return "\n".join(out).strip()


def _stale_prefix(artifact_commit: str | None, head: str,
                  stale: list[str], label: str) -> str:
    if artifact_commit and not head.startswith(artifact_commit) \
            and artifact_commit != head:
        stale.append(label)
        return f"STALE@{artifact_commit[:12]} "
    return ""


def build_bundle_body(plane: Plane) -> tuple[str, list[str], list[str]]:
    """Deterministic bundle body (no timestamps). Returns
    (body, trimmed[], stale[])."""
    cp = json.loads(plane.checkpoint.read_text("utf-8"))
    head = head_commit(plane.repo)
    trimmed: list[str] = []
    stale: list[str] = []
    parts: list[str] = []

    # 1 invariants — REPO.md/ROLE.md invariant blocks, else doctrine slice
    sources = [plane.repo / "REPO.md", plane.repo / "ROLE.md"]
    inv = "\n\n".join(_extract_sections(p.read_text("utf-8"), ["Invariant"])
                      for p in sources if p.exists()).strip()
    if not inv:
        doctrine = plane.repo / ".Doctrine.md"
        if doctrine.exists():
            inv = _extract_sections(doctrine.read_text("utf-8"),
                                    ["Prime Directive", "Non-Negotiables"])
    text, _ = _clip(inv or "(no invariant source found)", BUDGETS[0][1])
    parts.append("## Invariants\n" + text)

    # 2 control
    control = dict(cp["control"])
    control_line = (f"seq={cp['seq']} at_commit={cp['at_commit'][:12]} "
                    f"worktree={cp['worktree']} role={control['role']} "
                    f"phase={control['phase']} "
                    f"ponytail={control['ponytail_mode']} "
                    f"gates={','.join(control.get('gates_passed', [])) or '-'}")
    parts.append("## Control\n" + control_line)

    # 3 active intents
    lines = []
    for intent in control.get("active_intents", []):
        p = plane.intents / f"{intent}.intent.json"
        if not p.exists():
            lines.append(f"- {intent}: MISSING intent file")
            continue
        data = json.loads(p.read_text("utf-8"))
        prefix = _stale_prefix(data.get("at_commit"), head, stale,
                               f"intent:{intent}")
        title = data.get("title", intent)
        acc = data.get("acceptance_criteria", [])
        lines.append(f"- {prefix}**{intent}** — {title}")
        lines.extend(f"  - AC: {a}" for a in acc)
    text, was = _clip("\n".join(lines) or "(no active intents)",
                      BUDGETS[2][1])
    if was:
        trimmed.append("intents")
    parts.append("## Active intents\n" + text)

    # 4 distillate (+ merged dead_ends already live in the latest one)
    dists = _distillate_files(plane)
    if dists:
        d = json.loads(dists[-1].read_text("utf-8"))
        prefix = _stale_prefix(d.get("at_commit"), head, stale, "distillate")
        seg = [f"{prefix}(distillate seq {d['seq']})"]
        for item in d.get("learned", []):
            seg.append(f"- [{item['kind']}/{item['confidence']}] "
                       f"{item['claim']} (evidence: {item['evidence']})")
        seg.append("Dead ends:")
        seg.extend(f"- {e['approach']} → {e['why_failed']}"
                   for e in d.get("dead_ends", []))
        seg.append("Open threads:")
        seg.extend(f"- {t}" for t in d.get("open_threads", []))
        seg.append("Next actions:")
        seg.extend(f"- {n}" for n in d.get("next_actions", []))
        text, was = _clip("\n".join(seg), BUDGETS[3][1])
        if was:
            trimmed.append("distillate")
    else:
        text = "(no distillates)"
    parts.append("## Distillate\n" + text)

    # 5 decisions slice — entries tagged to the active intents
    active = set(control.get("active_intents", []))
    lines = []
    if plane.decisions.exists():
        for raw in plane.decisions.read_text("utf-8").splitlines():
            if not raw.strip():
                continue
            entry = json.loads(raw)
            if not active or active & set(entry.get("intents", [])):
                lines.append(f"- (seq {entry['seq']}) {entry['claim']} "
                             f"[{entry['evidence']}]")
    text, was = _clip("\n".join(lines) or "(no matching decisions)",
                      BUDGETS[4][1])
    if was:
        trimmed.append("decisions")
    parts.append("## Decisions\n" + text)

    # 6 graph slice
    report = plane.repo / "graphify-out" / "GRAPH_REPORT.md"
    if report.exists():
        built = cp["state_index"]["graph"].get("built_at_commit")
        prefix = _stale_prefix(built, head, stale, "graph")
        text, was = _clip(prefix + report.read_text("utf-8"), BUDGETS[5][1])
        if was:
            trimmed.append("graph")
    else:
        text = "(no graph built)"
    parts.append("## Graph\n" + text)

    # 7 unresolved effects
    count = _unresolved_effects(plane)
    text, _ = _clip(f"unresolved effects: {count}", BUDGETS[6][1])
    parts.append("## Unresolved effects\n" + text)

    body = "\n\n".join(parts) + "\n"
    return body, trimmed, stale


def cmd_hydrate(plane: Plane, check: bool = False) -> int:
    if not plane.checkpoint.exists():
        print("no checkpoint.json — run checkpoint first", file=sys.stderr)
        return 1
    body1, trimmed, stale = build_bundle_body(plane)
    sha1 = sha256_bytes(body1.encode("utf-8"))
    if check:
        body2, _, _ = build_bundle_body(plane)
        sha2 = sha256_bytes(body2.encode("utf-8"))
        if sha1 != sha2:
            print(f"DETERMINISM FAILED: {sha1[:12]} != {sha2[:12]}")
            return 1
        print(f"hydrate --check OK: bundle_sha256 {sha1[:12]} stable")
        return 0

    cp = json.loads(plane.checkpoint.read_text("utf-8"))
    header = canonical_line({
        "at_commit": cp["at_commit"], "bundle_sha256": sha1,
        "checkpoint_seq": cp["seq"], "generated_at": now_utc(),
        "stale": sorted(stale), "trimmed": sorted(trimmed),
    })
    plane.local.mkdir(parents=True, exist_ok=True)
    out = plane.local / "hydration.bundle.md"
    out.write_bytes((f"<!-- doctrine:hydration {header} -->\n\n" + body1)
                    .encode("utf-8"))
    print(f"bundle written: {out} ({len(body1) // TOKEN_CHARS} tokens est., "
          f"sha {sha1[:12]}"
          + (f", trimmed: {','.join(trimmed)}" if trimmed else "")
          + (f", STALE: {','.join(stale)}" if stale else "") + ")")
    return 0


def cmd_prune(plane: Plane, keep: int) -> int:
    files = _distillate_files(plane)
    victims = files[:-keep] if keep >= 1 and len(files) > keep else []
    if not victims:
        print(f"nothing to prune ({len(files)} ≤ keep {keep})")
        return 0
    print(f"pruning {len(victims)} distillate(s); their dead_ends will "
          "merge into the NEXT checkpoint's distillate:")
    ends, _ = _merge_dead_ends([], victims, cap=10 ** 6)
    pending = plane.distillates / "pending-dead-ends.json"
    pending.write_bytes(canonical_bytes({"dead_ends": ends}))
    for f in victims:
        print(f"  - {f.name}")
        f.unlink()
    print(f"merged negatives staged in {pending.name}")
    return 0


def cmd_status(plane: Plane) -> int:
    if not plane.checkpoint.exists():
        print("no state plane (run: init, then checkpoint)")
        return 0
    cp = json.loads(plane.checkpoint.read_text("utf-8"))
    dists = _distillate_files(plane)
    print(f"checkpoint seq {cp['seq']} @ {cp['at_commit'][:12]} "
          f"({cp['worktree']}) session {cp['session_id']}")
    print(f"role={cp['control']['role']} phase={cp['control']['phase']} "
          f"intents={','.join(cp['control']['active_intents']) or '-'}")
    print(f"distillates: {len(dists)} · unresolved effects: "
          f"{cp['state_index']['unresolved_effects']}")
    return 0


# -------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doctrine_state",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="repo root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    p_cp = sub.add_parser("checkpoint")
    p_cp.add_argument("--proposal", type=Path, required=True)
    p_cp.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    sub.add_parser("verify")
    p_hy = sub.add_parser("hydrate")
    p_hy.add_argument("--check", action="store_true")
    p_pr = sub.add_parser("prune")
    p_pr.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    sub.add_parser("status")
    args = parser.parse_args(argv)

    plane = Plane(args.root.resolve())
    try:
        if args.command == "init":
            return cmd_init(plane)
        if args.command == "checkpoint":
            return cmd_checkpoint(plane, args.proposal, args.keep)
        if args.command == "verify":
            return cmd_verify(plane)
        if args.command == "hydrate":
            return cmd_hydrate(plane, args.check)
        if args.command == "prune":
            return cmd_prune(plane, args.keep)
        if args.command == "status":
            return cmd_status(plane)
    except SchemaError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"git failed: {exc.stderr.strip()}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

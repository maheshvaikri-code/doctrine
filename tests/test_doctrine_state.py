"""Tests for tools/doctrine_state.py — run: python -m unittest discover tests"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import doctrine_state as ds  # noqa: E402

SCHEMAS = REPO / ".Doctrine" / "state-plane" / "schemas"
EXAMPLES = REPO / ".Doctrine" / "state-plane" / "examples"


def proposal(dead_ends=None, learned=None):
    return {
        "session_id": "s-test-1",
        "control": {"role": "backend-engineer", "phase": "g3",
                    "ponytail_mode": "off", "active_intents": [],
                    "gates_passed": []},
        "distillate": {
            "task_refs": ["t-1"],
            "learned": learned if learned is not None else [
                {"claim": "canonical writer is stable", "kind": "fact",
                 "evidence": "tests/test_doctrine_state.py:1",
                 "confidence": "verified"}],
            "dead_ends": dead_ends or [], "open_threads": [],
            "next_actions": []},
    }


class TempRepo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"],
                       cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "t"],
                       cwd=self.root, check=True)
        (self.root / "seed.txt").write_text("seed\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=self.root,
                       check=True)
        dest = self.root / ".Doctrine" / "state-plane" / "schemas"
        dest.mkdir(parents=True)
        for f in SCHEMAS.glob("*.json"):
            shutil.copy(f, dest / f.name)
        self.plane = ds.Plane(self.root)
        ds.cmd_init(self.plane)

    def tearDown(self):
        self._tmp.cleanup()

    def checkpoint(self, prop=None, keep=5):
        p = self.root / "proposal.json"
        p.write_text(json.dumps(prop or proposal()), encoding="utf-8")
        return ds.cmd_checkpoint(self.plane, p, keep=keep)


class TestCanonical(unittest.TestCase):
    def test_sorted_lf_single_newline_no_trailing_ws(self):
        raw = ds.canonical_bytes({"b": 1, "a": {"z": [1, 2], "y": None}})
        text = raw.decode("utf-8")
        self.assertTrue(text.endswith("\n"))
        self.assertFalse(text.endswith("\n\n"))
        self.assertNotIn("\r", text)
        self.assertLess(text.index('"a"'), text.index('"b"'))
        for line in text.splitlines():
            self.assertEqual(line, line.rstrip(), "trailing whitespace")

    def test_stable(self):
        obj = json.loads((EXAMPLES / "checkpoint.example.json")
                         .read_text("utf-8"))
        self.assertEqual(ds.canonical_bytes(obj), ds.canonical_bytes(obj))


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.cp_schema = json.loads(
            (SCHEMAS / "checkpoint.schema.json").read_text("utf-8"))
        self.di_schema = json.loads(
            (SCHEMAS / "distillate.schema.json").read_text("utf-8"))
        self.cp = json.loads(
            (EXAMPLES / "checkpoint.example.json").read_text("utf-8"))
        self.di = json.loads(
            (EXAMPLES / "distillate.example.json").read_text("utf-8"))

    def test_examples_validate(self):
        ds.validate(self.cp, self.cp_schema)
        ds.validate(self.di, self.di_schema)

    def test_missing_required(self):
        bad = dict(self.cp)
        del bad["seq"]
        with self.assertRaises(ds.SchemaError):
            ds.validate(bad, self.cp_schema)

    def test_unknown_field_rejected(self):
        bad = dict(self.cp, extra_field=1)
        with self.assertRaises(ds.SchemaError):
            ds.validate(bad, self.cp_schema)

    def test_max_items(self):
        bad = dict(self.di)
        bad["dead_ends"] = [{"approach": "a", "why_failed": "b"}] * 9
        with self.assertRaises(ds.SchemaError):
            ds.validate(bad, self.di_schema)

    def test_bad_pattern(self):
        bad = dict(self.cp, at_commit="NOTHEX")
        with self.assertRaises(ds.SchemaError):
            ds.validate(bad, self.cp_schema)

    def test_enum(self):
        bad = json.loads(json.dumps(self.cp))
        bad["worktree"] = "messy"
        with self.assertRaises(ds.SchemaError):
            ds.validate(bad, self.cp_schema)


class TestCheckpointVerify(TempRepo):
    def test_chain_and_verify(self):
        self.assertEqual(self.checkpoint(), 0)
        self.assertEqual(ds.cmd_verify(self.plane), 0)
        self.assertEqual(self.checkpoint(), 0)
        self.assertEqual(ds.cmd_verify(self.plane), 0)
        cp = json.loads(self.plane.checkpoint.read_text("utf-8"))
        self.assertEqual(cp["seq"], 1)
        self.assertIsNotNone(cp["prev_sha256"])

    def test_tamper_detected(self):
        self.checkpoint()
        self.checkpoint()
        victim = sorted(self.plane.checkpoints.glob("0-*.json"))[0]
        data = json.loads(victim.read_text("utf-8"))
        data["session_id"] = "forged"
        victim.write_bytes(ds.canonical_bytes(data))
        self.assertEqual(ds.cmd_verify(self.plane), 1)

    def test_decisions_written_and_indexed(self):
        prop = proposal(learned=[
            {"claim": "exit codes mirror gate semantics",
             "kind": "decision_ref", "evidence": "decisions:D-1",
             "confidence": "verified"}])
        self.checkpoint(prop)
        self.assertTrue(self.plane.decisions.exists())
        self.assertEqual(ds.cmd_verify(self.plane), 0)

    def test_invalid_proposal_rejected(self):
        prop = proposal()
        prop["distillate"]["learned"][0]["confidence"] = "hopeful"
        p = self.root / "bad.json"
        p.write_text(json.dumps(prop), encoding="utf-8")
        with self.assertRaises(ds.SchemaError):
            ds.cmd_checkpoint(self.plane, p)
        self.assertFalse(self.plane.checkpoint.exists(),
                         "nothing written on validation failure")


class TestPrune(TempRepo):
    def test_dead_ends_merge_forward(self):
        for i in range(3):
            self.checkpoint(proposal(dead_ends=[
                {"approach": f"approach-{i}", "why_failed": f"reason-{i}"}]),
                keep=2)
        dists = ds._distillate_files(self.plane)
        self.assertLessEqual(len(dists), 2)
        latest = json.loads(dists[-1].read_text("utf-8"))
        approaches = {e["approach"] for e in latest["dead_ends"]}
        self.assertIn("approach-0", approaches,
                      "pruned negatives must outlive the prune")
        self.assertIn("approach-2", approaches)

    def test_keep_one(self):
        self.checkpoint(keep=1)
        self.checkpoint(keep=1)
        self.assertEqual(len(ds._distillate_files(self.plane)), 1)

    def test_manual_prune_stages_pending(self):
        for i in range(3):
            self.checkpoint(proposal(dead_ends=[
                {"approach": f"a-{i}", "why_failed": "r"}]))
        self.assertEqual(ds.cmd_prune(self.plane, keep=1), 0)
        pending = self.plane.distillates / "pending-dead-ends.json"
        self.assertTrue(pending.exists())
        self.checkpoint()
        self.assertFalse(pending.exists(), "pending consumed by checkpoint")
        latest = json.loads(
            ds._distillate_files(self.plane)[-1].read_text("utf-8"))
        self.assertIn("a-0", {e["approach"] for e in latest["dead_ends"]})


class TestHydrate(TempRepo):
    def test_deterministic_and_written(self):
        self.checkpoint()
        self.assertEqual(ds.cmd_hydrate(self.plane, check=True), 0)
        self.assertEqual(ds.cmd_hydrate(self.plane), 0)
        bundle = self.plane.local / "hydration.bundle.md"
        text = bundle.read_text("utf-8")
        self.assertIn("doctrine:hydration", text)
        self.assertIn("## Control", text)
        header = json.loads(text.split("doctrine:hydration ", 1)[1]
                            .split(" -->", 1)[0])
        body = text.split("-->\n\n", 1)[1]
        self.assertEqual(header["bundle_sha256"],
                         ds.sha256_bytes(body.encode("utf-8")))

    def test_no_checkpoint_errors(self):
        self.assertEqual(ds.cmd_hydrate(self.plane), 1)


if __name__ == "__main__":
    unittest.main()

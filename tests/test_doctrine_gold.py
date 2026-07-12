"""Tests for tools/doctrine_gold.py — run: python -m unittest discover tests"""

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

import doctrine_gold as dg  # noqa: E402
import doctrine_state as ds  # noqa: E402


class GoldRepo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"],
                       cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "t"],
                       cwd=self.root, check=True)
        # schema in place
        dest = self.root / ".Doctrine" / "schemas"
        dest.mkdir(parents=True)
        shutil.copy(REPO / ".Doctrine" / "schemas" /
                    "gold-build.schema.json", dest)
        # verdict, sign-offs, artifact
        for rel in ("docs/merges/task.md", "docs/reviews/task.md",
                    "docs/qa/task-security.md", "docs/qa/task.md",
                    "docs/reviews/task-scope.md"):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# {rel}\nUNANIMOUS/SIGN-OFF\n", encoding="utf-8")
        (self.root / "dist").mkdir()
        (self.root / "dist" / "app.whl").write_bytes(b"artifact-bytes-v1")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=self.root,
                       check=True)
        subprocess.run(["git", "tag", "-a", "v1.0.0", "-m", "v1"],
                       cwd=self.root, check=True)

    def tearDown(self):
        self._tmp.cleanup()

    def proposal(self, tag="v1.0.0", **overrides):
        base = {
            "tag": tag,
            "merge_verdict": "docs/merges/task.md",
            "signoffs": {
                "code_review": "docs/reviews/task.md",
                "security": "docs/qa/task-security.md",
                "qa": "docs/qa/task.md",
                "project_review": "docs/reviews/task-scope.md",
            },
            "artifacts": [{"path": "dist/app.whl", "sha256": "0" * 64}],
            "soak": {"environment": "staging", "result": "pass",
                     "evidence": "make smoke on staging - exit 0"},
            "human_approval": {"approved_by": "Mahesh Vaikri",
                               "date": "2026-07-12",
                               "statement": "go for v1.0.0"},
        }
        base.update(overrides)
        return base

    def record(self, proposal=None):
        p = self.root / "gold-proposal.json"
        p.write_text(json.dumps(proposal or self.proposal()),
                     encoding="utf-8")
        return dg.cmd_record(self.root, p)


class TestRecordAndCheck(GoldRepo):
    def test_happy_path(self):
        self.assertEqual(self.record(), 0)
        out = self.root / "docs" / "releases" / "gold" / "v1.0.0.json"
        self.assertTrue(out.exists())
        record = json.loads(out.read_text("utf-8"))
        self.assertIsNone(record["prev_gold_sha256"])
        self.assertEqual(record["artifacts"][0]["sha256"],
                         ds.sha256_file(self.root / "dist" / "app.whl"))
        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 0)

    def test_artifact_tamper_fails_check(self):
        self.record()
        (self.root / "dist" / "app.whl").write_bytes(b"tampered")
        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 1)

    def test_record_tamper_fails_check(self):
        self.record()
        out = self.root / "docs" / "releases" / "gold" / "v1.0.0.json"
        record = json.loads(out.read_text("utf-8"))
        record["soak"]["environment"] = "forged"
        out.write_bytes(ds.canonical_bytes(record))
        # canonical rewrite passes schema; chain check on the NEXT record
        # catches it — verify via a second record whose prev hash was
        # computed pre-tamper.
        subprocess.run(["git", "tag", "-a", "v1.0.1", "-m", "v"],
                       cwd=self.root, check=True)
        pre_tamper_ok = self.record(self.proposal(tag="v1.0.1"))
        self.assertEqual(pre_tamper_ok, 0)
        record["soak"]["environment"] = "forged-again"
        out.write_bytes(ds.canonical_bytes(record))
        self.assertEqual(dg.cmd_check(self.root, "v1.0.1"), 1)

    def test_chain_links_records(self):
        self.record()
        first = self.root / "docs" / "releases" / "gold" / "v1.0.0.json"
        subprocess.run(["git", "tag", "-a", "v1.1.0", "-m", "v"],
                       cwd=self.root, check=True)
        self.assertEqual(self.record(self.proposal(tag="v1.1.0")), 0)
        second = json.loads(
            (self.root / "docs" / "releases" / "gold" / "v1.1.0.json")
            .read_text("utf-8"))
        self.assertEqual(second["prev_gold_sha256"], ds.sha256_file(first))
        self.assertEqual(dg.cmd_check(self.root, "v1.1.0"), 0)

    def test_missing_signoff_refused(self):
        (self.root / "docs" / "qa" / "task-security.md").unlink()
        with self.assertRaises(dg.StateError):
            self.record()
        self.assertFalse((self.root / "docs" / "releases").exists(),
                         "nothing written on refusal")

    def test_missing_verdict_refused(self):
        (self.root / "docs" / "merges" / "task.md").unlink()
        with self.assertRaises(dg.StateError):
            self.record()

    def test_empty_human_approval_refused(self):
        prop = self.proposal()
        prop["human_approval"]["statement"] = ""
        with self.assertRaises(dg.SchemaError):
            self.record(prop)

    def test_path_escape_refused(self):
        prop = self.proposal()
        prop["signoffs"]["security"] = "../outside.md"
        with self.assertRaises(dg.StateError):
            self.record(prop)

    def test_immutable_records(self):
        self.record()
        with self.assertRaises(dg.StateError):
            self.record()

    def test_unknown_tag_refused(self):
        prop = self.proposal(tag="v9.9.9")
        with self.assertRaises(
                (dg.StateError, subprocess.CalledProcessError)):
            self.record(prop)

    def test_moved_tag_fails_check(self):
        self.record()
        (self.root / "new.txt").write_text("x\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "advance"], cwd=self.root,
                       check=True)
        subprocess.run(["git", "tag", "-fa", "v1.0.0", "-m", "moved"],
                       cwd=self.root, check=True)
        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 1)

    def test_check_without_record_fails(self):
        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 1)


if __name__ == "__main__":
    unittest.main()

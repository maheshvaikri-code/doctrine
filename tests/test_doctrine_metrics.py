"""Tests for tools/doctrine_metrics.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import doctrine_metrics as dm  # noqa: E402


class TestEnrich(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"],
                       cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "t"],
                       cwd=self.root, check=True)
        (self.root / "a.txt").write_text("a\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "first"], cwd=self.root,
                       check=True)
        self.sha = subprocess.run(["git", "rev-parse", "HEAD"],
                                  cwd=self.root, capture_output=True,
                                  text=True, check=True).stdout.strip()

    def tearDown(self):
        self._tmp.cleanup()

    def write_review(self, text: str) -> None:
        p = self.root / "docs" / "reviews" / "task.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_real_commit_extracted_bogus_ignored(self):
        self.write_review(
            f"Reviewed at {self.sha[:12]}. Bogus: abcdef1234567890abcd. "
            "A sha256 that must NOT match: " + "ab" * 32 + ".\n")
        self.assertEqual(dm.cmd_enrich(self.root, ["docs/reviews"],
                                       dm.DEFAULT_OUT), 0)
        entries = json.loads(
            (self.root / dm.DEFAULT_OUT).read_text("utf-8"))
        self.assertEqual(entries,
                         [{"id": self.sha, "human_reviewed": True}])

    def test_unreachable_commit_ignored(self):
        subprocess.run(["git", "checkout", "-qb", "side"], cwd=self.root,
                       check=True)
        (self.root / "b.txt").write_text("b\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "side"], cwd=self.root,
                       check=True)
        side = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
        subprocess.run(["git", "checkout", "-q", "-"], cwd=self.root,
                       check=True)
        self.write_review(f"Mentions side-branch commit {side}.\n")
        dm.cmd_enrich(self.root, ["docs/reviews"], dm.DEFAULT_OUT)
        entries = json.loads(
            (self.root / dm.DEFAULT_OUT).read_text("utf-8"))
        self.assertEqual(entries, [], "unreachable commits must not count")

    def test_no_artifacts_is_a_clean_refusal(self):
        self.assertEqual(dm.cmd_enrich(self.root, ["docs/reviews"],
                                       dm.DEFAULT_OUT), 1)
        self.assertFalse((self.root / dm.DEFAULT_OUT).exists())

    def test_not_a_git_repo_refused(self):
        with tempfile.TemporaryDirectory() as bare:
            with self.assertRaises(dm.StateError):
                dm.cmd_enrich(Path(bare), ["docs/reviews"],
                              dm.DEFAULT_OUT)


class TestVerdictClassifier(unittest.TestCase):
    def test_verdict_lines_classified(self):
        cases = {
            "## Delta verdict (v0.5.0): REQUEST-CHANGES":
                "REQUEST-CHANGES",
            "## Re-audit verdict: SIGN-OFF (cleared)": "SIGN-OFF",
            "Final delta verdict: APPROVE-WITH-NITS":
                "APPROVE-WITH-NITS",
            "**Final verdict: PASS.**": "PASS",
            "VERDICT: VETO (deploy gate blocked)": "VETO",
        }
        for line, want in cases.items():
            self.assertEqual(dm.classify_verdict_line(line), want, line)

    def test_prose_and_tool_output_not_counted(self):
        for line in ("Security Reviewer holds the ship veto.",
                     "CHECK FAILED (3) - do not deploy v1.0.0:",
                     "VERIFY FAILED (1):",
                     "the tests pass locally"):
            self.assertIsNone(dm.classify_verdict_line(line), line)


class TestGates(TestEnrich):
    def tag(self, name):
        subprocess.run(["git", "tag", "-a", name, "-m", name],
                       cwd=self.root, check=True)

    def test_per_release_verdict_mining(self):
        self.tag("v0.1.0")
        self.write_review(
            "## Delta verdict (task): REQUEST-CHANGES\n"
            "later...\n## Final verdict: APPROVE\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "docs: review"],
                       cwd=self.root, check=True)
        self.tag("v0.2.0")
        out = Path("docs") / "metrics" / "gates.md"
        self.assertEqual(dm.cmd_gates(self.root, out), 0)
        report = (self.root / out).read_text("utf-8")
        self.assertIn("| v0.2.0 |", report)
        self.assertIn("APPROVE:1", report)
        self.assertIn("REQUEST-CHANGES:1", report)

    def test_needs_two_tags(self):
        self.tag("v0.1.0")
        self.assertEqual(dm.cmd_gates(self.root, None), 1)


if __name__ == "__main__":
    unittest.main()

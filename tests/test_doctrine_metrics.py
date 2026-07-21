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

    def test_mark_authorship_blankets_all_commits(self):
        """Post-trailer-strip provenance: every HEAD-reachable commit
        gets the asserted authorship; reviewed flags are preserved."""
        self.write_review(f"Reviewed at {self.sha[:12]}.\n")
        self.assertEqual(dm.cmd_enrich(self.root, ["docs/reviews"],
                                       dm.DEFAULT_OUT,
                                       mark_authorship="agent_assisted"), 0)
        entries = json.loads(
            (self.root / dm.DEFAULT_OUT).read_text("utf-8"))
        self.assertEqual(len(entries), 1)  # one commit in this repo
        self.assertEqual(entries[0]["authorship"], "agent_assisted")
        self.assertEqual(entries[0]["agent_name"], "claude")
        self.assertTrue(entries[0]["human_reviewed"])
        with self.assertRaises(dm.StateError):
            dm.cmd_enrich(self.root, ["docs/reviews"], dm.DEFAULT_OUT,
                          mark_authorship="robot_overlord")

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


class TestCaptureHint(unittest.TestCase):
    def run_hint(self, root: Path, env_extra: dict) -> str:
        import os
        env = {k: v for k, v in os.environ.items()
               if k not in ("OTEL_EXPORTER_OTLP_ENDPOINT",
                            "ANTHROPIC_BASE_URL")}
        env.update(env_extra)
        out = subprocess.run(
            [sys.executable, str(REPO / "tools" / "doctrine_metrics.py"),
             "--root", str(root), "capture-hint"],
            capture_output=True, text=True, env=env)
        self.assertEqual(out.returncode, 0, "a hint is never a gate")
        return out.stderr

    def test_hints_when_adopted_and_uncaptured(self):
        self.assertIn("NOT being captured", self.run_hint(REPO, {}))

    def test_silent_when_captured(self):
        self.assertEqual(self.run_hint(REPO, {
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:4318"}), "")

    def test_silent_when_not_adopted(self):
        with tempfile.TemporaryDirectory() as bare:
            self.assertEqual(self.run_hint(Path(bare), {}), "")


class TestBudget(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_budget(self, **kw) -> tuple[int, str]:
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = dm.cmd_budget(self.root, kw.get("cap"), kw.get("spent"),
                                 kw.get("log"))
        return code, out.getvalue()

    def test_under_cap_ok(self):
        code, msg = self.run_budget(cap=1000, spent=200)
        self.assertEqual(code, 0)
        self.assertIn("budget ok", msg)

    def test_warn_near_cap(self):
        code, msg = self.run_budget(cap=1000, spent=850)
        self.assertEqual(code, 0)
        self.assertIn("warning", msg)

    def test_over_cap_escalates(self):
        code, msg = self.run_budget(cap=1000, spent=1200)
        self.assertEqual(code, 1, "over-cap must signal an escalation")
        self.assertIn("BUDGET EXCEEDED", msg)
        self.assertIn("Section 5", msg)

    def test_no_telemetry_is_not_a_breach(self):
        # no --spent and no log present -> exits 0 with a launch hint
        code, msg = self.run_budget(cap=1000)
        self.assertEqual(code, 0)
        self.assertIn("no token telemetry", msg)

    def test_nonpositive_cap_refused(self):
        with self.assertRaises(dm.StateError):
            self.run_budget(cap=0, spent=10)

    def test_sum_tokens_defensive_parse(self):
        log = self.root / "codemonk_tokens.jsonl"
        log.write_text(
            json.dumps({"total_tokens": 100}) + "\n"
            + json.dumps({"tokens": 50}) + "\n"
            + json.dumps({"usage": {"total_tokens": 25}}) + "\n"
            + "not json at all\n"
            + json.dumps(["a", "list", "not", "a", "dict"]) + "\n"
            + json.dumps({"unrelated": "field"}) + "\n"
            + json.dumps({"tokens": True}) + "\n",  # bool must not count
            encoding="utf-8")
        self.assertEqual(dm._sum_tokens(log), 175)

    def test_log_path_summed_and_gated(self):
        log = self.root / "toks.jsonl"
        log.write_text(json.dumps({"total_tokens": 1500}) + "\n",
                       encoding="utf-8")
        code, msg = self.run_budget(cap=1000, log=log)
        self.assertEqual(code, 1)
        self.assertIn("1500", msg)


if __name__ == "__main__":
    unittest.main()

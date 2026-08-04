"""Tests for tools/doctrine_verify.py — source-vs-consumer gate scoping.

Regression for the ADR-002 defect: in a consumer repo (a host repo with
its own code), doctrine_verify must NOT ruff the host's files or run the
host's test suite; it verifies only Doctrine's own surface (lint + state).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import doctrine_verify as dv  # noqa: E402


class TestSourceDetection(unittest.TestCase):
    def test_doctrineos_pyproject_is_source(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text(
                '[project]\nname="doctrineos"\n', encoding="utf-8")
            self.assertTrue(dv.is_source_repo(Path(d)))

    def test_doctrineos_text_in_comment_is_not_source(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text(
                '[project]\nname = "host"\n'
                '# example: name = "doctrineos"\n', encoding="utf-8")
            self.assertFalse(dv.is_source_repo(Path(d)))

    def test_doctrineos_name_in_other_table_is_not_source(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text(
                '[project]\nname = "host"\n'
                '[tool.example]\nname = "doctrineos"\n', encoding="utf-8")
            self.assertFalse(dv.is_source_repo(Path(d)))

    def test_no_pyproject_is_consumer(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(dv.is_source_repo(Path(d)))

    def test_other_pyproject_is_consumer(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text(
                '[project]\nname = "maple-oss"\n', encoding="utf-8")
            self.assertFalse(dv.is_source_repo(Path(d)))


class TestGateScoping(unittest.TestCase):
    def _run(self, root: Path):
        ran: list[str] = []

        def fake_gate(name, cmd, cwd):
            ran.append(name)
            return True

        with mock.patch.object(dv, "run_gate", fake_gate):
            rc = dv.main([str(root)])
        return rc, ran

    def test_consumer_runs_only_doctrine_surface(self):
        # no pyproject => consumer; no state plane => state skipped.
        with tempfile.TemporaryDirectory() as d:
            rc, ran = self._run(Path(d))
        self.assertEqual(rc, 0)
        self.assertEqual(ran, ["lint"])  # NOT ruff, NOT the host test suite

    def test_consumer_still_verifies_state_when_present(self):
        with tempfile.TemporaryDirectory() as d:
            sp = Path(d) / ".doctrine-state"
            sp.mkdir()
            (sp / "checkpoint.json").write_text("{}", encoding="utf-8")
            rc, ran = self._run(Path(d))
        self.assertEqual(ran, ["lint", "state"])
        self.assertNotIn("tests", ran)

    def test_source_runs_full_suite(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text(
                '[project]\nname = "doctrineos"\n', encoding="utf-8")
            rc, ran = self._run(Path(d))
        self.assertIn("lint", ran)
        self.assertIn("tests", ran)  # the doctrine dev suite runs in source

    def test_source_fails_when_required_ruff_is_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text(
                '[project]\nname = "doctrineos"\n', encoding="utf-8")
            with mock.patch.object(dv, "ruff_available", return_value=False):
                rc, ran = self._run(Path(d))
        self.assertEqual(rc, 1)
        self.assertEqual(ran, ["lint", "tests"])


class TestGoldGating(unittest.TestCase):
    """Regression: `doctrine_verify` deciding whether to invoke the gold
    gate at all, independent of what the gate itself then decides."""

    def _git(self, cwd: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=cwd, check=True,
                       capture_output=True)

    def _make_repo(self, root: Path) -> None:
        self._git(root, "init", "-q")
        self._git(root, "config", "user.email", "t@example.invalid")
        self._git(root, "config", "user.name", "t")
        gold = root / "docs" / "releases" / "gold"
        gold.mkdir(parents=True)
        (gold / "v1.0.0.json").write_text("{}", encoding="utf-8")
        self._git(root, "add", "-A")
        self._git(root, "commit", "-qm", "seed")

    def test_a_non_git_directory_does_not_force_the_gold_gate(self):
        """A plain directory with no .git has no history to hide anything
        in; running the gate there is noise, not safety."""
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(dv.git_knows_gold(Path(d)))

    def test_history_survives_a_staged_but_uncommitted_removal(self):
        """Regression: the previous check read the INDEX (`git ls-files`),
        which a staged `git rm` empties before any commit exists. `git log`
        reads history, which the staging area cannot erase."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._make_repo(root)
            self._git(root, "rm", "-r", "-q", "docs/releases/gold")

            self.assertTrue(dv.git_knows_gold(root))

    def test_history_survives_a_committed_relocation(self):
        """Regression: `git mv docs/releases lib && git commit` removes the
        gold directory from HEAD's tree in the very commit that relocates
        it; only history (not the current tree) still shows it existed."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._make_repo(root)
            self._git(root, "mv", "docs/releases", "lib")
            self._git(root, "commit", "-qm", "reorganize")

            self.assertTrue(dv.git_knows_gold(root))

    def test_a_repo_that_never_tracked_gold_reports_false(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._git(root, "init", "-q")
            self._git(root, "config", "user.email", "t@example.invalid")
            self._git(root, "config", "user.name", "t")
            (root / "README.md").write_text("x", encoding="utf-8")
            self._git(root, "add", "-A")
            self._git(root, "commit", "-qm", "seed")

            self.assertFalse(dv.git_knows_gold(root))


if __name__ == "__main__":
    unittest.main()

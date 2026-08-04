"""Tests for the cross-repo fleet view.

The load-bearing property is that inspection is READ-ONLY: a status command
that mutated a governed repo would be worse than no view at all.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import doctrine_fleet as fleet  # noqa: E402


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _make_source(root: Path, version: str = "0.7.0") -> None:
    (root / ".Doctrine.md").write_text(
        f"# .Doctrine.md - Engineering Doctrine v{version}\n", encoding="utf-8")
    (root / ".Doctrine").mkdir(exist_ok=True)
    (root / ".Doctrine" / "README.md").write_text("corpus\n", encoding="utf-8")
    (root / "tools").mkdir(exist_ok=True)
    (root / "tools" / "doctrine_install.py").write_text(
        "# installer\n", encoding="utf-8")


def _make_repo(root: Path, version: str = "0.7.0", *, git: bool = True) -> None:
    _make_source(root, version)
    if git:
        _git(root, "init", "-q")
        _git(root, "config", "user.email", "t@example.invalid")
        _git(root, "config", "user.name", "Fleet Test")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "seed")
        _git(root, "tag", "-a", f"v{version}", "-m", "release")


def _tree_digest(root: Path) -> str:
    """A fingerprint of every file under root - path, size and bytes."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


class FleetTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.source = self.workspace / "source"
        self.source.mkdir()
        _make_source(self.source)

    def _repo(self, name: str, version: str = "0.7.0", **kwargs) -> Path:
        path = self.workspace / name
        path.mkdir()
        _make_repo(path, version, **kwargs)
        return path


class TestInspection(FleetTestCase):
    def test_a_matching_install_reports_current(self) -> None:
        repo = self._repo("app")

        row = fleet.inspect(repo, self.source, "0.7.0")

        self.assertEqual(row["doctrineVersion"], "0.7.0")
        self.assertEqual(row["drift"], "current")
        self.assertEqual(row["worktree"], "clean")
        self.assertEqual(row["state"], "none")
        self.assertEqual(row["release"], "v0.7.0")
        self.assertEqual(row["goldRecords"], 0)

    def test_an_older_install_reports_how_far_behind(self) -> None:
        repo = self._repo("legacy", version="0.6.29")

        row = fleet.inspect(repo, self.source, "0.7.0")

        self.assertEqual(row["drift"], "behind v0.7.0")

    def test_a_newer_install_reports_ahead(self) -> None:
        repo = self._repo("future", version="0.8.0")

        self.assertEqual(fleet.inspect(repo, self.source, "0.7.0")["drift"],
                         "ahead")

    def test_a_locally_edited_corpus_reports_modified(self) -> None:
        """Same version, different bytes - the drift that lint later trips on."""
        repo = self._repo("edited")
        (repo / ".Doctrine" / "README.md").write_text("hand-edited\n",
                                                      encoding="utf-8")

        self.assertEqual(fleet.inspect(repo, self.source, "0.7.0")["drift"],
                         "modified")

    def test_a_missing_carrier_reports_incomplete(self) -> None:
        repo = self._repo("partial")
        (repo / "tools" / "doctrine_install.py").unlink()

        self.assertEqual(fleet.inspect(repo, self.source, "0.7.0")["drift"],
                         "incomplete")

    def test_dirty_worktrees_and_release_distance_are_reported(self) -> None:
        repo = self._repo("busy")
        (repo / "notes.txt").write_text("uncommitted\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "work past the tag")
        (repo / "more.txt").write_text("still uncommitted\n", encoding="utf-8")

        row = fleet.inspect(repo, self.source, "0.7.0")

        self.assertEqual(row["worktree"], "dirty")
        self.assertEqual(row["release"], "v0.7.0 +1")

    def test_state_and_gold_posture_are_read_from_disk(self) -> None:
        repo = self._repo("stateful")
        (repo / ".doctrine-state").mkdir()
        (repo / ".doctrine-state" / "checkpoint.json").write_text(
            json.dumps({"seq": 24}), encoding="utf-8")
        gold = repo / "docs" / "releases" / "gold"
        gold.mkdir(parents=True)
        (gold / "v0.7.0.json").write_text("{}", encoding="utf-8")

        row = fleet.inspect(repo, self.source, "0.7.0")

        self.assertEqual(row["state"], "seq 24")
        self.assertEqual(row["goldRecords"], 1)

    def test_a_corrupt_checkpoint_is_reported_not_raised(self) -> None:
        repo = self._repo("corrupt")
        (repo / ".doctrine-state").mkdir()
        (repo / ".doctrine-state" / "checkpoint.json").write_text(
            "{not json", encoding="utf-8")

        self.assertEqual(fleet.inspect(repo, self.source, "0.7.0")["state"],
                         "unreadable")

    def test_a_directory_without_git_still_reports(self) -> None:
        repo = self._repo("nogit", git=False)

        row = fleet.inspect(repo, self.source, "0.7.0")

        self.assertEqual(row["worktree"], "unknown")
        self.assertEqual(row["release"], "untagged")


class TestCommand(FleetTestCase):
    def test_status_exits_nonzero_when_any_repo_drifted(self) -> None:
        current = self._repo("current")
        behind = self._repo("behind", version="0.6.29")

        self.assertEqual(fleet.cmd_status([current], self.source, False), 0)
        self.assertEqual(
            fleet.cmd_status([current, behind], self.source, False), 1)

    def test_non_doctrine_paths_are_skipped_not_fatal(self) -> None:
        plain = self.workspace / "unrelated"
        plain.mkdir()

        self.assertEqual(fleet.cmd_status([plain], self.source, False), 0)

    def test_discovery_finds_repos_one_level_down(self) -> None:
        self._repo("alpha")
        self._repo("beta")
        (self.workspace / "not-a-repo").mkdir()

        found = {p.name for p in fleet.discover(self.workspace)}

        self.assertEqual(found, {"source", "alpha", "beta"})

    def test_the_fleet_config_names_the_repos(self) -> None:
        self._repo("alpha")
        state = self.workspace / ".doctrine-state"
        state.mkdir()
        (state / "fleet.json").write_text(json.dumps({"repos": ["alpha"]}),
                                          encoding="utf-8")

        self.assertEqual([p.name for p in fleet.from_config(self.workspace)],
                         ["alpha"])

    def test_a_malformed_fleet_config_yields_no_repos(self) -> None:
        state = self.workspace / ".doctrine-state"
        state.mkdir()
        (state / "fleet.json").write_text("{not json", encoding="utf-8")

        self.assertEqual(fleet.from_config(self.workspace), [])

    def test_json_output_is_machine_readable(self) -> None:
        repo = self._repo("app")
        buffer = []
        original = sys.stdout.write
        sys.stdout.write = buffer.append  # type: ignore[assignment]
        try:
            fleet.cmd_status([repo], self.source, True)
        finally:
            sys.stdout.write = original  # type: ignore[assignment]

        payload = json.loads("".join(buffer))

        self.assertEqual(payload["sourceVersion"], "0.7.0")
        self.assertEqual(payload["repos"][0]["repo"], "app")
        self.assertEqual(payload["repos"][0]["drift"], "current")


class TestResilience(FleetTestCase):
    """A survey must survive the repos it surveys."""

    def test_an_unreadable_directory_does_not_take_down_the_scan(self) -> None:
        """Regression: one PermissionError under --root aborted the whole
        fleet view with a traceback, while every other failure in this module
        degrades to 'unknown'."""
        good = self._repo("readable")
        blocked = self.workspace / "blocked"
        blocked.mkdir()

        def is_file(self: Path) -> bool:
            if "blocked" in self.as_posix():
                raise PermissionError(13, "Access is denied")
            return os.path.isfile(self)   # not Path.is_file: that is patched

        with mock.patch.object(fleet.Path, "is_file", is_file):
            found = fleet.discover(self.workspace)

        self.assertIn(good.name, {p.name for p in found})
        self.assertEqual(fleet.cmd_status([blocked], self.source, False), 0)

    def test_a_skipped_path_reports_why(self) -> None:
        """Regression: an unreadable directory was reported as 'no
        .Doctrine.md'. An operator reading that draws exactly the wrong
        conclusion about their fleet."""
        missing = self.workspace / "gone"
        plain = self.workspace / "plain"
        plain.mkdir()
        as_file = self.workspace / "afile"
        as_file.write_text("x", encoding="utf-8")

        self.assertEqual(fleet.skip_reason(plain), "no .Doctrine.md")
        self.assertEqual(fleet.skip_reason(missing), "no such path")
        self.assertEqual(fleet.skip_reason(as_file), "not a directory")

        def is_file(self: Path) -> bool:
            raise PermissionError(13, "Access is denied")

        with mock.patch.object(fleet.Path, "is_file", is_file):
            self.assertIn("unreadable", fleet.skip_reason(plain))

    def test_a_non_ascii_repo_name_renders_instead_of_crashing(self) -> None:
        """Regression: a CJK or emoji directory name raised
        UnicodeEncodeError on a cp1252 console and killed the command."""
        repo = self._repo("日本語repo")

        row = fleet.inspect(repo, self.source, "0.7.0")
        rendered = fleet.render_table([row])

        self.assertIn("repo", rendered)
        self.assertEqual(fleet.cmd_status([repo], self.source, False), 0)


class TestReadOnly(FleetTestCase):
    def test_inspection_never_writes_to_a_governed_repo(self) -> None:
        repo = self._repo("untouched")
        (repo / ".doctrine-state").mkdir()
        (repo / ".doctrine-state" / "checkpoint.json").write_text(
            json.dumps({"seq": 3}), encoding="utf-8")
        before = _tree_digest(repo)

        fleet.cmd_status([repo], self.source, False)

        self.assertEqual(_tree_digest(repo), before)

    def test_inspection_does_not_rewrite_a_stale_git_index(self) -> None:
        """Regression: `git status` refreshes and rewrites the index whenever
        the stat cache is stale - true of any fresh clone. The original
        read-only test passed only because its fixture was committed
        microseconds earlier, so the index was still warm."""
        repo = self._repo("stale")
        index = repo / ".git" / "index"
        stale = time.time() - 86_400
        for path in sorted(repo.rglob("*")):
            if path.is_file() and ".git" not in path.parts:
                os.utime(path, (stale, stale))
        before = index.read_bytes()

        fleet.cmd_status([repo], self.source, False)

        self.assertEqual(index.read_bytes(), before,
                         "inspection rewrote the git index")

    def test_inspection_does_not_run_commands_from_the_scanned_repo(self) -> None:
        """Regression: git honours the SCANNED repo's core.fsmonitor, so a
        'strictly read-only' scan executed code chosen by the repo it was
        inspecting."""
        repo = self._repo("hostile")
        marker = self.workspace / "fsmonitor-fired.txt"
        script = self.workspace / "fsmonitor.py"
        script.write_text(
            f"from pathlib import Path\n"
            f"Path(r'{marker}').write_text('fired')\n", encoding="utf-8")
        _git(repo, "config", "core.fsmonitor",
             f'"{sys.executable}" "{script}"')

        fleet.cmd_status([repo], self.source, False)

        self.assertFalse(marker.exists(),
                         "the scanned repo's configured command was executed")


if __name__ == "__main__":
    unittest.main()

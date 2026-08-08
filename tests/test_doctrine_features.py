"""Tests for tools/doctrine_features.py — the FEATURES.md toggle reader."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import doctrine_features as df  # noqa: E402


class TempRepo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / ".Doctrine.md").write_text("# doctrine\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def features(self, body: str) -> None:
        (self.root / "FEATURES.md").write_text(body, encoding="utf-8")


class TestParsing(TempRepo):
    def test_reads_on_and_off_bold_or_plain(self):
        self.features(
            "| Feature | State | What |\n|---|---|---|\n"
            "| `alpha` | **on** | x |\n"
            "| `beta` | off | y |\n"
            "| `gamma` | ON | z |\n"
            "| `delta` | **OFF** | w |\n")
        self.assertEqual(df.read_features(self.root),
                         {"alpha": True, "beta": False,
                          "gamma": True, "delta": False})

    def test_prose_mentioning_a_feature_is_not_a_toggle(self):
        """Only table rows count. A sentence saying a feature is off must not
        flip it, or documentation silently becomes configuration."""
        self.features("| `alpha` | on | x |\n\n"
                      "Turn `alpha` off by setting it to off.\n")
        self.assertTrue(df.is_on(self.root, "alpha"))


class TestDefaults(TempRepo):
    def test_unknown_feature_defaults_on(self):
        """A repo installed before a toggle existed must keep its behaviour
        rather than silently lose it."""
        self.features("| `alpha` | on | x |\n")
        self.assertTrue(df.is_on(self.root, "never-heard-of-it"))

    def test_missing_file_defaults_on(self):
        self.assertEqual(df.read_features(self.root), {})
        self.assertTrue(df.is_on(self.root, "anything"))

    def test_unparseable_file_fails_OPEN_not_closed(self):
        """A toggle file that disables behaviour when it fails to parse is a
        worse failure than having no toggle file."""
        (self.root / "FEATURES.md").write_bytes(b"\xff\xfe not markdown")
        self.assertTrue(df.is_on(self.root, "prune-on-force"))

    def test_explicit_off_beats_the_default(self):
        self.features("| `prune-on-force` | off | |\n")
        self.assertFalse(df.is_on(self.root, "prune-on-force"))

    def test_lookup_is_case_insensitive(self):
        self.features("| `Prune-On-Force` | off | |\n")
        self.assertFalse(df.is_on(self.root, "prune-on-force"))


class TestShippedFile(unittest.TestCase):
    def test_this_repos_own_features_file_parses(self):
        """The shipped FEATURES.md is the template every consumer is seeded
        with; if it does not parse, every install gets a dead switchboard."""
        parsed = df.read_features(REPO)
        self.assertTrue(parsed, "the repo's own FEATURES.md did not parse")
        for name in ("autonomous-verification", "prune-on-force",
                     "drift-banner", "state-plane", "orchestration-ceremony"):
            self.assertIn(name, parsed)
        # orchestration-ceremony narrows required PAPERWORK, not permission
        # (nothing here reaches the guard) - so unlike autonomous-verification
        # it belongs with the backward-compatible defaults: on.
        self.assertTrue(parsed["orchestration-ceremony"])

    def test_find_root_locates_the_repo_from_a_subdir(self):
        self.assertEqual(df.find_root(REPO / "tools"), REPO)


if __name__ == "__main__":
    unittest.main()

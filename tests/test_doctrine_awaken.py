"""Tests for the activation layer: doctrine_awaken (doctor) + doctrine_engage.

Verifies the doctor's AWAKE/NOT-AWAKE verdict (UserPromptSubmit is the critical
awakening check), non-doctrine-repo safety, and the engage tool's root discovery.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import doctrine_awaken as aw   # noqa: E402
import doctrine_engage as eng  # noqa: E402

_SS = {"hooks": [{"type": "command", "command": "hydrate"}]}
_UPS = {"hooks": [{"type": "command", "command": "engage"}]}


def _wire(root: Path, *, ups: bool) -> None:
    """Fully wire an activation-ready repo; omit UserPromptSubmit iff not ups."""
    (root / ".Doctrine.md").write_text("# doctrine\n", "utf-8")
    (root / ".Doctrine").mkdir()
    (root / "tools").mkdir()
    (root / "tools" / "doctrine_engage.py").write_text("x\n", "utf-8")
    (root / ".doctrine-state").mkdir()
    (root / "AGENTS.md").write_text("boot\n", "utf-8")
    (root / "CLAUDE.md").write_text(
        "@.Doctrine.md\n@.doctrine-state/local/hydration.bundle.md\n", "utf-8")
    (root / ".claude").mkdir()
    hooks = {"SessionStart": [_SS]}
    if ups:
        hooks["UserPromptSubmit"] = [_UPS]
    (root / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": hooks}), "utf-8")


class TestAwaken(unittest.TestCase):
    def test_fully_wired_repo_is_awake(self):
        with tempfile.TemporaryDirectory() as d:
            _wire(Path(d), ups=True)
            rows, awake = aw.audit(Path(d))
            self.assertTrue(awake, [r for r in rows if r[0] != aw.OK])

    def test_missing_userpromptsubmit_is_not_awake(self):
        with tempfile.TemporaryDirectory() as d:
            _wire(Path(d), ups=False)
            rows, awake = aw.audit(Path(d))
            self.assertFalse(awake)  # UserPromptSubmit is a critical check
            ups = [r for r in rows if "UserPromptSubmit" in r[1]]
            self.assertEqual(len(ups), 1)
            self.assertEqual(ups[0][0], aw.MISS)

    def test_missing_agents_boot_is_not_awake(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _wire(root, ups=True)
            (root / "AGENTS.md").unlink()
            rows, awake = aw.audit(root)
            self.assertFalse(awake)
            agents = [r for r in rows if "AGENTS.md present" in r[1]]
            self.assertEqual(len(agents), 1)
            self.assertEqual(agents[0][0], aw.MISS)

    def test_non_doctrine_dir_is_not_awake(self):
        with tempfile.TemporaryDirectory() as d:
            _, awake = aw.audit(Path(d))
            self.assertFalse(awake)


class TestEngage(unittest.TestCase):
    def test_reminder_names_personal_builder_and_devops_path(self):
        # BOTH markers: new installs write "solobuilder", but 15+ existing
        # repos carry the legacy "personal". Keying on one strands the other.
        self.assertIn("Delivery profile: solobuilder", eng.REMINDER)
        self.assertIn("Delivery profile: personal", eng.REMINDER)
        self.assertIn("DevOps verification", eng.REMINDER)
        self.assertIn("creative build -> deterministic verification",
                      eng.REMINDER)

    def test_reminder_keeps_craft_roles_on_the_personal_profile(self):
        """Regression: the reminder used to say specialists activate "only from
        real risk", so personal-profile work wore `[ROLE: Solo Builder]` alone
        and never loaded the craft card (interop for a CLI, database for a
        schema). The profile relaxes ceremony, not the role system."""
        self.assertIn("FULL ROLE SET", eng.REMINDER)
        self.assertIn("GATING ONLY", eng.REMINDER)
        # both instructions that collapsed the role system must stay gone
        self.assertNotIn("activate other roles only from real risk",
                         eng.REMINDER)
        self.assertNotIn("default to Solo Builder", eng.REMINDER)

    def test_find_root_none_outside_doctrine_repo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(eng.find_root(Path(d)))

    def test_find_root_from_subdir(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".Doctrine.md").write_text("# doctrine\n", "utf-8")
            sub = root / "a" / "b"
            sub.mkdir(parents=True)
            self.assertEqual(eng.find_root(sub), root)


class TestCorpusDrift(unittest.TestCase):
    """A session `@`-imports .Doctrine.md ONCE, at start. Reinstalling the
    corpus under a live session leaves it acting on deleted roles and skills,
    and nothing said so - garagebox kept emitting `[ROLE: Solo Builder]` after
    that role had been removed from its disk."""

    def _corpus(self, root: Path) -> None:
        (root / ".Doctrine.md").write_text("# doctrine v1\n", "utf-8")
        for sub in ("roles", "skills"):
            (root / ".Doctrine" / sub).mkdir(parents=True)
        (root / ".Doctrine" / "roles" / "backend-engineer.md").write_text(
            "x\n", "utf-8")
        (root / ".Doctrine" / "skills" / "testing.md").write_text("x\n", "utf-8")

    def test_first_turn_records_baseline_and_stays_quiet(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._corpus(root)
            self.assertEqual(eng.drift_notice(root, "s1"), "")

    def test_unchanged_corpus_never_warns(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._corpus(root)
            eng.drift_notice(root, "s1")
            for _ in range(3):
                self.assertEqual(eng.drift_notice(root, "s1"), "")

    def test_deleted_role_card_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._corpus(root)
            eng.drift_notice(root, "s1")
            (root / ".Doctrine" / "roles" / "backend-engineer.md").unlink()
            self.assertIn("STALE", eng.drift_notice(root, "s1"))

    def test_edited_root_law_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._corpus(root)
            eng.drift_notice(root, "s1")
            (root / ".Doctrine.md").write_text("# doctrine v2\n", "utf-8")
            self.assertIn("STALE", eng.drift_notice(root, "s1"))

    def test_a_restarted_session_starts_clean(self):
        """The banner must clear on restart, or it becomes permanent noise."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._corpus(root)
            eng.drift_notice(root, "old-session")
            (root / ".Doctrine.md").write_text("# doctrine v2\n", "utf-8")
            self.assertIn("STALE", eng.drift_notice(root, "old-session"))
            self.assertEqual(eng.drift_notice(root, "new-session"), "")

    def test_skill_body_edits_do_not_warn(self):
        """Card BODIES are Read on demand mid-session, so they are never stale.
        Hashing them would fire on every ordinary edit and train the reader to
        ignore the banner."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._corpus(root)
            eng.drift_notice(root, "s1")
            (root / ".Doctrine" / "skills" / "testing.md").write_text(
                "rewritten entirely\n", "utf-8")
            self.assertEqual(eng.drift_notice(root, "s1"), "")

    def test_missing_session_id_is_a_silent_no_op(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._corpus(root)
            self.assertEqual(eng.drift_notice(root, None), "")

    def test_undecodable_payload_does_not_take_the_hook_down(self):
        """A hook that raises blocks the turn. One bad byte must not."""
        self.assertIsNone(eng._session_id(b"\xff\xfe not json"))
        self.assertIsNone(eng._session_id(b""))
        self.assertEqual(eng._session_id(b'{"session_id":"a/b..c"}'), "abc")


if __name__ == "__main__":
    unittest.main()

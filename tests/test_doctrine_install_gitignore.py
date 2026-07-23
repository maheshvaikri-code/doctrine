"""Regression: the installer's managed .gitignore block.

Default install ignores only machine-local state (corpus stays committable).
--local lists the WHOLE framework footprint in one marker-delimited block,
including the variable per-adapter paths, and never the repo's docs/ work
product. The writer replaces (not duplicates) its block and preserves all
content outside the markers byte-exactly, including CRLF.
"""
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import doctrine_install as di  # noqa: E402


class TestGitignoreBlockBuilder(unittest.TestCase):
    def test_default_block_is_minimal_corpus_committable(self):
        block = di.gitignore_block(["claude"], local=False)
        self.assertEqual(block, [".doctrine-state/local/", "__pycache__/"])
        self.assertNotIn(".Doctrine/", block)  # corpus stays committable

    def test_local_block_covers_the_framework(self):
        block = di.gitignore_block(["claude", "cursor"], local=True)
        for path in (".Doctrine.md", ".Doctrine/", ".doctrine-state/",
                     ".mcp.json", "AGENTS.md", "tools/doctrine_*.py",
                     "tests/test_doctrine_*.py", ".claude/agents/",
                     "CLAUDE.md", ".cursor/rules/doctrine.mdc"):
            self.assertIn(path, block)

    def test_local_block_uses_variable_adapter_paths(self):
        self.assertIn("GEMINI.md", di.gitignore_block(["gemini"], local=True))
        self.assertIn(".github/copilot-instructions.md",
                      di.gitignore_block(["copilot"], local=True))
        # a non-claude install must NOT ignore the claude-only files
        cur = di.gitignore_block(["cursor"], local=True)
        self.assertNotIn("CLAUDE.md", cur)
        self.assertNotIn(".claude/agents/", cur)

    def test_local_block_never_ignores_docs_work_product(self):
        block = di.gitignore_block(["all"] + sorted(di.ADAPTERS), local=True)
        self.assertFalse([ln for ln in block if ln.startswith("docs/")],
                         "docs/ artifacts (briefs/ADRs/reviews) are work product")

    def test_makefile_is_offered_commented_not_active(self):
        block = di.gitignore_block(["claude"], local=True)
        self.assertTrue(any(ln.startswith("# Makefile") for ln in block))
        self.assertNotIn("Makefile", block)  # not an active (uncommented) rule


class TestManagedBlockWriter(unittest.TestCase):
    def _write(self, path, lines):
        rep = di.Report()
        di.write_managed_block(path, lines, rep, path.parent)
        return rep

    def test_appends_marked_block_to_empty_file(self):
        with tempfile.TemporaryDirectory() as d:
            gi = Path(d) / ".gitignore"
            self._write(gi, [".Doctrine/", "AGENTS.md"])
            text = gi.read_text("utf-8")
            self.assertIn(di.GITIGNORE_BEGIN, text)
            self.assertIn(di.GITIGNORE_END, text)
            self.assertIn(".Doctrine/", text)

    def test_replaces_block_not_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            gi = Path(d) / ".gitignore"
            self._write(gi, [".doctrine-state/local/"])          # minimal
            self._write(gi, [".Doctrine/", ".mcp.json"])         # --local
            text = gi.read_text("utf-8")
            self.assertEqual(text.count(di.GITIGNORE_BEGIN), 1)  # single block
            self.assertEqual(text.count(di.GITIGNORE_END), 1)
            self.assertIn(".Doctrine/", text)
            self.assertNotIn(".doctrine-state/local/", text)     # old block gone

    def test_preserves_outside_content_and_crlf(self):
        with tempfile.TemporaryDirectory() as d:
            gi = Path(d) / ".gitignore"
            gi.write_bytes(b"build/\r\ndist/\r\n")               # CRLF, user rules
            self._write(gi, [".Doctrine/"])
            raw = gi.read_bytes()
            self.assertIn(b"build/", raw)
            self.assertIn(b"dist/", raw)
            self.assertIn(b"\r\n", raw)                          # CRLF preserved
            self.assertNotIn(b"\n\n\r\n", raw.replace(b"\r\n", b"\n"))
            self.assertIn(".Doctrine/", gi.read_text("utf-8"))

    def test_idempotent_second_write_is_a_noop(self):
        with tempfile.TemporaryDirectory() as d:
            gi = Path(d) / ".gitignore"
            self._write(gi, [".Doctrine/", "AGENTS.md"])
            before = gi.read_bytes()
            rep = self._write(gi, [".Doctrine/", "AGENTS.md"])
            self.assertEqual(gi.read_bytes(), before)            # unchanged
            self.assertEqual(rep.skipped_same, 1)


class TestLocalInstallIntegration(unittest.TestCase):
    def test_fresh_local_install_writes_framework_block(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "fresh"
            rc = di.install(REPO, target, ["claude"], enterprise=False,
                            ci=False, force=False, local=True)
            self.assertIn(rc, (0, 1))
            text = (target / ".gitignore").read_text("utf-8")
            self.assertIn(di.GITIGNORE_BEGIN, text)
            self.assertIn(".Doctrine/", text)          # whole corpus ignored
            self.assertIn("tools/doctrine_*.py", text)


if __name__ == "__main__":
    unittest.main()

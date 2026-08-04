"""Tests for tools/doctrine_install.py and tools/doctrine_mcp.py."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import doctrine_install as di  # noqa: E402
import doctrine_lint as dl  # noqa: E402


class TestInstaller(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name) / "consumer"

    def tearDown(self):
        self._tmp.cleanup()

    def install(self, tools="claude", **kw):
        return di.install(REPO, self.target,
                          [t for t in tools.split(",")],
                          kw.get("enterprise", False), kw.get("ci", False),
                          kw.get("force", False),
                          ci_provider=kw.get("ci_provider", "github"))

    def test_ci_wiring_lands_at_each_providers_canonical_path(self):
        for provider, rel in (("github", ".github/workflows/doctrine.yml"),
                              ("gitlab", ".gitlab-ci.yml"),
                              ("azure", "azure-pipelines.yml")):
            with self.subTest(provider=provider):
                self._tmp.cleanup()
                self._tmp = tempfile.TemporaryDirectory()
                self.target = Path(self._tmp.name) / "consumer"
                self.assertEqual(
                    self.install(ci=True, ci_provider=provider), 0)
                installed = self.target / rel
                self.assertTrue(installed.is_file(), rel)
                self.assertIn("doctrine_lint.py",
                              installed.read_text("utf-8"))

    def test_the_guard_hook_resolves_from_the_project_not_the_cwd(self):
        """Regression: the hook invoked `tools/doctrine_guard.py` relatively.

        Run from a subdirectory, python cannot find it and exits 2 - the code
        the hook contract reserves for BLOCK - so the enforcement gate became
        a total lockout that prevented its own repair. The plugin's variant
        failed the other way: its `os.path.exists` check missed, so the gate
        silently turned OFF. Both are executed here from a subdirectory.
        """
        for config in (REPO / ".claude" / "settings.json",
                       REPO / "plugin" / "hooks" / "hooks.json"):
            hooks = json.loads(config.read_text("utf-8"))["hooks"]
            self.assertTrue(hooks.get("PreToolUse"),
                            f"{config.name}: no PreToolUse hook")
            # EVERY hook, not just the guard: a SessionStart or
            # UserPromptSubmit hook exiting 2 blocks the turn just as hard.
            for event, groups in hooks.items():
                for group in groups:
                    for entry in group["hooks"]:
                        argv = shlex.split(entry["command"], posix=False)
                        argv = [a[1:-1]
                                if len(a) > 1 and a[0] == a[-1] == '"' else a
                                for a in argv]
                        result = subprocess.run(
                            argv, cwd=REPO / "tools",
                            input='{"tool_name":"Write","cwd":"%s",'
                                  '"tool_input":{"file_path":'
                                  '"docs/releases/gold/v1.0.0.json",'
                                  '"content":"{}"}}' % REPO.as_posix(),
                            capture_output=True, text=True,
                            env={**os.environ,
                                 "CLAUDE_PROJECT_DIR": str(REPO)})

                        with self.subTest(config=config.name, event=event,
                                          command=entry["command"][:40]):
                            self.assertEqual(
                                result.returncode, 0,
                                "hook failed from a subdirectory "
                                f"({event}): {result.stderr[:200]}")
                            # rc == 0 is the ONE condition a silently-off
                            # hook also satisfies - its os.path.exists misses
                            # and it exits 0 by design. This assertion used to
                            # stop here, and a verifier caught it asserting
                            # exactly the failure its own docstring named.
                            # Every activation hook must also DO something;
                            # either stream proves it ran (doctrine_metrics
                            # reports on stderr).
                            if event != "PreToolUse":
                                self.assertTrue(
                                    (result.stdout + result.stderr).strip(),
                                    f"{event} hook produced no output at all "
                                    "from a subdirectory - it resolved "
                                    "nothing and silently did not run")

    def test_the_guard_hook_still_decides_from_a_subdirectory(self):
        for config in (REPO / ".claude" / "settings.json",
                       REPO / "plugin" / "hooks" / "hooks.json"):
            entry = json.loads(config.read_text("utf-8"))[
                "hooks"]["PreToolUse"][0]["hooks"][0]
            argv = shlex.split(entry["command"], posix=False)
            argv = [a[1:-1] if len(a) > 1 and a[0] == a[-1] == '"' else a
                    for a in argv]

            result = subprocess.run(
                argv, cwd=REPO / "tools",
                input='{"tool_name":"Write","cwd":"%s","tool_input":'
                      '{"file_path":"docs/releases/gold/v1.0.0.json",'
                      '"content":"{}"}}' % REPO.as_posix(),
                capture_output=True, text=True,
                env={**os.environ, "CLAUDE_PROJECT_DIR": str(REPO)})

            with self.subTest(config=config.name):
                self.assertIn("permissionDecision", result.stdout,
                              "the gate went silent instead of deciding")

    def test_an_unknown_ci_provider_is_refused_before_any_write(self):
        self.assertEqual(self.install(ci=True, ci_provider="jenkins"), 2)
        self.assertFalse(self.target.exists(),
                         "a refused install must write nothing")

    def test_claude_install_round_trip(self):
        self.assertEqual(self.install("claude,cursor"), 0)
        for rel in (".Doctrine.md", ".Doctrine/00-charter.md",
                    ".Doctrine/skills/backend.md",
                    "tools/doctrine_state.py", "tools/doctrine_mcp.py",
                    ".claude/agents/code-reviewer.md",
                    ".claude/commands/checkpoint.md",
                    ".claude/settings.json", "CLAUDE.md", "AGENTS.md",
                    ".cursor/rules/doctrine.mdc", "Makefile", ".mcp.json",
                    "tests/test_doctrine_state.py"):
            self.assertTrue((self.target / rel).exists(), rel)
        claude_md = (self.target / "CLAUDE.md").read_text("utf-8")
        self.assertIn("@.Doctrine.md", claude_md)
        gitignore = (self.target / ".gitignore").read_text("utf-8")
        self.assertIn(".doctrine-state/local/", gitignore)

    def test_maple_flag_remains_an_idempotent_compatibility_alias(self):
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       maple=True), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertEqual(brief.count("Workforce runtime: maple"), 1)

    def test_maple_is_enabled_by_default(self):
        self.assertEqual(self.install(), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Workforce runtime: maple", brief)
        self.assertNotIn("Agent latitude:", brief)

    def test_personal_profile_seeds_canonical_marker(self):
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       personal=True), 0)
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       personal=True), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Delivery profile: personal", brief)
        self.assertEqual(brief.count("Agent latitude: creative"), 1)
        self.assertIn("Workforce runtime: maple", brief)

    def test_solo_cli_alias_seeds_personal_profile(self):
        self.assertEqual(di.main([
            "--source", str(REPO),
            "--target", str(self.target),
            "--tool", "codex",
            "--solo",
        ]), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Delivery profile: personal", brief)
        self.assertIn("Agent latitude: creative", brief)

    def test_personal_reinstall_preserves_explicit_agent_latitude(self):
        brief_path = self.target / "docs" / "brief.md"
        brief_path.parent.mkdir(parents=True)
        brief_path.write_text(
            "Delivery profile: personal\n"
            "**Agent latitude:** deterministic\n",
            encoding="utf-8",
        )
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       personal=True), 0)
        brief = brief_path.read_text("utf-8")
        self.assertIn("**Agent latitude:** deterministic", brief)
        self.assertNotIn("Agent latitude: creative", brief)

    def test_personal_and_enterprise_are_rejected_before_copy(self):
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], True, False, False,
                       personal=True), 2)
        self.assertFalse((self.target / ".Doctrine.md").exists())

    def test_personal_rejects_existing_enterprise_brief_before_copy(self):
        brief = self.target / "docs" / "brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("Merge profile: enterprise\n", encoding="utf-8")
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       personal=True), 2)
        self.assertFalse((self.target / ".Doctrine.md").exists())

    def test_enterprise_rejects_existing_personal_brief_before_copy(self):
        brief = self.target / "docs" / "brief.md"
        brief.parent.mkdir(parents=True)
        brief.write_text("Delivery profile: personal\n", encoding="utf-8")
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], True, False, False),
            2,
        )
        self.assertFalse((self.target / ".Doctrine.md").exists())

    def test_personal_remains_compatible_with_startup(self):
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       startup=True, personal=True), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Delivery profile: personal", brief)
        self.assertIn("Company profile: startup", brief)

    def test_verify_flag_runs_init_then_gates(self):
        # --verify must init state THEN run the gate suite, both in the
        # target; assert the plumbing (not the 9-min suite itself, which
        # has its own tests and would recurse through the copied tests).
        calls = []

        def fake_run(cmd, cwd=None, **kw):
            calls.append((list(cmd), Path(cwd)))
            return type("R", (), {"returncode": 0})()

        with mock.patch.object(di.subprocess, "run", fake_run):
            rc = di.install(REPO, self.target, ["claude"], False, False,
                            False, verify=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2, calls)
        (init_cmd, init_cwd), (verify_cmd, verify_cwd) = calls
        self.assertIn("tools/doctrine_state.py", init_cmd)
        self.assertIn("init", init_cmd)
        self.assertEqual(init_cwd, self.target)
        self.assertIn("tools/doctrine_verify.py", verify_cmd)
        self.assertEqual(verify_cwd, self.target)

    def test_verify_propagates_gate_failure(self):
        # a failing gate suite must surface as a non-zero install exit
        def fake_run(cmd, cwd=None, **kw):
            hit = any("doctrine_verify.py" in str(c) for c in cmd)
            return type("R", (), {"returncode": 1 if hit else 0})()

        with mock.patch.object(di.subprocess, "run", fake_run):
            rc = di.install(REPO, self.target, ["claude"], False, False,
                            False, verify=True)
        self.assertNotEqual(rc, 0)

    def test_verify_refuses_on_tool_conflict(self):
        # G5 MAJOR-1 regression: a target carrying a different-content
        # enforcement tool must NOT be executed by --verify. copy_file
        # skips it (no --force), so --verify must refuse, not run it.
        (self.target / "tools").mkdir(parents=True)
        (self.target / "tools" / "doctrine_verify.py").write_text(
            "raise SystemExit('should never run')\n", encoding="utf-8")
        calls = []

        def fake_run(cmd, cwd=None, **kw):
            calls.append(cmd)
            return type("R", (), {"returncode": 0})()

        with mock.patch.object(di.subprocess, "run", fake_run):
            rc = di.install(REPO, self.target, ["claude"], False, False,
                            False, verify=True)
        self.assertEqual(rc, 2)
        self.assertEqual(calls, [])  # never executed the target's tools

    def test_no_verify_runs_no_subprocess(self):
        calls = []

        def fake_run(cmd, cwd=None, **kw):
            calls.append(cmd)
            return type("R", (), {"returncode": 0})()

        with mock.patch.object(di.subprocess, "run", fake_run):
            di.install(REPO, self.target, ["claude"], False, False, False)
        self.assertEqual(calls, [])

    def test_idempotent(self):
        self.install()
        first = sorted(p.relative_to(self.target).as_posix()
                       for p in self.target.rglob("*") if p.is_file())
        self.assertEqual(self.install(), 0)
        second = sorted(p.relative_to(self.target).as_posix()
                        for p in self.target.rglob("*") if p.is_file())
        self.assertEqual(first, second)

    def test_existing_claude_md_appended_not_replaced(self):
        self.target.mkdir(parents=True)
        (self.target / "CLAUDE.md").write_text(
            "# My project rules\nkeep me\n", encoding="utf-8")
        self.install()
        text = (self.target / "CLAUDE.md").read_text("utf-8")
        self.assertIn("keep me", text)
        self.assertIn("@.Doctrine.md", text)

    def test_differing_file_skipped_without_force(self):
        self.install()
        marker = self.target / ".Doctrine" / "00-charter.md"
        marker.write_text("locally edited\n", encoding="utf-8")
        self.assertEqual(self.install(), 1)  # nonzero: skipped diffs
        self.assertEqual(marker.read_text("utf-8"), "locally edited\n")
        self.assertEqual(self.install(force=True), 0)
        self.assertNotEqual(marker.read_text("utf-8"), "locally edited\n")

    def test_force_reinstall_preserves_repo_state_memory_and_plans(self):
        self.assertEqual(self.install(enterprise=True), 0)
        protected = {
            ".doctrine-state/checkpoint.json": b'{"seq":7}\n',
            ".doctrine-state/checkpoints/7-session.json": b'{"seq":7}\n',
            ".doctrine-state/local/openhawk/sessions.jsonl": b'{"id":"s1"}\n',
            "memory/project.ndjson": b'{"fact":"keep"}\n',
            "sessions/current.json": b'{"session":"keep"}\n',
            "docs/plans/current-program.md": b"# Keep this plan\n",
            "docs/briefs/current-task.md": b"# Keep this brief\n",
            "docs/adr/999-project-decision.md": b"# Keep this decision\n",
        }
        brief = self.target / "docs" / "brief.md"
        protected["docs/brief.md"] = (
            brief.read_bytes() + b"\nRepository-owned acceptance data.\n"
        )
        for rel, data in protected.items():
            path = self.target / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        self.assertEqual(self.install(enterprise=True, force=True), 0)
        for rel, expected in protected.items():
            self.assertEqual(
                (self.target / rel).read_bytes(),
                expected,
                f"force reinstall changed repository-owned data: {rel}",
            )

    def test_existing_agents_md_untouched(self):
        self.target.mkdir(parents=True)
        (self.target / "AGENTS.md").write_text("mine\n", encoding="utf-8")
        self.install()
        self.assertEqual((self.target / "AGENTS.md").read_text("utf-8"),
                         "mine\n")

    def test_mcp_json_registers_doctrineos(self):
        self.install()
        cfg = json.loads((self.target / ".mcp.json").read_text("utf-8"))
        self.assertIn("doctrineos", cfg.get("mcpServers", {}))
        self.assertIn("doctrine_mcp.py",
                      " ".join(cfg["mcpServers"]["doctrineos"]["args"]))

    def test_existing_mcp_json_untouched(self):
        self.target.mkdir(parents=True)
        (self.target / ".mcp.json").write_text('{"mcpServers":{"mine":{}}}',
                                                encoding="utf-8")
        self.install()
        self.assertEqual((self.target / ".mcp.json").read_text("utf-8"),
                         '{"mcpServers":{"mine":{}}}')

    def test_enterprise_seeds_brief(self):
        self.install(enterprise=True)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Merge profile: enterprise", brief)

    def test_reinstall_preserves_inline_profile_brief_byte_exact(self):
        brief = self.target / "docs" / "brief.md"
        brief.parent.mkdir(parents=True)
        original = (
            b"# Project brief\n\n"
            b"**Profiles:** `Merge profile: enterprise` | "
            b"`Workforce runtime: maple`\n"
            b"Repository-owned acceptance data.\n"
        )
        brief.write_bytes(original)

        self.assertEqual(self.install(enterprise=True, force=True), 0)
        self.assertEqual(brief.read_bytes(), original)

    def test_startup_seeds_brief(self):
        di.install(REPO, self.target, ["claude"], False, False, False,
                   startup=True)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Company profile: startup", brief)

    def test_unknown_tool_refused(self):
        self.assertEqual(self.install("notatool"), 2)

    def test_source_equals_target_refused(self):
        self.assertEqual(di.install(REPO, REPO, ["claude"], False, False,
                                    False), 2)

    def test_nested_source_target_refused(self):
        """Regression: PD-4/IN-2 — self-ingestion on rerun."""
        self.assertEqual(di.install(REPO, REPO / "consumer", ["claude"],
                                    False, False, False), 2)
        self.assertFalse((REPO / "consumer").exists())

    def test_installer_ships_every_tool(self):
        """Regression: doctrine_metrics.py was added in v0.6.1 but never
        joined TOOL_FILES — consumer installs lacked it while their
        copied hooks referenced it. Any tools/doctrine_*.py not shipped
        by the installer is a packaging defect."""
        on_disk = {p.name for p in (REPO / "tools").glob("doctrine_*.py")}
        self.assertEqual(on_disk, set(di.TOOL_FILES),
                         "installer TOOL_FILES out of sync with tools/")

    def test_installer_ships_dashboard_openapi_contract(self):
        """Regression: consumer dashboard tests need their public contract."""
        self.assertEqual(self.install(), 0)
        rel = Path("docs/contracts/doctrine-control-room.openapi.json")
        self.assertEqual(
            (self.target / rel).read_bytes(),
            (REPO / rel).read_bytes(),
        )

    def test_installed_target_lints_clean(self):
        """Regression: PD-1 — a consumer repo must verify out of the box
        (no CHANGELOG, no plugin/ — source-repo-only checks skip)."""
        self.assertEqual(self.install(), 0)
        self.assertEqual(dl.main([str(self.target)]), 0)

    def test_append_preserves_crlf(self):
        """Regression: PD-5 — same class as v0.3.0's D-2."""
        self.target.mkdir(parents=True)
        (self.target / "CLAUDE.md").write_bytes(
            b"# Mine\r\n\r\nkeep-crlf\r\n")
        self.install()
        raw = (self.target / "CLAUDE.md").read_bytes()
        self.assertIn(b"keep-crlf\r\n", raw)
        self.assertIn(b"@.Doctrine.md\r\n", raw)


class TestMcpServer(unittest.TestCase):
    """Protocol-level test over a real stdio subprocess against this repo
    (read-only tools only)."""

    def test_handshake_list_and_calls(self):
        proc = subprocess.Popen(
            [sys.executable, str(REPO / "tools" / "doctrine_mcp.py"),
             "--root", str(REPO)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            def rpc(payload):
                proc.stdin.write(json.dumps(payload) + "\n")
                proc.stdin.flush()
                return json.loads(proc.stdout.readline())

            init = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18",
                                   "capabilities": {},
                                   "clientInfo": {"name": "t"}}})
            self.assertEqual(init["result"]["serverInfo"]["name"],
                             "doctrineos")
            proc.stdin.write(json.dumps(
                {"jsonrpc": "2.0",
                 "method": "notifications/initialized"}) + "\n")
            proc.stdin.flush()

            tools = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            names = {t["name"] for t in tools["result"]["tools"]}
            self.assertLessEqual(
                {"doctrine_lint", "state_verify", "gold_check"}, names)

            status = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": "state_status",
                                     "arguments": {}}})
            self.assertFalse(status["result"]["isError"])
            text = status["result"]["content"][0]["text"]
            self.assertTrue("checkpoint seq" in text
                            or "no state plane" in text, text)

            gold = rpc({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                        "params": {"name": "gold_check",
                                   "arguments": {"tag": "v0.4.0"}}})
            self.assertTrue(gold["result"]["isError"])
            self.assertIn("no gold record",
                          gold["result"]["content"][0]["text"])

            unknown = rpc({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                           "params": {"name": "nope", "arguments": {}}})
            self.assertIn("error", unknown)

            bad = rpc({"jsonrpc": "2.0", "id": 6, "method": "no/such"})
            self.assertEqual(bad["error"]["code"], -32601)

            # Regression: PD-2/MCP-1 — malformed input never kills the loop
            for raw in ("[]", '"just a string"', "42", "null",
                        "[" * 3000 + "]" * 3000):
                proc.stdin.write(raw + "\n")
                proc.stdin.flush()
                reply = json.loads(proc.stdout.readline())
                self.assertIn("error", reply, raw[:20])
            string_params = rpc({"jsonrpc": "2.0", "id": 7,
                                 "method": "tools/call",
                                 "params": "state_status"})
            self.assertEqual(string_params["error"]["code"], -32602)
            missing_arg = rpc({"jsonrpc": "2.0", "id": 8,
                               "method": "tools/call",
                               "params": {"name": "gold_check",
                                          "arguments": {}}})
            self.assertEqual(missing_arg["error"]["code"], -32602)
            self.assertIn("tag", missing_arg["error"]["message"])
            alive = rpc({"jsonrpc": "2.0", "id": 9, "method": "ping"})
            self.assertEqual(alive.get("result"), {},
                             "server must survive all of the above")
        finally:
            proc.stdin.close()
            proc.wait(timeout=15)
            proc.stdout.close()
            proc.stderr.close()


if __name__ == "__main__":
    unittest.main()

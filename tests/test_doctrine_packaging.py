"""Tests for tools/doctrine_install.py and tools/doctrine_mcp.py."""

from __future__ import annotations

import json
import os
import re
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


_YAML_TITLE_KEY_RE = re.compile(r"^\s*-?\s*(?:name|displayName)\s*:\s*(.*)$")


def hook_configs():
    """Every hook config present in THIS tree, skipping what isn't shipped.

    `plugin/hooks/hooks.json` exists only in Doctrine's own source repo - the
    installer ships `tests/` into every consumer but deliberately does not
    ship `plugin/`, which is the Claude Code plugin's own packaging. Reading
    it unconditionally made two guard-hook tests fail with FileNotFoundError
    in EVERY consumer repo, permanently, for a file that was never supposed
    to be there. Present-in-source is asserted separately (see
    `TestInstaller.test_the_source_repo_ships_both_hook_configs`) so this
    tolerance cannot silently degrade into "no configs checked at all".
    """
    return [path for path in (REPO / ".claude" / "settings.json",
                              REPO / "plugin" / "hooks" / "hooks.json")
            if path.is_file()]


def yaml_title_colon_violations(text):
    """Lines whose `name:`/`displayName:` value is an unquoted plain scalar
    containing a bare `: ` (or ending in `:`) - invalid YAML: a colon-space
    inside a plain scalar starts a mapping, per spec, so the parser (and
    GitHub/GitLab/Azure's own) rejects the whole file. This is the exact
    defect this project's own CI templates hit once already: a hand-written,
    prose step title with a colon in it, unquoted.

    Deliberately not a full YAML grammar check - this project takes on no
    YAML-parsing dependency (stdlib-first, dependency-policy.md's "write the
    10 lines" preference over a first-ever third-party dependency for one
    test). It targets the demonstrated failure class, not general
    well-formedness; a template that grows more elaborate syntax would
    warrant a real parser instead.
    """
    violations = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _YAML_TITLE_KEY_RE.match(line)
        if not match:
            continue
        value = match.group(1).strip()
        if not value:
            continue
        if (value[0] == value[-1] == '"') or (value[0] == value[-1] == "'"):
            continue  # fully quoted - safe regardless of what's inside
        if ": " in value or value.endswith(":"):
            violations.append(f"line {lineno}: {line}")
    return violations


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
                # The CI templates wire in the scope-aware entrypoint, not a
                # re-implementation of its steps (ADR-012) - a consumer repo
                # that installs this file must get doctrine_verify.py's
                # is_source_repo() gating, not a copy of the raw ruff/
                # unittest commands that gating exists to skip for them.
                text = installed.read_text("utf-8")
                self.assertIn("doctrine_verify.py", text)
                # Regression guard for the exact defect ADR-012 fixed: a
                # re-implemented, unconditional ruff/unittest step in the
                # template would flood a consumer's own code with Doctrine's
                # ruff findings and run/hang on the consumer's own test
                # suite (ADR-002's observed MAPLE incident, reintroduced at
                # the CI layer instead of the local-verify layer).
                self.assertNotIn("ruff check tools tests", text)
                self.assertNotIn("unittest discover -s tests -v", text)
                # This exact template shipped once with an unquoted colon in
                # a step name - invalid YAML that silently disables the
                # whole workflow (no gate ever runs, no error surfaced
                # anywhere but a parser). Caught in review, not by this
                # test, because this assertion didn't exist yet.
                violations = yaml_title_colon_violations(text)
                self.assertFalse(
                    violations,
                    f"{rel}: unquoted colon in a name/displayName value is "
                    f"invalid YAML (silently disables the whole workflow): "
                    f"{violations}")

    def test_ci_install_works_when_the_source_is_itself_an_install(self):
        """Regression: every CI template must live INSIDE the corpus.

        `github` used to be sourced from the source repo's own live
        `.github/workflows/doctrine.yml`, which the installer does not ship.
        Installing from the source repo worked, so nothing caught it; a
        CHAINED install - target A installed from source, then target B
        installed with A as `--source` - crashed with FileNotFoundError,
        because A never received the file github's entry points at. gitlab
        and azure were unaffected: their templates ship under
        `.Doctrine/templates/ci/`. This asserts the whole set is symmetric.
        """
        first = Path(self._tmp.name) / "first"
        self.assertEqual(
            di.install(REPO, first, ["claude"], False, False, False), 0)
        for provider in sorted(di.CI_PROVIDERS):
            with self.subTest(provider=provider):
                source_rel = di.CI_PROVIDERS[provider][0]
                self.assertTrue(
                    (first / source_rel).is_file(),
                    f"{provider}: template {source_rel} was not installed, so "
                    f"a consumer can never act as an install source for it")
                second = Path(self._tmp.name) / f"second-{provider}"
                self.assertEqual(
                    di.install(first, second, ["claude"], False, True, False,
                               ci_provider=provider), 0,
                    f"{provider}: chained install failed")
                self.assertTrue(
                    (second / di.CI_PROVIDERS[provider][1]).is_file())

    @unittest.skipUnless(dl.is_source_repo(REPO),
                         "source-repo invariant: a consumer has no "
                         ".github/workflows/doctrine.yml to compare against")
    def test_the_github_template_and_the_live_workflow_do_not_drift(self):
        """The corpus template and this repo's own live workflow are twins.

        GitHub only reads workflows from `.github/workflows/`, and the
        installer can only source from inside the corpus, so the same content
        must exist in both places. Two copies is exactly the setup that let
        ADR-012's defect sit unnoticed for months, so the parity is asserted
        rather than trusted to whoever edits one of them next.
        """
        template = REPO / di.CI_PROVIDERS["github"][0]
        live = REPO / ".github" / "workflows" / "doctrine.yml"
        self.assertEqual(
            template.read_text("utf-8").replace("\r\n", "\n"),
            live.read_text("utf-8").replace("\r\n", "\n"),
            f"{template.relative_to(REPO)} and "
            f"{live.relative_to(REPO)} have drifted apart; edit one, copy "
            f"it to the other")

    def test_the_pretooluse_matcher_is_the_write_tools_and_not_bash(self):
        """The matcher IS the security boundary now (ADR-014).

        Before, the guard's own rules were the boundary and the matcher was
        plumbing. Since Bash was removed from the matcher, the matcher string
        alone decides whether a write is checked at all - and nothing tested
        it. Both existing hook tests drive the hook with a Write payload and
        assert exit code + output, so `Bash` silently reappearing (undoing a
        deliberate decision) or `Write` silently disappearing (turning the
        whole gate off while every other test still passes) would both go
        unnoticed. Flagged by the verifier that retired the Bash tests.
        """
        expected = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
        for config in hook_configs():
            with self.subTest(config=config.name):
                groups = json.loads(
                    config.read_text("utf-8"))["hooks"]["PreToolUse"]
                matchers = [g.get("matcher", "") for g in groups]
                tools = {t for m in matchers for t in m.split("|") if t}
                self.assertEqual(
                    tools, expected,
                    f"{config.name}: PreToolUse matcher is {matchers}. "
                    f"Bash must NOT be present (ADR-014 removed the shell "
                    f"arm; the path-analysis code it needs is deleted), and "
                    f"every write tool MUST be, or the guard silently stops "
                    f"seeing writes it is the only check for.")

    @unittest.skipUnless(dl.is_source_repo(REPO),
                         "source-repo invariant: the installer deliberately "
                         "does not ship plugin/ into a consumer")
    def test_the_source_repo_ships_both_hook_configs(self):
        """`hook_configs()` skips a missing config so consumer repos can run
        this suite; that tolerance must not hide a config going missing HERE,
        where both are supposed to exist.

        Skipped outside the source repo for the same reason `hook_configs()`
        tolerates the absence: `plugin/` is the Claude Code plugin's own
        packaging and is never installed. Asserting it unconditionally is the
        very defect this test exists alongside - a permanently-red suite in
        every consumer is how a real regression gets waved through.
        """
        self.assertEqual(
            len(hook_configs()), 2,
            "the source repo must have BOTH .claude/settings.json and "
            "plugin/hooks/hooks.json; hook_configs() found "
            f"{[str(p.relative_to(REPO)) for p in hook_configs()]}")

    def test_the_guard_hook_resolves_from_the_project_not_the_cwd(self):
        """Regression: the hook invoked `tools/doctrine_guard.py` relatively.

        Run from a subdirectory, python cannot find it and exits 2 - the code
        the hook contract reserves for BLOCK - so the enforcement gate became
        a total lockout that prevented its own repair. The plugin's variant
        failed the other way: its `os.path.exists` check missed, so the gate
        silently turned OFF. Both are executed here from a subdirectory.
        """
        for config in hook_configs():
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
        for config in hook_configs():
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

    def test_machine_local_settings_never_travel_to_a_consumer(self):
        """SECURITY. `.claude/settings.local.json` is Claude Code's personal
        override layer: it MERGES OVER settings.json, is untracked by
        convention, and accumulates whatever that operator approved.

        The installer used to copy the whole `.claude/` tree, so the source
        machine's standing permissions - and its absolute paths - were
        installed into every consumer as allow rules. Found in a real repo,
        which had inherited three `Bash(cp ...)` approvals from this one,
        one of them containing the source machine's full path.
        """
        self.assertEqual(self.install(), 0)
        leaked = self.target / ".claude" / "settings.local.json"
        self.assertFalse(
            leaked.exists(),
            "the source repo's machine-local permissions were installed")

        # and it must not sneak back in under --force
        self.assertEqual(self.install(force=True), 0)
        self.assertFalse(leaked.exists())

    @unittest.skipUnless(dl.is_source_repo(REPO),
                         "source-repo invariant: a consumer is not a git "
                         "checkout of Doctrine, so it has no source manifest "
                         "to check itself against")
    def test_only_git_tracked_files_are_installed(self):
        """The PRIMARY rule, and why it is an allowlist.

        `settings.local.json` was the leak we found; `scheduled_tasks.lock` was
        sitting untracked right beside it and a name denylist would have missed
        it, exactly as the guard's write-verb blocklist missed new spellings
        for four rounds. Tracked-ness is the honest definition of "part of the
        framework": if the doctrine's own repo does not commit a file, it is
        not something to install into somebody else's.
        """
        self.assertEqual(self.install(), 0)
        tracked = di.source_manifest(REPO)
        self.assertIsNotNone(tracked, "source repo should be a git checkout")
        for path in sorted((self.target / ".claude").rglob("*")):
            if path.is_file():
                rel = path.relative_to(self.target).as_posix()
                self.assertIn(rel, tracked,
                              f"installed an untracked source file: {rel}")

    def test_manifest_is_none_for_a_non_git_source(self):
        """Must degrade, not install nothing: a tarball source has no git, and
        the caller falls back to the name denylist."""
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(di.source_manifest(Path(d)))

    def test_any_local_json_override_is_treated_as_machine_local(self):
        """The FALLBACK, used only when git cannot answer. Guards the class,
        not one filename: Claude Code's override layer is `*.local.json`."""
        for name in ("settings.local.json", "mcp.local.json",
                     "anything.local.json", "scheduled_tasks.lock"):
            self.assertTrue(di.is_machine_local(Path("x") / name), name)
        for name in ("settings.json", "local.json", "plugin.json"):
            self.assertFalse(di.is_machine_local(Path("x") / name), name)

    def test_features_md_is_seeded_but_never_overwritten(self):
        """FEATURES.md is CONSUMER-owned policy, unlike the corpus. Clobbering
        it under --force would silently re-enable something the human turned
        off - the one failure mode a toggle file must not have."""
        self.assertEqual(self.install(), 0)
        features = self.target / "FEATURES.md"
        self.assertTrue(features.exists(), "FEATURES.md was not seeded")

        mine = "| `prune-on-force` | off | my choice |\n"
        features.write_text(mine, encoding="utf-8")
        self.assertEqual(self.install(force=True), 0)
        self.assertEqual(features.read_text("utf-8"), mine,
                         "--force overwrote the repo's own toggles")

    def test_a_toggle_actually_governs_behaviour(self):
        """Guards against a decorative switchboard: a table nobody reads is
        worse than no table, because it reads as configuration."""
        self.assertEqual(self.install(), 0)
        stale = self.target / ".Doctrine" / "roles" / "zz-stale.md"

        (self.target / "FEATURES.md").write_text(
            "| `prune-on-force` | off | |\n", encoding="utf-8")
        stale.write_text("stale\n", encoding="utf-8")
        self.assertEqual(self.install(force=True), 0)
        self.assertTrue(stale.exists(), "toggle off did not stop the prune")

        (self.target / "FEATURES.md").write_text(
            "| `prune-on-force` | on | |\n", encoding="utf-8")
        self.assertEqual(self.install(force=True), 0)
        self.assertFalse(stale.exists(), "toggle on did not allow the prune")

    def test_claude_md_imports_features(self):
        """Read once per session is the whole point; without the import the
        agent never sees the toggles at all."""
        self.assertEqual(self.install(), 0)
        claude_md = (self.target / "CLAUDE.md").read_text("utf-8")
        self.assertIn("@FEATURES.md", claude_md)

    def test_force_prunes_corpus_files_deleted_upstream(self):
        """The installer used to only COPY, so a role deleted from the doctrine
        survived forever in every consumer - garagebox kept offering
        `[ROLE: Solo Builder]` after a --force reinstall that had removed it."""
        self.assertEqual(self.install(), 0)
        stale = self.target / ".Doctrine" / "roles" / "zz-deleted-upstream.md"
        stale.write_text("stale role\n", encoding="utf-8")

        self.assertEqual(self.install(force=True), 0)
        self.assertFalse(stale.exists(), "--force left a deleted role installed")

    def test_prune_is_recoverable_because_it_backs_up_first(self):
        """Deleting from someone else's repo must be reversible, not merely
        careful."""
        self.assertEqual(self.install(), 0)
        stale = self.target / ".Doctrine" / "skills" / "zz-gone.md"
        stale.write_text("irreplaceable\n", encoding="utf-8")

        report = di.Report()
        di.prune_corpus(REPO, self.target, report, True)

        self.assertIn(".Doctrine/skills/zz-gone.md", report.pruned)
        self.assertIsNotNone(report.prune_backup)
        saved = report.prune_backup / "skills" / "zz-gone.md"
        self.assertTrue(saved.exists(), "pruned file was not backed up")
        self.assertEqual(saved.read_text("utf-8"), "irreplaceable\n")

    def test_a_plain_install_never_deletes_anything(self):
        """Pruning is destructive, so it is gated on --force. An ordinary
        upgrade must never remove a file."""
        self.assertEqual(self.install(), 0)
        stale = self.target / ".Doctrine" / "roles" / "zz-deleted-upstream.md"
        stale.write_text("stale role\n", encoding="utf-8")

        self.assertEqual(self.install(), 0)
        self.assertTrue(stale.exists(),
                        "a non-force install deleted a file")

    def test_prune_stays_inside_the_corpus(self):
        """The blast radius that matters. `.Doctrine/` is the installed
        snapshot the installer owns; everything else belongs to the consumer -
        its own commands, its docs, and above all its memory."""
        self.assertEqual(self.install(), 0)
        mine = {
            self.target / ".claude" / "commands" / "my-own.md": "mine\n",
            self.target / "docs" / "my-notes.md": "notes\n",
            self.target / ".doctrine-state" / "checkpoints" / "1-a.json":
                '{"seq":1}\n',
        }
        for path, body in mine.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

        self.assertEqual(self.install(force=True), 0)

        for path, body in mine.items():
            self.assertTrue(path.exists(), f"prune reached {path.name}")
            self.assertEqual(path.read_text("utf-8"), body)

    def test_force_reinstall_never_touches_the_state_plane(self):
        """INVARIANT: --force refreshes the FRAMEWORK, never the repo's MEMORY.

        .doctrine-state holds checkpoints, distillates and decisions - a
        consumer's session history, hash-chained. The installer must not write
        into it under any flag. Asserted at the INSTALLER level, not just on
        doctrine_state.init, so that adding .doctrine-state to a copy_tree (or
        any new seed step) fails here rather than costing a consumer its
        memory on the next upgrade.
        """
        self.assertEqual(self.install(), 0)
        state = self.target / ".doctrine-state"
        state.mkdir(exist_ok=True)
        (state / "checkpoints").mkdir(exist_ok=True)
        durable = {
            state / "checkpoints" / "7-abc123.json": b'{"seq":7}\n',
            state / "decisions.ndjson": b'{"id":"d-1"}\n',
        }
        for path, blob in durable.items():
            path.write_bytes(blob)

        self.assertEqual(self.install(force=True), 0)

        for path, blob in durable.items():
            self.assertTrue(path.exists(),
                            f"--force deleted {path.name} from the state plane")
            self.assertEqual(path.read_bytes(), blob,
                             f"--force rewrote {path.name}")

    def test_agents_boot_is_refreshed_under_force(self):
        """Regression: AGENTS.md was guarded by `if not agents.exists()`, so it
        was exempt from --force. The ignition file for every non-Claude agent
        went stale after the first install - still naming roles the corpus had
        deleted - and the installer reported nothing."""
        self.assertEqual(self.install(), 0)
        boot = self.target / "AGENTS.md"
        boot.write_text("stale boot\n", encoding="utf-8")

        # without --force: skipped, but REPORTED rather than silently ignored
        report = di.Report()
        di.copy_file(REPO / ".Doctrine" / "adapters" / "AGENTS.md", boot,
                     self.target, report, False)
        self.assertIn("AGENTS.md", report.skipped_diff)
        self.assertEqual(boot.read_text("utf-8"), "stale boot\n")

        # with --force: actually refreshed
        self.assertEqual(self.install(force=True), 0)
        self.assertEqual(
            boot.read_bytes(),
            (REPO / ".Doctrine" / "adapters" / "AGENTS.md").read_bytes())

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

    def test_solobuilder_profile_seeds_canonical_marker(self):
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       personal=True), 0)
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       personal=True), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Delivery profile: solobuilder", brief)
        self.assertEqual(brief.count("Agent latitude: creative"), 1)
        self.assertIn("Workforce runtime: maple", brief)

    def test_solobuilder_cli_flag_seeds_the_profile(self):
        self.assertEqual(di.main([
            "--source", str(REPO),
            "--target", str(self.target),
            "--tool", "codex",
            "--solobuilder",
        ]), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Delivery profile: solobuilder", brief)
        self.assertIn("Agent latitude: creative", brief)

    def test_legacy_personal_marker_still_blocks_enterprise(self):
        """15+ repos were installed with the old spelling. Enterprise must
        still refuse to combine with a legacy brief, or the mutual-exclusion
        rule silently stops applying to every repo installed before the
        rename."""
        (self.target / "docs").mkdir(parents=True, exist_ok=True)
        (self.target / "docs" / "brief.md").write_text(
            "Delivery profile: personal\n", encoding="utf-8")
        self.assertEqual(
            di.install(REPO, self.target, ["claude"],
                       True, False, False), 2)

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

    def test_solobuilder_remains_compatible_with_startup(self):
        self.assertEqual(
            di.install(REPO, self.target, ["claude"], False, False, False,
                       startup=True, personal=True), 0)
        brief = (self.target / "docs" / "brief.md").read_text("utf-8")
        self.assertIn("Delivery profile: solobuilder", brief)
        self.assertIn("Company profile: startup", brief)

    def test_verify_flag_runs_init_then_gates(self):
        # --verify must init state THEN run the gate suite, both in the
        # target; assert the plumbing (not the 9-min suite itself, which
        # has its own tests and would recurse through the copied tests).
        calls = []

        def fake_run(cmd, cwd=None, **kw):
            # cwd is None only for the installer's read-only `git ls-files`
            # against the SOURCE; every TARGET-side call passes cwd=target.
            # This test is about the target-side plumbing.
            if cwd is not None:
                calls.append((list(cmd), Path(cwd)))
            return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

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
            return type("R", (), {"returncode": 1 if hit else 0,
                                  "stdout": "", "stderr": ""})()

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
            # Record TARGET-side calls only. cwd is None solely for the
            # installer's read-only `git ls-files` against the SOURCE, which
            # executes nothing from the target and is not what this guards.
            if cwd is not None:
                calls.append(cmd)
            return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with mock.patch.object(di.subprocess, "run", fake_run):
            rc = di.install(REPO, self.target, ["claude"], False, False,
                            False, verify=True)
        self.assertEqual(rc, 2)
        self.assertEqual(calls, [])  # never executed the target's tools

    def test_no_verify_executes_nothing_from_the_target(self):
        """The property this protects is 'never execute the TARGET's tools' -
        the sibling verify tests say so, and the recorded failure is real: a
        --verify path once ran target-side tool files that copy_file had
        SKIPPED, i.e. unvetted code the installer had not written.

        Asserted by ORIGIN rather than by call count, because the installer now
        also asks git, read-only, which files the SOURCE tracks (so it stops
        shipping the source machine's settings.local.json). A bare
        `calls == []` would forbid that harmless source-side read while still
        permitting a target-side execution introduced under some other cwd.
        """
        calls = []

        def fake_run(cmd, cwd=None, **kw):
            calls.append((list(cmd), cwd))
            return type("R", (), {"returncode": 1, "stdout": "", "stderr": ""})()

        with mock.patch.object(di.subprocess, "run", fake_run):
            di.install(REPO, self.target, ["claude"], False, False, False)

        target = str(self.target)
        for cmd, cwd in calls:
            self.assertNotEqual(str(cwd), target,
                                f"ran a subprocess IN the target: {cmd}")
            self.assertNotIn(target, " ".join(str(c) for c in cmd),
                             f"executed something FROM the target: {cmd}")

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

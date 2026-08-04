"""Tests for tools/doctrine_gold.py — run: python -m unittest discover tests"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_chain_order_survives_clone(self):
        """Regression: G-1/GD-1 — order comes from prev-hash links, never
        mtimes (clones reset them; attackers forge them)."""
        import os
        self.record()
        for i, tag in enumerate(["v1.1.0", "v1.2.0"]):
            subprocess.run(["git", "tag", "-a", tag, "-m", "v"],
                           cwd=self.root, check=True)
            self.assertEqual(self.record(self.proposal(tag=tag)), 0)
        gold = self.root / "docs" / "releases" / "gold"
        # simulate clone: equalize, then REVERSE mtimes
        for i, p in enumerate(sorted(gold.glob("*.json"), reverse=True)):
            os.utime(p, (1000000 + i, 1000000 + i))
        chain = dg.load_chain(self.root)
        self.assertEqual([p.name for p in chain],
                         ["v1.0.0.json", "v1.1.0.json", "v1.2.0.json"])
        subprocess.run(["git", "tag", "-a", "v1.3.0", "-m", "v"],
                       cwd=self.root, check=True)
        self.assertEqual(self.record(self.proposal(tag="v1.3.0")), 0)
        fourth = json.loads((gold / "v1.3.0.json").read_text("utf-8"))
        self.assertEqual(fourth["prev_gold_sha256"],
                         ds.sha256_file(gold / "v1.2.0.json"),
                         "must chain to the true head, not the mtime head")
        self.assertEqual(dg.cmd_check(self.root, "v1.3.0"), 0)

    def test_forged_second_genesis_detected(self):
        """Regression: G-1 — a forged genesis breaks topology loudly."""
        self.record()
        gold = self.root / "docs" / "releases" / "gold"
        forged = json.loads((gold / "v1.0.0.json").read_text("utf-8"))
        forged["tag"] = "v9.9.9"
        (gold / "v9.9.9.json").write_bytes(ds.canonical_bytes(forged))
        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 1)

    def test_chain_fork_detected(self):
        """Regression: G-1 — two records claiming one predecessor."""
        self.record()
        subprocess.run(["git", "tag", "-a", "v1.1.0", "-m", "v"],
                       cwd=self.root, check=True)
        self.record(self.proposal(tag="v1.1.0"))
        gold = self.root / "docs" / "releases" / "gold"
        fork = json.loads((gold / "v1.1.0.json").read_text("utf-8"))
        fork["tag"] = "v1.1.1"
        (gold / "v1.1.1.json").write_bytes(ds.canonical_bytes(fork))
        self.assertEqual(dg.cmd_check(self.root, "v1.1.0"), 1)

    def test_empty_signoff_refused(self):
        """Regression: G-2 — existence is not evidence."""
        (self.root / "docs" / "qa" / "task-security.md").write_bytes(b"")
        with self.assertRaises(dg.StateError):
            self.record()
        self.assertFalse((self.root / "docs" / "releases").exists())

    def test_signoff_edited_after_promotion_fails_check(self):
        """Regression: G-2 — sign-offs are content-pinned."""
        self.record()
        p = self.root / "docs" / "qa" / "task-security.md"
        p.write_text(p.read_text("utf-8") + "\nretracted!\n",
                     encoding="utf-8")
        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 1)

    def test_lightweight_tag_refused(self):
        """Regression: GD-3 — annotated tags only."""
        subprocess.run(["git", "tag", "v2.0.0"], cwd=self.root, check=True)
        with self.assertRaises(dg.StateError):
            self.record(self.proposal(tag="v2.0.0"))

    def test_bad_tag_rejected_before_git_or_paths(self):
        """Regression: GD-4 — tag validated before argv/path use."""
        for bad in ("--all", "../secret", "v1.0.0; rm -rf", "HEAD"):
            with self.assertRaises(dg.StateError, msg=bad):
                dg.cmd_check(self.root, bad)
            with self.assertRaises(dg.StateError, msg=bad):
                self.record(self.proposal(tag=bad))

    def test_duplicate_artifact_paths_refused(self):
        """Regression: GD-6."""
        prop = self.proposal()
        prop["artifacts"] = [{"path": "dist/app.whl", "sha256": "0" * 64},
                             "dist/app.whl"]
        with self.assertRaises(dg.StateError):
            self.record(prop)

    def test_shape_tampered_record_fails_cleanly(self):
        """Regression: GD-2 — schema failure exits 1, no traceback."""
        self.record()
        out = self.root / "docs" / "releases" / "gold" / "v1.0.0.json"
        record = json.loads(out.read_text("utf-8"))
        record["artifacts"] = "not-a-list"
        out.write_bytes(ds.canonical_bytes(record))
        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 1)


class TestAttestation(GoldRepo):
    """Signature attestation: the chain proves WHAT was promoted, a signed
    tag proves WHO promoted it."""

    def test_an_unsigned_tag_is_recorded_as_unsigned(self):
        self.record()

        record = json.loads(
            (self.root / "docs" / "releases" / "gold" / "v1.0.0.json")
            .read_text("utf-8"))

        self.assertEqual(
            record["attestation"],
            {"signed": False, "signer": None, "key": None, "format": None})

    def test_require_signature_refuses_an_unsigned_tag(self):
        proposal = self.root / "gold-proposal.json"
        proposal.write_text(json.dumps(self.proposal()), encoding="utf-8")

        with self.assertRaises(dg.StateError) as raised:
            dg.cmd_record(self.root, proposal, require_signature=True)

        self.assertIn("no signature", str(raised.exception))
        self.assertFalse((self.root / "docs" / "releases" / "gold").exists(),
                         "a refused promotion must write nothing")

    def test_check_with_require_signature_refuses_an_unsigned_tag(self):
        self.record()

        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 0)
        self.assertEqual(
            dg.cmd_check(self.root, "v1.0.0", require_signature=True), 1)

    def test_records_written_before_attestation_still_validate(self):
        """Records are immutable: v0.6.x records must not become invalid."""
        self.record()
        out = self.root / "docs" / "releases" / "gold" / "v1.0.0.json"
        record = json.loads(out.read_text("utf-8"))
        del record["attestation"]
        out.write_bytes(ds.canonical_bytes(record))

        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 0)

    def test_a_record_that_claims_a_signature_fails_when_the_tag_lost_it(self):
        self.record()
        out = self.root / "docs" / "releases" / "gold" / "v1.0.0.json"
        record = json.loads(out.read_text("utf-8"))
        record["attestation"] = {"signed": True, "signer": "Someone",
                                 "key": "DEADBEEF"}
        out.write_bytes(ds.canonical_bytes(record))

        self.assertEqual(dg.cmd_check(self.root, "v1.0.0"), 1)


def _has(program: str) -> bool:
    return shutil.which(program) is not None


class TestRealSignedTags(GoldRepo):
    """End-to-end with REAL keys, one per backend git supports.

    Parse fixtures prove we read git's output correctly; only these prove the
    whole path - key, signature, git's verdict, our attestation - actually
    works. Each skips when its backend is absent rather than pretending.
    """

    def _promote(self, tag: str) -> dict:
        proposal = self.root / "gold-proposal.json"
        proposal.write_text(json.dumps(self.proposal(tag=tag)),
                            encoding="utf-8")
        self.assertEqual(
            dg.cmd_record(self.root, proposal, require_signature=True), 0,
            "--require-signature must accept a genuinely signed tag")
        return json.loads(
            (self.root / "docs" / "releases" / "gold" / f"{tag}.json")
            .read_text("utf-8"))

    @unittest.skipUnless(_has("ssh-keygen"), "ssh-keygen not available")
    def test_ssh_signed_tag_verifies_and_is_attested(self):
        key = self.root / "signing_key"
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-C",
                        "doctrine-test@example.invalid", "-f", str(key)],
                       check=True, capture_output=True)
        public = (self.root / "signing_key.pub").read_text("utf-8").strip()
        allowed = self.root / "allowed_signers"
        allowed.write_text(f"doctrine-test@example.invalid {public}\n",
                           encoding="utf-8")
        for name, value in (("gpg.format", "ssh"),
                            ("user.signingkey", str(key)),
                            ("gpg.ssh.allowedSignersFile", str(allowed)),
                            ("user.email", "doctrine-test@example.invalid")):
            subprocess.run(["git", "config", name, value], cwd=self.root,
                           check=True, capture_output=True)
        subprocess.run(["git", "tag", "-s", "v2.0.0", "-m", "signed"],
                       cwd=self.root, check=True, capture_output=True)

        attestation = dg.verify_tag_signature(self.root, "v2.0.0")

        self.assertTrue(attestation["signed"], attestation)
        self.assertEqual(attestation["format"], "ssh")
        self.assertEqual(attestation["signer"], "doctrine-test@example.invalid")
        self.assertTrue(attestation["key"].startswith("SHA256:"),
                        attestation["key"])
        self.assertEqual(self._promote("v2.0.0")["attestation"], attestation)

    def _ssh_signer(self, name: str) -> str:
        """Configure a fresh ssh signing identity; return its email."""
        email = f"{name}@example.invalid"
        key = self.root / f"key_{name}"
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-C", email,
                        "-f", str(key)], check=True, capture_output=True)
        public = (self.root / f"key_{name}.pub").read_text("utf-8").strip()
        allowed = self.root / "allowed_signers"
        with allowed.open("a", encoding="utf-8") as handle:
            handle.write(f"{email} {public}\n")
        for setting, value in (("gpg.format", "ssh"),
                               ("user.signingkey", str(key)),
                               ("gpg.ssh.allowedSignersFile", str(allowed)),
                               ("user.email", email)):
            subprocess.run(["git", "config", setting, value], cwd=self.root,
                           check=True, capture_output=True)
        return email

    @unittest.skipUnless(_has("ssh-keygen"), "ssh-keygen not available")
    def test_resigning_the_tag_as_someone_else_fails_the_deploy_gate(self):
        """Regression: an independent security pass deleted the tag, re-cut
        it at the SAME commit with a second key, and `check
        --require-signature` printed GOLD and exited 0 while the record still
        credited the first signer. Any principal in the trust store could
        re-attribute a promotion."""
        alice = self._ssh_signer("alice")
        subprocess.run(["git", "tag", "-s", "v4.0.0", "-m", "signed"],
                       cwd=self.root, check=True, capture_output=True)
        record = self._promote("v4.0.0")
        self.assertEqual(record["attestation"]["signer"], alice)
        self.assertEqual(
            dg.cmd_check(self.root, "v4.0.0", require_signature=True), 0)

        subprocess.run(["git", "tag", "-d", "v4.0.0"], cwd=self.root,
                       check=True, capture_output=True)
        mallory = self._ssh_signer("mallory")
        subprocess.run(["git", "tag", "-s", "v4.0.0", "-m", "signed"],
                       cwd=self.root, check=True, capture_output=True)

        self.assertNotEqual(alice, mallory)
        self.assertTrue(
            dg.verify_tag_signature(self.root, "v4.0.0")["signed"],
            "the re-cut tag must be genuinely signed, or this proves nothing")
        self.assertEqual(dg.cmd_check(self.root, "v4.0.0"), 1)
        self.assertEqual(
            dg.cmd_check(self.root, "v4.0.0", require_signature=True), 1)

    @unittest.skipUnless(_has("ssh-keygen"), "ssh-keygen not available")
    def test_a_signed_record_naming_nobody_fails_require_signature(self):
        """Regression: a record claiming signed:true with signer=key=null
        skipped the identity comparison (which needs both sides set) and
        passed the gate whose whole purpose is to prove WHO promoted."""
        self._ssh_signer("alice")
        subprocess.run(["git", "tag", "-s", "v6.0.0", "-m", "signed"],
                       cwd=self.root, check=True, capture_output=True)
        self._promote("v6.0.0")
        out = self.root / "docs" / "releases" / "gold" / "v6.0.0.json"
        record = json.loads(out.read_text("utf-8"))
        record["attestation"] = {"signed": True, "signer": None, "key": None,
                                 "format": "ssh"}
        out.write_bytes(ds.canonical_bytes(record))

        self.assertEqual(
            dg.cmd_check(self.root, "v6.0.0", require_signature=True), 1)

    @unittest.skipUnless(_has("ssh-keygen"), "ssh-keygen not available")
    def test_a_record_without_attestation_cannot_claim_a_signed_promotion(self):
        """Regression: a forged record could omit `attestation` entirely and
        skip the comparison, so `--require-signature` passed on a record that
        proved nothing."""
        self._ssh_signer("alice")
        subprocess.run(["git", "tag", "-s", "v5.0.0", "-m", "signed"],
                       cwd=self.root, check=True, capture_output=True)
        self._promote("v5.0.0")
        out = self.root / "docs" / "releases" / "gold" / "v5.0.0.json"
        record = json.loads(out.read_text("utf-8"))
        del record["attestation"]
        out.write_bytes(ds.canonical_bytes(record))

        self.assertEqual(dg.cmd_check(self.root, "v5.0.0"), 0)
        self.assertEqual(
            dg.cmd_check(self.root, "v5.0.0", require_signature=True), 1)

    @unittest.skipUnless(_has("gpg"), "gpg not available")
    def test_openpgp_signed_tag_verifies_and_is_attested(self):
        home = self.root / "gnupg"
        home.mkdir(mode=0o700)
        environment = {**os.environ, "GNUPGHOME": str(home)}
        generated = subprocess.run(
            ["gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase",
             "", "--quick-generate-key", "Doctrine Test "
             "<doctrine-test@example.invalid>", "ed25519", "sign", "never"],
            env=environment, capture_output=True, text=True, timeout=120)
        if generated.returncode != 0:
            self.skipTest(f"gpg could not generate a key here: "
                          f"{generated.stderr.strip()[:200]}")
        listed = subprocess.run(
            ["gpg", "--list-secret-keys", "--with-colons"], env=environment,
            capture_output=True, text=True, check=True)
        fingerprint = next(line.split(":")[9] for line in
                           listed.stdout.splitlines() if line.startswith("fpr"))
        for name, value in (("gpg.format", "openpgp"),
                            ("user.signingkey", fingerprint),
                            ("user.email", "doctrine-test@example.invalid")):
            subprocess.run(["git", "config", name, value], cwd=self.root,
                           check=True, capture_output=True)
        tagged = subprocess.run(
            ["git", "tag", "-s", "v3.0.0", "-m", "signed"], cwd=self.root,
            env=environment, capture_output=True, text=True)
        if tagged.returncode != 0:
            self.skipTest(f"gpg could not sign here: "
                          f"{tagged.stderr.strip()[:200]}")

        with mock.patch.dict(os.environ, {"GNUPGHOME": str(home)}):
            attestation = dg.verify_tag_signature(self.root, "v3.0.0")
            self.assertTrue(attestation["signed"], attestation)
            self.assertEqual(attestation["format"], "openpgp")
            self.assertIn("Doctrine Test", attestation["signer"] or "")
            self.assertEqual(self._promote("v3.0.0")["attestation"],
                             attestation)


class TestGate(GoldRepo):
    """The backstop that does not depend on intercepting the writer.

    Three independent security passes each found new shell spellings that
    reached a protected file, because static analysis of a Turing-complete
    shell cannot be complete. This gate asks a different question - do the
    recorded hashes still match? - which no spelling can dodge.
    """

    def test_an_empty_repo_passes(self):
        self.assertEqual(dg.cmd_gate(self.root), 0)

    def test_every_record_is_verified(self):
        self.record()

        self.assertEqual(dg.cmd_gate(self.root), 0)

    def test_tampering_fails_the_gate_however_it_was_written(self):
        self.record()
        artifact = self.root / "dist" / "app.whl"

        # Not through any tool the guard can see: straight to the filesystem.
        artifact.write_bytes(b"artifact-bytes-TAMPERED")

        self.assertEqual(dg.cmd_gate(self.root), 1)

    def test_a_record_that_is_not_a_version_is_refused(self):
        self.record()
        gold = self.root / "docs" / "releases" / "gold"
        (gold / "notes.json").write_text("{}", encoding="utf-8")

        self.assertEqual(dg.cmd_gate(self.root), 1)


class TestSignatureParsing(unittest.TestCase):
    """The parse is pure so it is testable without provisioning a key.

    Fixtures are git's real output shapes; the parser fails CLOSED on
    anything it does not recognise, so a format drift can only ever
    under-report a signature, never invent one.
    """

    def test_gpg_good_signature_yields_signer_and_fingerprint(self):
        raw = (
            "[GNUPG:] NEWSIG\n"
            "[GNUPG:] GOODSIG 4AEE18F83AFDEB23 Ada Lovelace <ada@example.org>\n"
            "[GNUPG:] VALIDSIG "
            "ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234 2026-08-03\n"
        )

        self.assertEqual(
            dg.parse_signature_status(0, raw, "openpgp"),
            {"signed": True, "signer": "Ada Lovelace <ada@example.org>",
             "key": "ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234",
             "format": "openpgp"},
        )

    def test_ssh_good_signature_is_recognised(self):
        raw = ('Good "git" signature for ada@example.org with ED25519 key '
               "SHA256:abcdef0123456789\n")

        self.assertEqual(
            dg.parse_signature_status(0, raw, "ssh"),
            {"signed": True, "signer": "ada@example.org",
             "key": "SHA256:abcdef0123456789", "format": "ssh"},
        )

    def test_x509_good_signature_is_recognised(self):
        """gpgsm speaks the same status protocol as gpg; only the armor
        header distinguishes the backend, which is why format detection
        reads the tag object rather than the verifier's chatter."""
        raw = (
            "[GNUPG:] NEWSIG\n"
            "[GNUPG:] GOODSIG 0F1E2D3C4B5A6978 "
            "/CN=Ada Lovelace/O=Example Ltd/C=GB\n"
            "[GNUPG:] TRUST_FULLY 0 shell\n"
        )

        self.assertEqual(
            dg.parse_signature_status(0, raw, "x509"),
            {"signed": True, "signer": "/CN=Ada Lovelace/O=Example Ltd/C=GB",
             "key": "0F1E2D3C4B5A6978", "format": "x509"},
        )

    def test_the_backend_is_read_from_the_tag_objects_armor(self):
        for marker, expected in (
                ("-----BEGIN SSH SIGNATURE-----", "ssh"),
                ("-----BEGIN PGP SIGNATURE-----", "openpgp"),
                ("-----BEGIN PGP MESSAGE-----", "openpgp"),
                ("-----BEGIN SIGNED MESSAGE-----", "x509")):
            with self.subTest(marker=marker):
                self.assertEqual(
                    dg.detect_signature_format(
                        f"object abc\ntype commit\ntag v1.0.0\n\nmsg\n"
                        f"{marker}\nblob\n"),
                    expected)

    def test_an_unsigned_tag_object_has_no_format(self):
        self.assertIsNone(dg.detect_signature_format(
            "object abc\ntype commit\ntag v1.0.0\n\njust a message\n"))

    def test_a_failed_verification_is_never_reported_as_signed(self):
        for code, raw in ((1, "error: no signature found\n"),
                          (1, "[GNUPG:] BADSIG 4AEE18F83AFDEB23 Ada\n"),
                          (0, "some output git never produced")):
            with self.subTest(code=code):
                self.assertEqual(
                    dg.parse_signature_status(code, raw),
                    {"signed": False, "signer": None, "key": None,
                     "format": None})

    def test_a_signature_git_rejects_is_unsigned_whatever_the_armor_says(self):
        """A tag CARRYING a signature block that fails verification must not
        be reported as signed - the armor names the backend, git decides."""
        self.assertEqual(
            dg.parse_signature_status(1, "[GNUPG:] EXPKEYSIG abc Ada\n",
                                      "openpgp"),
            {"signed": False, "signer": None, "key": None, "format": None})


if __name__ == "__main__":
    unittest.main()

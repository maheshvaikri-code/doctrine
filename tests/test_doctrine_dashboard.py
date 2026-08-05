"""Tests for the loopback Doctrine operations bridge consumed by local clients."""
from __future__ import annotations

import contextlib
import json
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import doctrine_dashboard as dashboard  # noqa: E402


def _run(repo: Path, *arguments: str) -> None:
    subprocess.run(
        list(arguments),
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
    )


def _make_repo(root: Path) -> None:
    (root / ".Doctrine").mkdir()
    (root / ".Doctrine.md").write_text("# Doctrine\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("boot\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text(
        "@.Doctrine.md\n@.doctrine-state/local/hydration.bundle.md\n",
        encoding="utf-8",
    )
    (root / "tools").mkdir()
    (root / "tools" / "doctrine_engage.py").write_text(
        "# present\n",
        encoding="utf-8",
    )
    (root / ".doctrine-state").mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [{"hooks": [{"type": "command"}]}],
                    "UserPromptSubmit": [{"hooks": [{"type": "command"}]}],
                }
            }
        ),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        '[project]\nname = "example-doctrine"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    _run(root, "git", "init", "-q")
    _run(root, "git", "config", "user.email", "test@example.invalid")
    _run(root, "git", "config", "user.name", "Doctrine Test")
    _run(root, "git", "add", ".")
    _run(root, "git", "commit", "-qm", "feat: initialize example")
    _run(root, "git", "tag", "v0.1.0")


def _wait_for_completion(
    store: dashboard.VerificationStore,
) -> dict[str, object]:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        current = store.current()
        if current["status"] != "running":
            return current
        time.sleep(0.01)
    raise AssertionError("verification did not complete")


class TestSnapshot(unittest.TestCase):
    def test_collects_truthful_repository_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            _make_repo(repo)
            store = dashboard.VerificationStore(repo)

            snapshot = dashboard.collect_snapshot(repo, store)

            self.assertEqual(snapshot["apiVersion"], "1")
            self.assertEqual(snapshot["repository"]["name"], "example-doctrine")
            self.assertEqual(snapshot["repository"]["version"], "0.1.0")
            self.assertFalse(snapshot["repository"]["isDirty"])
            self.assertGreater(snapshot["repository"]["trackedFiles"], 0)
            self.assertEqual(snapshot["activation"]["status"], "healthy")
            self.assertEqual(snapshot["statePlane"]["status"], "missing")
            self.assertEqual(snapshot["release"]["status"], "current")
            self.assertEqual(snapshot["release"]["latestTag"], "v0.1.0")
            self.assertEqual(snapshot["verification"]["status"], "never_run")
            self.assertIn(
                "Verification has not run from this bridge.",
                snapshot["partialReasons"],
            )
            self.assertEqual(
                snapshot["evidence"]["activity"][0]["title"],
                "feat: initialize example",
            )
            self.assertEqual(sum(snapshot["evidence"]["trend"]["7D"]), 1)

    def test_missing_project_is_an_empty_connection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            _run(repo, "git", "init", "-q")
            store = dashboard.VerificationStore(repo)

            snapshot = dashboard.collect_snapshot(repo, store)

            self.assertFalse(snapshot["repository"]["connected"])
            self.assertIsNone(snapshot["repository"]["name"])


class TestVerificationStore(unittest.TestCase):
    def test_output_tail_is_strictly_bounded(self) -> None:
        output = dashboard._OutputTail(limit=5)

        output.append("abc")
        output.append("defghi")

        self.assertEqual(output.value(), "efghi")

    def test_default_runner_invalidates_a_changed_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            _make_repo(repo)
            (repo / "tools" / "doctrine_verify.py").write_text(
                "\n".join(
                    [
                        "from pathlib import Path",
                        'Path("changed-during-run.txt").write_text("dirty")',
                        'print("=== lint: PASS")',
                        'print("=== ruff: PASS")',
                        'print("=== tests: PASS")',
                        'print("=== state: PASS")',
                        'print("VERIFY OK: 4 gate(s) green")',
                    ]
                ),
                encoding="utf-8",
            )
            _run(repo, "git", "add", "tools/doctrine_verify.py")
            _run(repo, "git", "commit", "-qm", "test: add verifier")

            result = dashboard._default_verify_runner(repo)

            self.assertEqual(result.returncode, 1)
            self.assertIn("Repository changed during verification.", result.stdout)
            self.assertTrue(result.stdout.rstrip().endswith("=== state: FAIL"))

    def test_parses_passing_gate_evidence_and_test_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            output = "\n".join(
                [
                    "Ran 12 tests in 0.500s",
                    "=== lint: PASS",
                    "=== ruff: PASS",
                    "=== tests: PASS",
                    "=== state: PASS",
                    "VERIFY OK: 4 gate(s) green",
                ]
            )

            def runner(_: Path) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(
                    ["verify"],
                    0,
                    stdout=output,
                    stderr="",
                )

            store = dashboard.VerificationStore(repo, runner=runner)
            accepted = store.start("abc1234")
            result = _wait_for_completion(store)

            self.assertEqual(accepted["status"], "running")
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["testCount"], 12)
            self.assertEqual(
                [gate["status"] for gate in result["gates"]],
                ["passed", "passed", "passed", "passed"],
            )
            self.assertTrue(store.cache_path.is_file())

    def test_exit_zero_with_a_failed_gate_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            output = "\n".join(
                [
                    "=== lint: PASS",
                    "=== ruff: PASS",
                    "=== tests: FAIL",
                    "=== state: PASS",
                    "VERIFY OK: 4 gate(s) green",
                ]
            )

            def runner(_: Path) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(
                    ["verify"],
                    0,
                    stdout=output,
                    stderr="",
                )

            store = dashboard.VerificationStore(repo, runner=runner)
            store.start("abc1234")
            result = _wait_for_completion(store)

            self.assertEqual(result["status"], "failed")
            self.assertEqual(
                [gate["status"] for gate in result["gates"]],
                ["passed", "passed", "failed", "passed"],
            )

    def test_rejects_a_second_concurrent_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            release = threading.Event()

            def runner(_: Path) -> subprocess.CompletedProcess[str]:
                release.wait(2)
                return subprocess.CompletedProcess(["verify"], 1, "", "")

            store = dashboard.VerificationStore(repo, runner=runner)
            store.start("abc1234")

            with self.assertRaises(dashboard.VerificationInProgress):
                store.start("abc1234")

            release.set()
            _wait_for_completion(store)

    def test_unexpected_worker_failure_settles_the_job(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)

            def runner(_: Path) -> subprocess.CompletedProcess[str]:
                raise RuntimeError("synthetic worker defect")

            store = dashboard.VerificationStore(repo, runner=runner)
            with self.assertLogs("doctrine.dashboard", level="ERROR"):
                store.start("abc1234")
                result = _wait_for_completion(store)

            self.assertEqual(result["status"], "failed")
            self.assertEqual(
                result["summary"],
                "Doctrine verification stopped unexpectedly.",
            )


class TestHttpBoundary(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        _make_repo(self.repo)
        self.server = dashboard.create_server(self.repo, port=0)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def _request(
        self,
        path: str,
        *,
        origin: str = "http://localhost:3003",
        data: bytes | None = None,
        content_type: str | None = None,
    ) -> urllib.request.Request:
        headers = {"Origin": origin}
        if content_type:
            headers["Content-Type"] = content_type
        return urllib.request.Request(
            f"{self.base_url}{path}",
            headers=headers,
            data=data,
            method="POST" if data is not None else "GET",
        )

    def test_health_and_snapshot_allow_the_client_origin(self) -> None:
        for path in ("/api/v1/health", "/api/v1/snapshot"):
            with urllib.request.urlopen(self._request(path), timeout=2) as response:
                payload = json.load(response)
                self.assertEqual(response.status, 200)
                self.assertEqual(
                    response.headers["Access-Control-Allow-Origin"],
                    "http://localhost:3003",
                )
                self.assertEqual(payload["apiVersion"], "1")

    def test_rejects_unapproved_browser_origin(self) -> None:
        request = self._request(
            "/api/v1/snapshot",
            origin="https://untrusted.example",
        )

        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 403)
        payload = json.loads(raised.exception.read())
        self.assertEqual(payload["error"]["code"], "origin_not_allowed")

    def test_mutation_requires_json_and_an_empty_object(self) -> None:
        wrong_type = self._request(
            "/api/v1/verifications",
            data=b"{}",
            content_type="text/plain",
        )
        unexpected_input = self._request(
            "/api/v1/verifications",
            data=b'{"command":"anything"}',
            content_type="application/json",
        )

        with self.assertRaises(urllib.error.HTTPError) as wrong_type_error:
            urllib.request.urlopen(wrong_type, timeout=2)
        with self.assertRaises(urllib.error.HTTPError) as input_error:
            urllib.request.urlopen(unexpected_input, timeout=2)

        self.assertEqual(wrong_type_error.exception.code, 415)
        self.assertEqual(input_error.exception.code, 400)

    def test_early_rejection_answers_a_late_arriving_body(self) -> None:
        """Regression: a rejected POST must consume the body it announced.

        Answering and closing while the body is still in flight makes the late
        bytes land on a closed socket; the OS replies RST and the client loses
        the response (ConnectionAbortedError / WinError 10053). That race is
        what made this suite flake ~1 run in 6 under load. Sending the headers
        and the body in separate segments reproduces it deterministically.
        """
        headers = (
            b"POST /api/v1/verifications HTTP/1.0\r\n"
            b"Host: localhost\r\n"
            b"Origin: http://localhost:3003\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: 2\r\n"
            b"\r\n"
        )
        host, port = self.server.server_address
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(headers)
            time.sleep(0.3)      # a broken server answers and closes here
            sock.sendall(b"{}")  # ... and this lands on a closed socket
            received = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                received += chunk

        self.assertTrue(
            received.startswith(b"HTTP/1.0 415 "),
            f"expected a 415 status line, got {received[:60]!r}",
        )

    def test_oversized_rejection_survives_a_late_arriving_body(self) -> None:
        """Regression: the 413 branch opts out of the body drain by design,
        and had therefore inherited the very race the drain was added to fix.
        The original test sent NO body (data=None), so it could not observe
        this; a review measured 10/10 ConnectionAbortedError here.
        """
        body = b"x" * (dashboard.MAX_REQUEST_BYTES + 1)
        headers = (
            b"POST /api/v1/verifications HTTP/1.0\r\n"
            b"Host: localhost\r\n"
            b"Origin: http://localhost:3003\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n"
        )
        host, port = self.server.server_address
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(headers)
            time.sleep(0.3)     # the server answers 413 here, without reading
            with contextlib.suppress(OSError):
                sock.sendall(body)   # ...and this lands on a closing socket
            received = b""
            with contextlib.suppress(OSError):
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    received += chunk

        self.assertTrue(
            received.startswith(b"HTTP/1.0 413 "),
            f"expected a 413 status line, got {received[:60]!r}",
        )

    def test_rejects_a_rebound_host_name(self) -> None:
        """Regression: loopback binding does not stop DNS rebinding. A page
        that re-resolves its own name to 127.0.0.1 reaches this server
        same-origin, and browsers omit Origin on same-origin GET - so the
        origin check waved it through and the repository snapshot leaked.
        """
        request = (
            b"GET /api/v1/snapshot HTTP/1.0\r\n"
            b"Host: attacker.example.com\r\n"
            b"\r\n"
        )
        host, port = self.server.server_address
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(request)
            received = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                received += chunk

        self.assertTrue(received.startswith(b"HTTP/1.0 403 "),
                        f"expected 403, got {received[:60]!r}")
        self.assertIn(b"host_not_allowed", received)
        self.assertNotIn(b"trackedFiles", received)

    def test_a_loopback_host_is_still_served(self) -> None:
        for host_header in (b"localhost", b"127.0.0.1", b"localhost:8765"):
            with self.subTest(host=host_header):
                host, port = self.server.server_address
                with socket.create_connection((host, port), timeout=5) as sock:
                    sock.sendall(b"GET /api/v1/health HTTP/1.0\r\nHost: "
                                 + host_header + b"\r\n\r\n")
                    received = sock.recv(4096)
                self.assertTrue(received.startswith(b"HTTP/1.0 200 "),
                                f"got {received[:60]!r}")

    def test_rejects_oversized_mutation_before_reading_it(self) -> None:
        request = urllib.request.Request(
            f"{self.base_url}/api/v1/verifications",
            headers={
                "Origin": "http://localhost:3003",
                "Content-Type": "application/json",
                "Content-Length": str(dashboard.MAX_REQUEST_BYTES + 1),
            },
            method="POST",
        )

        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 413)
        payload = json.loads(raised.exception.read())
        self.assertEqual(payload["error"]["code"], "request_too_large")

    def test_rejects_verification_when_worktree_is_dirty(self) -> None:
        (self.repo / "uncommitted.txt").write_text(
            "not attributable to HEAD\n",
            encoding="utf-8",
        )
        request = self._request(
            "/api/v1/verifications",
            data=b"{}",
            content_type="application/json",
        )

        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 409)
        payload = json.loads(raised.exception.read())
        self.assertEqual(payload["error"]["code"], "worktree_dirty")


class TestContract(unittest.TestCase):
    def test_openapi_lists_only_the_bounded_v1_surface(self) -> None:
        root = Path(__file__).resolve().parents[1]
        contract = json.loads(
            (
                root
                / "docs"
                / "contracts"
                / "doctrine-control-room.openapi.json"
            ).read_text("utf-8")
        )

        self.assertEqual(
            contract["info"]["title"],
            "Doctrine Local Operations Bridge",
        )
        self.assertIn("local clients", contract["info"]["description"])
        self.assertEqual(
            set(contract["paths"]),
            {
                "/api/v1/health",
                "/api/v1/snapshot",
                "/api/v1/verifications/current",
                "/api/v1/verifications",
            },
        )
        self.assertEqual(
            contract["paths"]["/api/v1/verifications"].keys(),
            {"post"},
        )


if __name__ == "__main__":
    unittest.main()

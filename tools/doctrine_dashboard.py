"""Loopback-only runtime bridge for the Doctrine Control Room.

The browser cannot read a repository or execute Doctrine's Python tools. This
module exposes a deliberately small HTTP boundary: a bounded repository
snapshot and one allowlisted verification operation. It never accepts a
command or filesystem path from an HTTP request.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import logging
import re
import secrets
import subprocess
import sys
import threading
import tomllib
from collections import deque
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Final

import doctrine_awaken
import doctrine_state

API_VERSION: Final = "1"
SERVICE_NAME: Final = "doctrine-control-room-bridge"
DEFAULT_PORT: Final = 8765
MAX_REQUEST_BYTES: Final = 1024
MAX_OUTPUT_CHARS: Final = 32 * 1024
GIT_TIMEOUT_SECONDS: Final = 5
VERIFY_TIMEOUT_SECONDS: Final = 180
DEFAULT_ORIGINS: Final = frozenset(
    {"http://localhost:3003", "http://127.0.0.1:3003"}
)
GATE_LABELS: Final = {
    "lint": "Doctrine corpus",
    "ruff": "Python quality",
    "tests": "Tooling tests",
    "state": "State chain",
}
VERIFY_GATE_RE: Final = re.compile(
    r"^=== (lint|ruff|tests|state): (PASS|FAIL)\b", re.MULTILINE
)
TEST_COUNT_RE: Final = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
VERIFY_OK_RE: Final = re.compile(
    r"^VERIFY OK: (\d+) gate\(s\) green$", re.MULTILINE
)
LOGGER = logging.getLogger("doctrine.dashboard")


class SnapshotError(RuntimeError):
    """Repository metadata could not be collected."""


class VerificationInProgress(RuntimeError):
    """A second verification was requested while one is active."""


class DirtyWorktree(RuntimeError):
    """Verification evidence cannot be attributed to a dirty worktree."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _run_git(repo: Path, arguments: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SnapshotError("Git metadata is unavailable.") from exc
    if result.returncode != 0:
        raise SnapshotError("Git metadata is unavailable.")
    return result.stdout


def _read_project(repo: Path) -> tuple[str | None, str | None]:
    path = repo / "pyproject.toml"
    if not path.is_file():
        return None, None
    try:
        with path.open("rb") as stream:
            project = tomllib.load(stream).get("project", {})
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SnapshotError("Project metadata is malformed.") from exc
    if not isinstance(project, dict):
        raise SnapshotError("Project metadata has no project table.")
    name = project.get("name")
    version = project.get("version")
    return (
        name if isinstance(name, str) else None,
        version if isinstance(version, str) else None,
    )


def _collect_activity(repo: Path) -> list[dict[str, str]]:
    output = _run_git(
        repo,
        ["log", "-8", "--format=%h%x1f%cI%x1f%s%x1e"],
    )
    activity: list[dict[str, str]] = []
    for record in output.split("\x1e"):
        parts = record.strip().split("\x1f")
        if len(parts) != 3:
            continue
        commit, occurred_at, title = parts
        activity.append(
            {
                "commit": commit[:12],
                "occurredAt": occurred_at,
                "title": title[:160],
            }
        )
    return activity


def _bucket_commits(
    timestamps: Sequence[datetime],
    *,
    days: int,
    buckets: int,
    now: datetime,
) -> list[int]:
    start = now - timedelta(days=days)
    counts = [0] * buckets
    for timestamp in timestamps:
        if timestamp < start or timestamp > now + timedelta(minutes=5):
            continue
        elapsed = (timestamp - start).total_seconds()
        position = min(int(elapsed * buckets / (days * 86400)), buckets - 1)
        counts[max(position, 0)] += 1
    return counts


def _collect_trend(repo: Path, now: datetime) -> dict[str, list[int]]:
    output = _run_git(repo, ["log", "--since=90.days", "--format=%cI"])
    timestamps: list[datetime] = []
    for raw in output.splitlines():
        try:
            timestamp = datetime.fromisoformat(raw.strip())
        except ValueError:
            continue
        timestamps.append(timestamp.astimezone(UTC))
    return {
        "7D": _bucket_commits(timestamps, days=7, buckets=7, now=now),
        "30D": _bucket_commits(timestamps, days=30, buckets=10, now=now),
        "90D": _bucket_commits(timestamps, days=90, buckets=12, now=now),
    }


def _count_files(path: Path, pattern: str) -> int:
    return sum(1 for candidate in path.glob(pattern) if candidate.is_file())


def _collect_activation(repo: Path) -> dict[str, Any]:
    rows, awake = doctrine_awaken.audit(repo)
    status_map = {
        doctrine_awaken.OK: "pass",
        doctrine_awaken.WARN: "warning",
        doctrine_awaken.MISS: "failed",
    }
    return {
        "status": "healthy" if awake else "degraded",
        "passing": sum(1 for marker, _, _ in rows if marker == doctrine_awaken.OK),
        "total": len(rows),
        "findings": [
            {"status": status_map[marker], "message": message}
            for marker, message, _ in rows
        ],
    }


def _collect_state_plane(repo: Path) -> dict[str, Any]:
    checkpoint_path = repo / ".doctrine-state" / "checkpoint.json"
    if not checkpoint_path.is_file():
        return {
            "status": "missing",
            "checkpointSeq": None,
            "checkpointCommit": None,
            "checkpoints": 0,
            "unresolvedEffects": 0,
            "role": None,
            "phase": None,
        }
    try:
        checkpoint = json.loads(checkpoint_path.read_text("utf-8"))
    except (OSError, ValueError) as exc:
        raise SnapshotError("State checkpoint is unreadable.") from exc
    if not isinstance(checkpoint, dict):
        raise SnapshotError("State checkpoint is malformed.")

    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            verify_code = doctrine_state.cmd_verify(doctrine_state.Plane(repo))
        except (doctrine_state.SchemaError, doctrine_state.StateError):
            verify_code = 1

    control = checkpoint.get("control", {})
    state_index = checkpoint.get("state_index", {})
    checkpoints_path = repo / ".doctrine-state" / "checkpoints"
    sequence = checkpoint.get("seq")
    checkpoint_commit = checkpoint.get("at_commit")
    unresolved_effects = (
        state_index.get("unresolved_effects", 0)
        if isinstance(state_index, dict)
        else 0
    )
    return {
        "status": "healthy" if verify_code == 0 else "degraded",
        "checkpointSeq": (
            sequence
            if isinstance(sequence, int)
            and not isinstance(sequence, bool)
            and sequence >= 0
            else None
        ),
        "checkpointCommit": (
            checkpoint_commit if isinstance(checkpoint_commit, str) else None
        ),
        "checkpoints": _count_files(checkpoints_path, "*.json"),
        "unresolvedEffects": (
            unresolved_effects
            if isinstance(unresolved_effects, int)
            and not isinstance(unresolved_effects, bool)
            and unresolved_effects >= 0
            else 0
        ),
        "role": (
            control.get("role")
            if isinstance(control, dict)
            and isinstance(control.get("role"), str)
            else None
        ),
        "phase": (
            control.get("phase")
            if isinstance(control, dict)
            and isinstance(control.get("phase"), str)
            else None
        ),
    }


def _empty_gates(status: str = "unknown") -> list[dict[str, str]]:
    return [
        {
            "key": key,
            "label": label,
            "status": status,
            "evidence": (
                "Verification in progress"
                if status == "running"
                else "Not run for this commit"
            ),
        }
        for key, label in GATE_LABELS.items()
    ]


def empty_verification() -> dict[str, Any]:
    """Return the public representation of a never-run verification."""
    return {
        "id": None,
        "status": "never_run",
        "commit": None,
        "startedAt": None,
        "finishedAt": None,
        "exitCode": None,
        "testCount": None,
        "summary": "Verification has not run for this repository.",
        "gates": _empty_gates(),
    }


Runner = Callable[[Path], subprocess.CompletedProcess[str]]


class _OutputTail:
    """Keep only the newest bounded output while a subprocess is running."""

    def __init__(self, limit: int = MAX_OUTPUT_CHARS) -> None:
        self.limit = limit
        self.chunks: deque[str] = deque()
        self.length = 0

    def append(self, chunk: str) -> None:
        self.chunks.append(chunk)
        self.length += len(chunk)
        overflow = self.length - self.limit
        while overflow > 0 and self.chunks:
            first = self.chunks[0]
            if len(first) <= overflow:
                self.chunks.popleft()
                self.length -= len(first)
                overflow = self.length - self.limit
            else:
                self.chunks[0] = first[overflow:]
                self.length -= overflow
                overflow = 0

    def value(self) -> str:
        return "".join(self.chunks)


def _default_verify_runner(repo: Path) -> subprocess.CompletedProcess[str]:
    verifier = repo / "tools" / "doctrine_verify.py"
    if not verifier.is_file():
        raise OSError("Doctrine verifier is unavailable.")
    arguments = [sys.executable, str(verifier)]
    process = subprocess.Popen(
        arguments,
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.stdout is None:
        process.kill()
        raise OSError("Doctrine verifier output stream is unavailable.")
    output = _OutputTail()

    def consume() -> None:
        for chunk in iter(lambda: process.stdout.read(4096), ""):
            output.append(chunk)

    reader = threading.Thread(
        target=consume,
        daemon=True,
        name="doctrine-verification-output",
    )
    reader.start()
    try:
        return_code = process.wait(timeout=VERIFY_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        reader.join(timeout=5)
        process.stdout.close()
        raise
    reader.join(timeout=5)
    process.stdout.close()
    return subprocess.CompletedProcess(
        arguments,
        return_code,
        stdout=output.value(),
        stderr="",
    )


def _parse_verification(
    *,
    job_id: str,
    commit: str | None,
    started_at: str,
    finished_at: str,
    result: subprocess.CompletedProcess[str],
) -> dict[str, Any]:
    output = f"{result.stdout}\n{result.stderr}"[-MAX_OUTPUT_CHARS:]
    observed: dict[str, str] = {}
    for key, verdict in VERIFY_GATE_RE.findall(output):
        observed[key] = verdict.lower()

    gates: list[dict[str, str]] = []
    test_counts = TEST_COUNT_RE.findall(output)
    test_count = int(test_counts[-1]) if test_counts else None
    for key, label in GATE_LABELS.items():
        verdict = observed.get(key)
        status = "passed" if verdict == "pass" else "failed"
        if verdict is None:
            status = "failed" if result.returncode else "unknown"
        evidence = "Passed"
        if key == "tests" and test_count is not None and status == "passed":
            evidence = f"{test_count} tests passed"
        elif status == "failed":
            evidence = "Gate failed"
        elif status == "unknown":
            evidence = "Gate result unavailable"
        gates.append(
            {
                "key": key,
                "label": label,
                "status": status,
                "evidence": evidence,
            }
        )

    ok_matches = VERIFY_OK_RE.findall(output)
    passed = result.returncode == 0 and len(observed) == len(GATE_LABELS)
    if passed and ok_matches:
        summary = f"{ok_matches[-1]} Doctrine gates passed."
    elif passed:
        summary = "Doctrine verification passed."
    else:
        summary = "Doctrine verification failed. Inspect the terminal output."
    return {
        "id": job_id,
        "status": "passed" if passed else "failed",
        "commit": commit,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "exitCode": result.returncode,
        "testCount": test_count,
        "summary": summary,
        "gates": gates,
    }


class VerificationStore:
    """Thread-safe single-job verification state with machine-local caching."""

    def __init__(
        self,
        repo: Path,
        runner: Runner = _default_verify_runner,
    ) -> None:
        self.repo = repo
        self.runner = runner
        self.cache_path = (
            repo / ".doctrine-state" / "local" / "dashboard-verification.json"
        )
        self._lock = threading.Lock()
        self._current = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        try:
            value = json.loads(self.cache_path.read_text("utf-8"))
        except (OSError, ValueError):
            return empty_verification()
        if not isinstance(value, dict) or value.get("status") == "running":
            return empty_verification()
        required = set(empty_verification())
        return value if set(value) == required else empty_verification()

    def current(self) -> dict[str, Any]:
        """Return an isolated copy of the current public job state."""
        with self._lock:
            return copy.deepcopy(self._current)

    def start(self, commit: str | None) -> dict[str, Any]:
        """Start one bounded verification or reject a concurrent request."""
        with self._lock:
            if self._current["status"] == "running":
                raise VerificationInProgress(
                    "A Doctrine verification is already running."
                )
            job_id = secrets.token_hex(8)
            started_at = _now_iso()
            self._current = {
                "id": job_id,
                "status": "running",
                "commit": commit,
                "startedAt": started_at,
                "finishedAt": None,
                "exitCode": None,
                "testCount": None,
                "summary": "Doctrine verification is running.",
                "gates": _empty_gates("running"),
            }
            public = copy.deepcopy(self._current)
        threading.Thread(
            target=self._execute,
            args=(job_id, commit, started_at),
            daemon=True,
            name="doctrine-verification",
        ).start()
        return public

    def _execute(
        self,
        job_id: str,
        commit: str | None,
        started_at: str,
    ) -> None:
        try:
            result = self.runner(self.repo)
            final = _parse_verification(
                job_id=job_id,
                commit=commit,
                started_at=started_at,
                finished_at=_now_iso(),
                result=result,
            )
        except subprocess.TimeoutExpired:
            final = {
                **empty_verification(),
                "id": job_id,
                "status": "timed_out",
                "commit": commit,
                "startedAt": started_at,
                "finishedAt": _now_iso(),
                "summary": "Doctrine verification exceeded 180 seconds.",
                "gates": [
                    {**gate, "status": "failed", "evidence": "Run timed out"}
                    for gate in _empty_gates()
                ],
            }
        except OSError:
            final = {
                **empty_verification(),
                "id": job_id,
                "status": "failed",
                "commit": commit,
                "startedAt": started_at,
                "finishedAt": _now_iso(),
                "summary": "Doctrine verification could not start.",
                "gates": [
                    {
                        **gate,
                        "status": "failed",
                        "evidence": "Verifier unavailable",
                    }
                    for gate in _empty_gates()
                ],
            }
        except Exception:
            LOGGER.exception("unexpected Doctrine verification worker failure")
            final = {
                **empty_verification(),
                "id": job_id,
                "status": "failed",
                "commit": commit,
                "startedAt": started_at,
                "finishedAt": _now_iso(),
                "summary": "Doctrine verification stopped unexpectedly.",
                "gates": [
                    {
                        **gate,
                        "status": "failed",
                        "evidence": "Worker stopped unexpectedly",
                    }
                    for gate in _empty_gates()
                ],
            }
        with self._lock:
            if self._current.get("id") != job_id:
                return
            self._current = final
            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                self.cache_path.write_text(
                    json.dumps(final, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            except OSError:
                LOGGER.warning("verification completed but its local cache failed")


def collect_snapshot(
    repo: Path,
    verification_store: VerificationStore,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Collect one current, bounded repository snapshot."""
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    partial_reasons: list[str] = []
    name, version = _read_project(repo)
    connected = (repo / ".Doctrine.md").is_file() and name is not None

    branch: str | None = None
    commit: str | None = None
    is_dirty = False
    tracked_files = 0
    latest_tag: str | None = None
    commits_ahead: int | None = None
    activity: list[dict[str, str]] = []
    trend = {"7D": [0], "30D": [0], "90D": [0]}
    try:
        branch = _run_git(repo, ["branch", "--show-current"]).strip() or None
        commit = _run_git(repo, ["rev-parse", "--short=12", "HEAD"]).strip()
        is_dirty = bool(_run_git(repo, ["status", "--porcelain=v1"]).strip())
        tracked_files = len(
            [item for item in _run_git(repo, ["ls-files", "-z"]).split("\0") if item]
        )
        activity = _collect_activity(repo)
        trend = _collect_trend(repo, current_time)
        try:
            latest_tag = (
                _run_git(repo, ["describe", "--tags", "--abbrev=0"]).strip() or None
            )
        except SnapshotError:
            latest_tag = None
        if latest_tag:
            commits_ahead = int(
                _run_git(repo, ["rev-list", "--count", f"{latest_tag}..HEAD"]).strip()
            )
    except (SnapshotError, ValueError):
        partial_reasons.append("Git metadata is incomplete.")

    activation = _collect_activation(repo)
    if activation["status"] != "healthy":
        partial_reasons.append("Doctrine activation has a critical gap.")
    elif activation["passing"] < activation["total"]:
        partial_reasons.append("Recommended Doctrine activation wiring is incomplete.")

    try:
        state_plane = _collect_state_plane(repo)
    except SnapshotError:
        state_plane = {
            "status": "degraded",
            "checkpointSeq": None,
            "checkpointCommit": None,
            "checkpoints": 0,
            "unresolvedEffects": 0,
            "role": None,
            "phase": None,
        }
    if state_plane["status"] != "healthy":
        partial_reasons.append("Doctrine state-chain evidence is unavailable.")

    verification = verification_store.current()
    if verification["status"] == "never_run":
        partial_reasons.append("Verification has not run from this bridge.")
    elif verification["commit"] != commit:
        partial_reasons.append("The latest verification belongs to another commit.")

    release_status = "unreleased"
    if latest_tag and commits_ahead == 0 and latest_tag == f"v{version}":
        release_status = "current"
    elif latest_tag:
        release_status = "ahead"

    return {
        "apiVersion": API_VERSION,
        "generatedAt": current_time.isoformat().replace("+00:00", "Z"),
        "partialReasons": partial_reasons[:12],
        "repository": {
            "connected": connected,
            "name": name,
            "version": version,
            "branch": branch,
            "commit": commit,
            "isDirty": is_dirty,
            "trackedFiles": tracked_files,
        },
        "activation": activation,
        "statePlane": state_plane,
        "verification": verification,
        "evidence": {
            "reviews": _count_files(repo / "docs" / "reviews", "*.md"),
            "qaReports": _count_files(repo / "docs" / "qa", "*.md"),
            "adrs": _count_files(repo / "docs" / "adr", "*.md"),
            "plans": _count_files(repo / "docs" / "plans", "*.md"),
            "goldRecords": _count_files(repo / "docs" / "releases" / "gold", "*.json"),
            "trend": trend,
            "activity": activity,
        },
        "release": {
            "currentVersion": version,
            "latestTag": latest_tag,
            "commitsAhead": commits_ahead,
            "status": release_status,
        },
    }


class BridgeApplication:
    """Owns repository services used by HTTP request handlers."""

    def __init__(
        self,
        repo: Path,
        allowed_origins: frozenset[str],
        verification_store: VerificationStore | None = None,
    ) -> None:
        self.repo = repo
        self.allowed_origins = allowed_origins
        self.verifications = verification_store or VerificationStore(repo)

    def snapshot(self) -> dict[str, Any]:
        return collect_snapshot(self.repo, self.verifications)


def _error(code: str, message: str, **details: object) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


def _handler_for(application: BridgeApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "DoctrineBridge/1"
        sys_version = ""

        def log_message(self, format: str, *args: object) -> None:
            return

        def _origin(self) -> str | None:
            return self.headers.get("Origin")

        def _origin_allowed(self) -> bool:
            origin = self._origin()
            return origin is None or origin in application.allowed_origins

        def _send_json(
            self,
            status: HTTPStatus,
            value: dict[str, Any],
        ) -> None:
            body = json.dumps(value, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            origin = self._origin()
            if origin in application.allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)

        def _reject_origin(self) -> bool:
            if self._origin_allowed():
                return False
            self._send_json(
                HTTPStatus.FORBIDDEN,
                _error(
                    "origin_not_allowed",
                    "This browser origin is not allowed to use the local bridge.",
                ),
            )
            return True

        def do_OPTIONS(self) -> None:
            if self._reject_origin():
                return
            self.send_response(HTTPStatus.NO_CONTENT)
            origin = self._origin()
            if origin in application.allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self) -> None:
            if self._reject_origin():
                return
            if self.path == "/api/v1/health":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "apiVersion": API_VERSION,
                        "service": SERVICE_NAME,
                        "status": "ok",
                    },
                )
                return
            if self.path == "/api/v1/snapshot":
                try:
                    snapshot = application.snapshot()
                except SnapshotError:
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        _error(
                            "snapshot_unavailable",
                            "The repository snapshot could not be collected.",
                        ),
                    )
                    return
                self._send_json(HTTPStatus.OK, snapshot)
                return
            if self.path == "/api/v1/verifications/current":
                self._send_json(
                    HTTPStatus.OK,
                    application.verifications.current(),
                )
                return
            self._send_json(
                HTTPStatus.NOT_FOUND,
                _error("not_found", "The requested bridge endpoint does not exist."),
            )

        def do_POST(self) -> None:
            if self._reject_origin():
                return
            if self.path != "/api/v1/verifications":
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    _error(
                        "not_found",
                        "The requested bridge endpoint does not exist.",
                    ),
                )
                return
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0]
            if content_type.lower() != "application/json":
                self._send_json(
                    HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                    _error(
                        "json_required",
                        "Verification requests must use application/json.",
                    ),
                )
                return
            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                content_length = -1
            if content_length < 0:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    _error("content_length_required", "Content-Length is required."),
                )
                return
            if content_length > MAX_REQUEST_BYTES:
                self._send_json(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    _error(
                        "request_too_large",
                        "The verification request exceeds 1 KiB.",
                    ),
                )
                return
            try:
                body = json.loads(self.rfile.read(content_length))
            except (UnicodeDecodeError, ValueError):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    _error("invalid_json", "The request body is not valid JSON."),
                )
                return
            if body != {}:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    _error(
                        "unexpected_input",
                        "Verification accepts an empty JSON object only.",
                    ),
                )
                return
            try:
                if _run_git(
                    application.repo,
                    ["status", "--porcelain=v1"],
                ).strip():
                    raise DirtyWorktree(
                        "Verification requires a clean worktree."
                    )
                commit = _run_git(
                    application.repo,
                    ["rev-parse", "--short=12", "HEAD"],
                ).strip()
                job = application.verifications.start(commit)
            except VerificationInProgress:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    _error(
                        "verification_in_progress",
                        "A Doctrine verification is already running.",
                    ),
                )
                return
            except DirtyWorktree:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    _error(
                        "worktree_dirty",
                        "Commit or stash local changes before verification.",
                    ),
                )
                return
            except SnapshotError:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    _error(
                        "repository_unavailable",
                        "The repository commit could not be resolved.",
                    ),
                )
                return
            self._send_json(HTTPStatus.ACCEPTED, job)

    return Handler


class BridgeServer(ThreadingHTTPServer):
    """Threaded HTTP server whose request threads cannot block shutdown."""

    daemon_threads = True


def create_server(
    repo: Path,
    *,
    port: int = DEFAULT_PORT,
    allowed_origins: frozenset[str] = DEFAULT_ORIGINS,
    verification_store: VerificationStore | None = None,
) -> BridgeServer:
    """Create a loopback bridge server without starting its event loop."""
    resolved_repo = repo.resolve()
    if not resolved_repo.is_dir():
        raise SnapshotError("Repository directory does not exist.")
    application = BridgeApplication(
        resolved_repo,
        allowed_origins,
        verification_store,
    )
    return BridgeServer(("127.0.0.1", port), _handler_for(application))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="doctrine-dashboard",
        description="Serve the loopback API for the Doctrine Control Room.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Doctrine repository to observe (default: current directory)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"loopback port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--origin",
        action="append",
        default=[],
        help="additional exact browser origin to allow; repeatable",
    )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    origins = frozenset({*DEFAULT_ORIGINS, *args.origin})
    try:
        server = create_server(args.repo, port=args.port, allowed_origins=origins)
    except (OSError, SnapshotError) as exc:
        parser.error(str(exc))
    host, port = server.server_address
    print(f"Doctrine Control Room bridge listening on http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Tests for hooks/SessionStart.py.

The hook is invoked as a subprocess, receives a JSON payload on stdin, and
emits either nothing (0 parks) or a JSON response with additionalContext.

Run from plugins/agent-meta/:
    python3 -m unittest discover tests -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = THIS_DIR.parent
HOOK = PLUGIN_DIR / "hooks" / "SessionStart.py"

sys.path.insert(0, str(PLUGIN_DIR))
from lib import park_storage as ps  # noqa: E402


def _run_hook(
    cwd: Path,
    session_id: str = "test-sess-1",
    parks_root: Path | None = None,
) -> subprocess.CompletedProcess:
    """Invoke SessionStart.py with a SessionStart payload on stdin."""
    payload = {"session_id": session_id, "cwd": str(cwd)}
    env = os.environ.copy()
    if parks_root is not None:
        env["CLAUDE_PARKS_ROOT"] = str(parks_root)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd),
    )


def _write_park(
    root: Path,
    key: str,
    slug: str,
    branch: str = "feat/test",
    status: str = "parked",
    parked_at: str = "2026-04-19T10:00:00",
) -> None:
    active = ps.ensure_park_dirs(key, root=root)
    park = ps.Park(
        slug=slug,
        status=status,
        parked_at=parked_at,
        branch=branch,
    )
    park.save(active / f"{slug}.md")


class ZeroParksTests(unittest.TestCase):
    """No active parks: hook exits 0, writes nothing to stdout."""

    def test_empty_parks_dir_exits_silently(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            result = _run_hook(repo)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_unknown_repo_key_exits_silently(self):
        """Repo key with no parks dir at all still exits cleanly."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "fresh"
            repo.mkdir()
            parks = Path(tmp) / "parks"
            parks.mkdir()
            result = _run_hook(repo, parks_root=parks)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")


class FewParksTests(unittest.TestCase):
    """1-8 parks: full list with branch column in additionalContext."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = self.tmp / "my-repo"
        self.repo.mkdir()
        self.parks = self.tmp / "parks"
        self.parks.mkdir()
        self.key = ps._slugify(str(self.repo.resolve()))

    def tearDown(self):
        self._tmp.cleanup()

    def _hook(self):
        return _run_hook(self.repo, parks_root=self.parks)

    def test_single_park_emits_additionalContext(self):
        _write_park(self.parks, self.key, "fix-auth-bug", "fix/auth-bug")
        result = self._hook()
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("fix-auth-bug", ctx)
        self.assertIn("fix/auth-bug", ctx)

    def test_output_has_correct_hookEventName(self):
        _write_park(self.parks, self.key, "test-park", "main")
        result = self._hook()
        data = json.loads(result.stdout)
        self.assertEqual(
            data["hookSpecificOutput"]["hookEventName"], "SessionStart"
        )

    def test_eight_parks_shows_all(self):
        for i in range(8):
            _write_park(self.parks, self.key, f"park-{i:02d}", f"feat/branch-{i}")
        result = self._hook()
        data = json.loads(result.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        for i in range(8):
            self.assertIn(f"park-{i:02d}", ctx)

    def test_context_mentions_park_count(self):
        for i in range(3):
            _write_park(self.parks, self.key, f"park-{i}", f"feat/b-{i}")
        result = self._hook()
        data = json.loads(result.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("3", ctx)

    def test_output_is_valid_json(self):
        _write_park(self.parks, self.key, "some-park", "main")
        result = self._hook()
        json.loads(result.stdout)  # must not raise


class ManyParksTests(unittest.TestCase):
    """>8 parks: collapsed one-line summary instead of full list."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = self.tmp / "big-repo"
        self.repo.mkdir()
        self.parks = self.tmp / "parks"
        self.parks.mkdir()
        self.key = ps._slugify(str(self.repo.resolve()))

    def tearDown(self):
        self._tmp.cleanup()

    def _write_n_parks(self, n: int) -> None:
        for i in range(n):
            _write_park(self.parks, self.key, f"park-{i:02d}", f"feat/branch-{i}")

    def _hook(self):
        return _run_hook(self.repo, parks_root=self.parks)

    def test_nine_parks_emits_collapsed_summary(self):
        self._write_n_parks(9)
        result = self._hook()
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("9", ctx)

    def test_collapsed_does_not_list_individual_parks(self):
        self._write_n_parks(9)
        result = self._hook()
        data = json.loads(result.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("park-00", ctx)

    def test_collapsed_mentions_audit(self):
        self._write_n_parks(9)
        result = self._hook()
        data = json.loads(result.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("audit", ctx.lower())

    def test_threshold_is_inclusive_at_eight(self):
        """Exactly 8 parks should still show the full list, not collapsed."""
        self._write_n_parks(8)
        result = self._hook()
        data = json.loads(result.stdout)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("park-00", ctx)


class InvalidInputTests(unittest.TestCase):
    def test_malformed_json_stdin_exits_cleanly(self):
        with TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input="not valid json {{",
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout.strip(), "")

    def test_empty_stdin_exits_cleanly(self):
        with TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input="",
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout.strip(), "")

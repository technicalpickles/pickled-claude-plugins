"""Tests for scripts/audit-parks.py.

Unit tests cover classify_park() directly via importlib (hyphenated filename).
Integration tests run the script as a subprocess for CLI modes.

Run from plugins/agent-meta/:
    python3 -m unittest discover tests -v
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = THIS_DIR.parent
SCRIPT = PLUGIN_DIR / "scripts" / "audit-parks.py"

sys.path.insert(0, str(PLUGIN_DIR))
from lib import park_storage as ps  # noqa: E402


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_parks", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NOW = datetime(2026, 4, 19, 12, 0, 0)


def days_ago(n: int) -> str:
    return (NOW - timedelta(days=n)).isoformat(timespec="seconds")


def make_park(**kwargs) -> ps.Park:
    defaults = dict(
        slug="test-park",
        status="parked",
        parked_at=days_ago(1),
        branch="feat/test",
    )
    defaults.update(kwargs)
    return ps.Park(**defaults)


def _no_branch(*args, **kwargs):
    """subprocess.run replacement: branch does not exist locally or remotely."""
    result = subprocess.CompletedProcess(args, 0, stdout="", stderr="")
    return result


def _local_branch_exists(*args, **kwargs):
    """subprocess.run replacement: branch exists locally, not remotely."""
    cmd = args[0]
    stdout = ""
    if "branch" in cmd and "--list" in cmd:
        stdout = "  feat/test\n"
    return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")


# ---------------------------------------------------------------------------
# Unit tests: classify_park()
# ---------------------------------------------------------------------------


class OrphanTests(unittest.TestCase):
    """status=parked, age > 30d → orphan."""

    def test_parked_31d_is_orphan(self):
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(31))
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            self.assertEqual(mod.classify_park(park, now=NOW), "orphan")

    def test_parked_29d_is_healthy(self):
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(29))
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            self.assertEqual(mod.classify_park(park, now=NOW), "healthy")

    def test_parked_30d_exactly_is_not_yet_orphan(self):
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(30))
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            # > 30d, not >= 30d
            self.assertEqual(mod.classify_park(park, now=NOW), "healthy")

    def test_last_kept_at_resets_orphan_clock(self):
        """last_kept_at more recent than parked_at should reset aging."""
        mod = _load_module()
        park = make_park(
            status="parked",
            parked_at=days_ago(40),
            last_kept_at=days_ago(5),
        )
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            self.assertEqual(mod.classify_park(park, now=NOW), "healthy")

    def test_last_kept_at_old_still_orphan(self):
        mod = _load_module()
        park = make_park(
            status="parked",
            parked_at=days_ago(50),
            last_kept_at=days_ago(35),
        )
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            self.assertEqual(mod.classify_park(park, now=NOW), "orphan")


class MaybeDoneTests(unittest.TestCase):
    """status=unparked, unparked_at > 7d → maybe_done."""

    def test_unparked_8d_is_maybe_done(self):
        mod = _load_module()
        park = make_park(
            status="unparked",
            parked_at=days_ago(10),
            unparked_at=days_ago(8),
        )
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            self.assertEqual(mod.classify_park(park, now=NOW), "maybe_done")

    def test_unparked_6d_is_healthy(self):
        mod = _load_module()
        park = make_park(
            status="unparked",
            parked_at=days_ago(10),
            unparked_at=days_ago(6),
        )
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            self.assertEqual(mod.classify_park(park, now=NOW), "healthy")

    def test_unparked_without_unparked_at_is_healthy(self):
        """Gracefully handle missing unparked_at even if status=unparked."""
        mod = _load_module()
        park = make_park(status="unparked", parked_at=days_ago(10))
        with patch.object(mod, "_branch_exists_locally", return_value=True):
            self.assertEqual(mod.classify_park(park, now=NOW), "healthy")


class BranchGoneTests(unittest.TestCase):
    """Branch exists neither locally nor remotely → branch_gone."""

    def test_branch_gone_when_neither_local_nor_remote(self):
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(1))
        with (
            patch.object(mod, "_branch_exists_locally", return_value=False),
            patch.object(mod, "_branch_exists_remotely", return_value=False),
        ):
            self.assertEqual(mod.classify_park(park, now=NOW), "branch_gone")

    def test_healthy_when_branch_exists_locally(self):
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(1))
        with (
            patch.object(mod, "_branch_exists_locally", return_value=True),
            patch.object(mod, "_branch_exists_remotely", return_value=False),
        ):
            self.assertEqual(mod.classify_park(park, now=NOW), "healthy")

    def test_healthy_when_branch_exists_remotely_only(self):
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(1))
        with (
            patch.object(mod, "_branch_exists_locally", return_value=False),
            patch.object(mod, "_branch_exists_remotely", return_value=True),
        ):
            self.assertEqual(mod.classify_park(park, now=NOW), "healthy")

    def test_branch_gone_takes_priority_over_orphan(self):
        """A very old park on a deleted branch → branch_gone, not orphan."""
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(60))
        with (
            patch.object(mod, "_branch_exists_locally", return_value=False),
            patch.object(mod, "_branch_exists_remotely", return_value=False),
        ):
            self.assertEqual(mod.classify_park(park, now=NOW), "branch_gone")

    def test_no_branch_field_skips_branch_check(self):
        """Park with no branch set should not trigger branch_gone."""
        mod = _load_module()
        park = make_park(status="parked", parked_at=days_ago(1), branch="")
        # No mocking needed — branch check is skipped entirely
        self.assertEqual(mod.classify_park(park, now=NOW), "healthy")


# ---------------------------------------------------------------------------
# Integration tests: CLI --list mode
# ---------------------------------------------------------------------------


def _run_list(cwd: Path, parks_root: Path) -> list:
    env = os.environ.copy()
    env["CLAUDE_PARKS_ROOT"] = str(parks_root)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--list"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )
    result.check_returncode()
    return json.loads(result.stdout)


def _run_action(cwd: Path, parks_root: Path, slug: str, action: str) -> str:
    env = os.environ.copy()
    env["CLAUDE_PARKS_ROOT"] = str(parks_root)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--action", slug, action],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )
    result.check_returncode()
    return result.stdout.strip()


def _write_park(
    root: Path,
    key: str,
    slug: str,
    branch: str = "feat/test",
    status: str = "parked",
    parked_at: str | None = None,
) -> None:
    active = ps.ensure_park_dirs(key, root=root)
    park = ps.Park(
        slug=slug,
        status=status,
        parked_at=parked_at or days_ago(1),
        branch=branch,
    )
    park.save(active / f"{slug}.md")


class ListModeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.cwd = self.tmp / "repo"
        self.cwd.mkdir()
        self.parks = self.tmp / "parks"
        self.parks.mkdir()
        self.key = ps._slugify(str(self.cwd.resolve()))

    def tearDown(self):
        self._tmp.cleanup()

    def test_empty_store_returns_empty_list(self):
        result = _run_list(self.cwd, self.parks)
        self.assertEqual(result, [])

    def test_lists_park_with_required_keys(self):
        _write_park(self.parks, self.key, "my-park", branch="main")
        result = _run_list(self.cwd, self.parks)
        self.assertEqual(len(result), 1)
        entry = result[0]
        for key in ("slug", "classification", "status", "branch", "parked_at", "path"):
            self.assertIn(key, entry, f"missing key: {key}")

    def test_slug_matches_written_park(self):
        _write_park(self.parks, self.key, "auth-fix")
        result = _run_list(self.cwd, self.parks)
        self.assertEqual(result[0]["slug"], "auth-fix")


# ---------------------------------------------------------------------------
# Integration tests: CLI --action mode
# ---------------------------------------------------------------------------


class ActionDoneTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.cwd = self.tmp / "repo"
        self.cwd.mkdir()
        self.parks = self.tmp / "parks"
        self.parks.mkdir()
        self.key = ps._slugify(str(self.cwd.resolve()))

    def tearDown(self):
        self._tmp.cleanup()

    def test_done_moves_to_done_subdir(self):
        _write_park(self.parks, self.key, "old-park")
        _run_action(self.cwd, self.parks, "old-park", "d")
        active = ps.park_dir(self.key, root=self.parks) / "old-park.md"
        done = ps.park_dir(self.key, root=self.parks) / "done" / "old-park.md"
        self.assertFalse(active.exists())
        self.assertTrue(done.exists())

    def test_stale_moves_to_stale_subdir(self):
        _write_park(self.parks, self.key, "dead-park")
        _run_action(self.cwd, self.parks, "dead-park", "s")
        active = ps.park_dir(self.key, root=self.parks) / "dead-park.md"
        stale = ps.park_dir(self.key, root=self.parks) / "stale" / "dead-park.md"
        self.assertFalse(active.exists())
        self.assertTrue(stale.exists())

    def test_delete_removes_file(self):
        _write_park(self.parks, self.key, "junk-park")
        _run_action(self.cwd, self.parks, "junk-park", "x")
        active = ps.park_dir(self.key, root=self.parks) / "junk-park.md"
        self.assertFalse(active.exists())

    def test_keep_updates_last_kept_at(self):
        _write_park(self.parks, self.key, "keep-me")
        _run_action(self.cwd, self.parks, "keep-me", "k")
        active = ps.park_dir(self.key, root=self.parks) / "keep-me.md"
        park = ps.Park.load(active)
        self.assertIsNotNone(park.last_kept_at)

    def test_keep_preserves_original_parked_at(self):
        original = days_ago(20)
        _write_park(self.parks, self.key, "keep-me", parked_at=original)
        _run_action(self.cwd, self.parks, "keep-me", "k")
        active = ps.park_dir(self.key, root=self.parks) / "keep-me.md"
        park = ps.Park.load(active)
        self.assertEqual(park.parked_at, original)

    def test_action_on_missing_park_exits_nonzero(self):
        env = os.environ.copy()
        env["CLAUDE_PARKS_ROOT"] = str(self.parks)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--action", "no-such-park", "d"],
            cwd=str(self.cwd),
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertNotEqual(result.returncode, 0)

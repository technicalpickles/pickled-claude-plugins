"""Tests for scripts/park-resolve.py.

These are subprocess-invocation tests: we actually run the script as a child
process, parse its stdout JSON, and assert on the shape. That matches how
the park SKILL.md calls it at runtime, so the coverage exercises the same
integration surface Claude does.

Run from plugins/agent-meta/:
    python3 -m unittest discover tests -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = THIS_DIR.parent
SCRIPT = PLUGIN_DIR / "scripts" / "park-resolve.py"

# Make `lib` importable so the test helpers can call park_storage directly
# to set up fixtures (recording an unpark) before invoking the script.
sys.path.insert(0, str(PLUGIN_DIR))

from lib import park_storage as ps  # noqa: E402


def _run(
    cwd: Path,
    *args: str,
    parks_root: Path | None = None,
) -> dict:
    """Invoke park-resolve.py and parse its stdout JSON.

    Passes ``--parks-root`` when ``parks_root`` is given so tests stay
    isolated from the real ``~/.claude/parks`` directory.
    """
    cmd = [sys.executable, str(SCRIPT), *args]
    if parks_root is not None:
        cmd.extend(["--parks-root", str(parks_root)])
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _init_repo(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=repo, check=True, capture_output=True,
    )


class OutputShapeTests(unittest.TestCase):
    """Every invocation must emit these top-level keys. Downstream (the
    park SKILL) reads each by name; missing keys would silently degrade
    park metadata."""

    REQUIRED_KEYS = {
        "repo_key",
        "branch",
        "worktree",
        "is_worktree",
        "parent",
    }

    def test_shape_inside_repo(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            out = _run(repo)
            self.assertEqual(set(out.keys()), self.REQUIRED_KEYS)

    def test_shape_outside_repo(self):
        with TemporaryDirectory() as tmp:
            out = _run(Path(tmp))
            self.assertEqual(set(out.keys()), self.REQUIRED_KEYS)


class MainCheckoutTests(unittest.TestCase):
    def test_not_a_worktree(self):
        """Plain checkout → is_worktree false, worktree null."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            out = _run(repo)
            self.assertFalse(out["is_worktree"])
            self.assertIsNone(out["worktree"])

    def test_branch_is_populated(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            subprocess.run(
                ["git", "checkout", "-b", "feat/my-branch"],
                cwd=repo, check=True, capture_output=True,
            )
            out = _run(repo)
            self.assertEqual(out["branch"], "feat/my-branch")

    def test_repo_key_matches_park_storage(self):
        """The script's repo_key must agree with park_storage.repo_key()
        called from the same cwd. If these drift, parks land in a different
        directory than everything else looks in."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            out = _run(repo)
            expected = ps._slugify(str(repo.resolve()))
            self.assertEqual(out["repo_key"], expected)


class WorktreeTests(unittest.TestCase):
    """Running inside a ``git worktree``: the worktree path must be
    reported, but repo_key must still match the main checkout (that's the
    core invariant of this whole feature)."""

    def test_is_worktree_true_and_path_matches(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            worktree = Path(tmp) / "r-wt"
            subprocess.run(
                ["git", "worktree", "add", str(worktree), "-b", "wt-branch"],
                cwd=repo, check=True, capture_output=True,
            )
            out = _run(worktree)
            self.assertTrue(out["is_worktree"])
            # worktree path is absolute, resolved — avoid symlink mismatches
            # on macOS (/var vs /private/var). resolve() on both sides.
            self.assertEqual(
                Path(out["worktree"]).resolve(),
                worktree.resolve(),
            )
            self.assertEqual(out["branch"], "wt-branch")

    def test_worktree_shares_repo_key_with_main(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            worktree = Path(tmp) / "r-wt"
            subprocess.run(
                ["git", "worktree", "add", str(worktree), "-b", "wt-branch"],
                cwd=repo, check=True, capture_output=True,
            )
            main = _run(repo)
            wt = _run(worktree)
            self.assertEqual(main["repo_key"], wt["repo_key"])


class ParentResolutionTests(unittest.TestCase):
    """--session-id reads .state/<sid>.json via park_storage.read_last_unpark.
    No arg means no lookup (parent stays null)."""

    def test_parent_null_without_session_id(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            out = _run(repo, parks_root=parks_root)
            self.assertIsNone(out["parent"])

    def test_parent_null_when_no_unpark_recorded(self):
        """Script must not crash when --session-id is given but the state
        file doesn't exist yet — that's the fresh-session case."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            out = _run(
                repo,
                "--session-id", "sess-never-unparked",
                parks_root=parks_root,
            )
            self.assertIsNone(out["parent"])

    def test_parent_populated_after_record_unpark(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            # Seed the breadcrumb the way a real unpark call would.
            key = ps._slugify(str(repo.resolve()))
            ps.record_unpark(
                key, session_id="sess-xyz", slug="feature-jwt", root=parks_root,
            )
            out = _run(
                repo,
                "--session-id", "sess-xyz",
                parks_root=parks_root,
            )
            self.assertEqual(out["parent"], "feature-jwt")


class OutsideRepoTests(unittest.TestCase):
    """No git? repo_key still computable (slug of cwd), branch and worktree
    both null. Must exit 0 so the skill doesn't break when invoked from a
    stray directory."""

    def test_outside_repo_does_not_crash(self):
        with TemporaryDirectory() as tmp:
            # Guard against /tmp landing inside a git repo.
            probe = subprocess.run(
                ["git", "rev-parse", "--git-common-dir"],
                cwd=tmp, capture_output=True, text=True,
            )
            if probe.returncode == 0 and probe.stdout.strip():
                self.skipTest(
                    f"TemporaryDirectory inside git repo: "
                    f"{probe.stdout.strip()}"
                )
            out = _run(Path(tmp))
            self.assertIsNone(out["branch"])
            self.assertIsNone(out["worktree"])
            self.assertFalse(out["is_worktree"])
            # repo_key is still a slug — the cwd slug.
            self.assertEqual(
                out["repo_key"],
                ps._slugify(str(Path(tmp).resolve())),
            )


if __name__ == "__main__":
    unittest.main()

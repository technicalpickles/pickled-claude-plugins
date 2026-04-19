"""Tests for park_storage. Stdlib unittest, no external deps.

Run from plugins/agent-meta/:
    python3 -m unittest discover tests -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

# Make `lib` importable when running `python3 -m unittest discover tests`
# from plugins/agent-meta/.
THIS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = THIS_DIR.parent
sys.path.insert(0, str(PLUGIN_DIR))

from lib import park_storage as ps  # noqa: E402


class SlugifyTests(unittest.TestCase):
    """Pin down the slug convention to match ~/.claude/projects/ dir names.

    Observed examples on disk:
      /Users/technicalpickles/github.com/technicalpickles/pickled-claude-plugins
        -> -Users-technicalpickles-github-com-technicalpickles-pickled-claude-plugins

    Rules we're matching:
      - Leading dash is KEPT (from leading `/`).
      - `/` becomes `-`.
      - `.` becomes `-`.
      - Other non-alphanumerics become `-`.
      - Alphanumerics pass through unchanged, case preserved.
    """

    def test_absolute_path_keeps_leading_dash(self):
        self.assertEqual(
            ps._slugify("/Users/technicalpickles/github.com/technicalpickles/pickled-claude-plugins"),
            "-Users-technicalpickles-github-com-technicalpickles-pickled-claude-plugins",
        )

    def test_dots_become_dashes(self):
        self.assertEqual(ps._slugify("/a/b.c/d"), "-a-b-c-d")

    def test_underscores_become_dashes(self):
        # non-alphanumeric → dash, so `_` becomes `-`
        self.assertEqual(ps._slugify("/a/b_c"), "-a-b-c")

    def test_alphanumerics_passthrough(self):
        self.assertEqual(ps._slugify("/abc123"), "-abc123")

    def test_trailing_slash_not_kept_as_dash_tail(self):
        # Path.resolve() strips trailing slashes already; but verify slugify
        # doesn't leave a stray trailing dash if it sneaks in.
        # Current observed Claude Code behavior keeps leading but strips trailing:
        # e.g. `/tmp/foo/` would yield `-tmp-foo` not `-tmp-foo-`.
        self.assertEqual(ps._slugify("/tmp/foo/"), "-tmp-foo")


class RepoKeyTests(unittest.TestCase):
    def test_inside_git_repo_uses_main_repo_root(self):
        """From the main checkout, ``--git-common-dir`` is ``.git`` (relative).
        Resolving against cwd and taking the parent must yield the repo root.
        """
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myrepo"
            repo.mkdir()
            subprocess.run(
                ["git", "init"], cwd=repo, check=True, capture_output=True
            )
            # Expected is the resolved repo root — same answer the old
            # ``--show-toplevel`` implementation would have produced for a
            # plain checkout. The worktree case (covered below) is where
            # the two implementations diverge.
            expected = ps._slugify(str(repo.resolve()))
            with patch("os.getcwd", return_value=str(repo)):
                self.assertEqual(ps.repo_key(), expected)

    def test_worktree_shares_key_with_main_repo(self):
        """The whole point of switching to ``--git-common-dir``: every
        worktree of a repo must produce the *same* repo_key() as the main
        checkout. With ``--show-toplevel`` this test would fail because
        each worktree has its own toplevel path.
        """
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myrepo"
            repo.mkdir()
            # Need at least one commit before `git worktree add` will work.
            subprocess.run(
                ["git", "init"], cwd=repo, check=True, capture_output=True
            )
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
            # Place the worktree OUTSIDE the main repo so its path doesn't
            # accidentally slugify to the same thing as the repo root.
            worktree = Path(tmp) / "myrepo-wt"
            subprocess.run(
                ["git", "worktree", "add", str(worktree), "-b", "wt-branch"],
                cwd=repo, check=True, capture_output=True,
            )

            with patch("os.getcwd", return_value=str(repo)):
                key_from_main = ps.repo_key()
            with patch("os.getcwd", return_value=str(worktree)):
                key_from_worktree = ps.repo_key()

            # The invariant: same repo → same key, regardless of worktree.
            self.assertEqual(key_from_main, key_from_worktree)
            # And both should correspond to the main repo root, not the
            # worktree path.
            self.assertEqual(key_from_main, ps._slugify(str(repo.resolve())))
            self.assertNotEqual(
                key_from_worktree, ps._slugify(str(worktree.resolve()))
            )

    def test_outside_git_repo_uses_cwd(self):
        with TemporaryDirectory() as tmp:
            # Make sure this dir is NOT a git repo (TemporaryDirectory never is,
            # unless something upstream makes it one).
            expected = ps._slugify(str(Path(tmp).resolve()))
            with patch("os.getcwd", return_value=tmp):
                # Run git from inside tmp; it should fail because no .git.
                # But we also need to guard against an ancestor being a repo.
                # /tmp typically has no parent git repo on macOS/Linux.
                result = subprocess.run(
                    ["git", "rev-parse", "--git-common-dir"],
                    cwd=tmp, capture_output=True, text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    self.skipTest(
                        f"TemporaryDirectory landed inside a git repo: "
                        f"{result.stdout.strip()}"
                    )
                self.assertEqual(ps.repo_key(), expected)


class ParkDirTests(unittest.TestCase):
    def test_park_dir_uses_default_root(self):
        key = "-some-key"
        expected = Path.home() / ".claude" / "parks" / key
        self.assertEqual(ps.park_dir(key), expected)

    def test_park_dir_respects_custom_root(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(ps.park_dir("abc", root=root), root / "abc")


class EnsureParkDirsTests(unittest.TestCase):
    def test_creates_all_subdirs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = "-repo-abc"
            returned = ps.ensure_park_dirs(key, root=root)
            active = root / key
            self.assertEqual(returned, active)
            self.assertTrue(active.is_dir())
            self.assertTrue((active / "done").is_dir())
            self.assertTrue((active / "stale").is_dir())
            self.assertTrue((active / ".state").is_dir())

    def test_idempotent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = "-repo-abc"
            ps.ensure_park_dirs(key, root=root)
            # Second call must not raise.
            ps.ensure_park_dirs(key, root=root)
            self.assertTrue((root / key / "done").is_dir())


class ListActiveTests(unittest.TestCase):
    def test_returns_top_level_md_files_only(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = "-r"
            ps.ensure_park_dirs(key, root=root)
            active = root / key

            # Two active parks
            (active / "2026-04-19-a.md").write_text(
                _minimal_park_text(slug="a", branch="feat/a")
            )
            (active / "2026-04-19-b.md").write_text(
                _minimal_park_text(slug="b", branch="feat/b")
            )
            # Noise that should be ignored
            (active / "done" / "2026-04-01-old.md").write_text(
                _minimal_park_text(slug="old", branch="feat/old")
            )
            (active / "stale" / "2026-04-01-dead.md").write_text(
                _minimal_park_text(slug="dead", branch="feat/dead")
            )
            (active / ".state" / "sess-1.json").write_text("{}")
            (active / "README.txt").write_text("not a park")

            parks = ps.list_active(key, root=root)
            slugs = sorted(p.slug for p in parks)
            self.assertEqual(slugs, ["a", "b"])

    def test_returns_empty_list_when_dir_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            # key never had ensure_park_dirs run
            self.assertEqual(ps.list_active("-missing", root=root), [])


class ParkLoadSaveTests(unittest.TestCase):
    def test_load_minimal_fields(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.md"
            path.write_text(textwrap.dedent("""\
                ---
                name: park-thing
                type: park
                status: parked
                slug: thing
                parked_at: 2026-04-19T10:23:00
                branch: feat/thing
                ---
                body text here
                """))
            p = ps.Park.load(path)
            self.assertEqual(p.slug, "thing")
            self.assertEqual(p.status, "parked")
            self.assertEqual(p.branch, "feat/thing")
            self.assertEqual(p.parked_at, "2026-04-19T10:23:00")
            self.assertEqual(p.name, "park-thing")
            self.assertEqual(p.type, "park")
            self.assertEqual(p.body, "body text here\n")
            # Optionals default to None
            self.assertIsNone(p.worktree)
            self.assertIsNone(p.unparked_at)
            self.assertIsNone(p.parent)
            self.assertIsNone(p.plan)
            self.assertIsNone(p.task)
            self.assertIsNone(p.origin_session_id)

    def test_load_null_values_become_none(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.md"
            path.write_text(textwrap.dedent("""\
                ---
                name: park-x
                type: park
                status: parked
                slug: x
                parked_at: 2026-04-19T10:23:00
                branch: feat/x
                worktree: null
                unparked_at: null
                parent: null
                ---
                """))
            p = ps.Park.load(path)
            self.assertIsNone(p.worktree)
            self.assertIsNone(p.unparked_at)
            self.assertIsNone(p.parent)

    def test_load_quoted_strings_unwrapped(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.md"
            path.write_text(textwrap.dedent("""\
                ---
                name: "park-q"
                type: park
                status: parked
                slug: 'q'
                parked_at: "2026-04-19T10:23:00"
                branch: "feat/with: colon"
                ---
                """))
            p = ps.Park.load(path)
            self.assertEqual(p.slug, "q")
            self.assertEqual(p.name, "park-q")
            self.assertEqual(p.branch, "feat/with: colon")

    def test_save_roundtrip_all_fields(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.md"
            original = ps.Park(
                slug="full",
                status="unparked",
                parked_at="2026-04-19T10:23:00",
                branch="feat/full",
                worktree="/abs/path/worktree",
                unparked_at="2026-04-19T12:00:00",
                parent="park-prev",
                plan="docs/plans/p.md",
                task="8a7b6c5d-uuid",
                origin_session_id="sess-xyz",
                name="park-full",
                type="park",
                body="Line 1\nLine 2\n",
            )
            original.save(path)
            loaded = ps.Park.load(path)
            self.assertEqual(loaded, original)

    def test_save_field_order_matches_dataclass(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.md"
            p = ps.Park(
                slug="o",
                status="parked",
                parked_at="2026-04-19T10:23:00",
                branch="feat/o",
                name="park-o",
                body="b\n",
            )
            p.save(path)
            content = path.read_text()
            # Grab just the frontmatter block
            self.assertTrue(content.startswith("---\n"))
            end = content.index("\n---\n", 4)
            fm = content[4:end]
            keys = [line.split(":", 1)[0] for line in fm.splitlines()]
            # Expected order = order from the Park dataclass, omitting `body`
            # and any field whose value we don't write (None optionals are
            # written as `null` so they DO appear, but name is set here).
            expected_prefix = [
                "slug",
                "status",
                "parked_at",
                "branch",
                "worktree",
                "unparked_at",
                "parent",
                "plan",
                "task",
                "origin_session_id",
                "name",
                "type",
            ]
            self.assertEqual(keys, expected_prefix)

    def test_save_writes_exact_bytes(self):
        """Lock down the on-disk format so downstream tools (grep, diff,
        migration scripts) can rely on it."""
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.md"
            p = ps.Park(
                slug="exact",
                status="parked",
                parked_at="2026-04-19T10:23:00",
                branch="feat/exact",
                name="park-exact",
                body="hello\n",
            )
            p.save(path)
            expected = (
                "---\n"
                "slug: exact\n"
                "status: parked\n"
                "parked_at: 2026-04-19T10:23:00\n"
                "branch: feat/exact\n"
                "worktree: null\n"
                "unparked_at: null\n"
                "parent: null\n"
                "plan: null\n"
                "task: null\n"
                "origin_session_id: null\n"
                "name: park-exact\n"
                "type: park\n"
                "---\n"
                "hello\n"
            )
            self.assertEqual(path.read_text(), expected)


class ParentChainStateTests(unittest.TestCase):
    """Per-session breadcrumb: unpark records the slug it resumed, park reads
    it back on the next park to auto-fill ``parent:``. State, not log —
    re-recording for the same session overwrites.
    """

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_write_last_unpark_then_read(self):
        key = "test-repo"
        ps.ensure_park_dirs(key, root=self.root)
        ps.record_unpark(key, session_id="sess-1", slug="jwt-auth", root=self.root)
        self.assertEqual(
            ps.read_last_unpark(key, "sess-1", root=self.root),
            "jwt-auth",
        )

    def test_read_last_unpark_returns_none_if_missing(self):
        key = "test-repo"
        ps.ensure_park_dirs(key, root=self.root)
        self.assertIsNone(
            ps.read_last_unpark(key, "no-such-session", root=self.root)
        )

    def test_most_recent_unpark_wins(self):
        """State cell, not log: a second record overwrites the first."""
        key = "test-repo"
        ps.ensure_park_dirs(key, root=self.root)
        ps.record_unpark(key, session_id="sess-1", slug="first-slug", root=self.root)
        ps.record_unpark(key, session_id="sess-1", slug="second-slug", root=self.root)
        self.assertEqual(
            ps.read_last_unpark(key, "sess-1", root=self.root),
            "second-slug",
        )

    def test_different_sessions_do_not_collide(self):
        key = "test-repo"
        ps.ensure_park_dirs(key, root=self.root)
        ps.record_unpark(key, session_id="sess-A", slug="slug-A", root=self.root)
        ps.record_unpark(key, session_id="sess-B", slug="slug-B", root=self.root)
        self.assertEqual(
            ps.read_last_unpark(key, "sess-A", root=self.root), "slug-A"
        )
        self.assertEqual(
            ps.read_last_unpark(key, "sess-B", root=self.root), "slug-B"
        )

    def test_state_file_lives_at_expected_path(self):
        """Pin the on-disk location so other tools (and future migrations)
        can find state files without asking park_storage."""
        key = "test-repo"
        ps.ensure_park_dirs(key, root=self.root)
        ps.record_unpark(key, session_id="sess-path", slug="s", root=self.root)
        expected = self.root / key / ".state" / "sess-path.json"
        self.assertTrue(expected.is_file(), f"expected state file at {expected}")

    def test_state_file_json_shape(self):
        """Format: {"last_unpark": "<slug>", "at": "<iso-ts>"}"""
        key = "test-repo"
        ps.ensure_park_dirs(key, root=self.root)
        ps.record_unpark(key, session_id="sess-shape", slug="the-slug", root=self.root)
        state_path = self.root / key / ".state" / "sess-shape.json"
        payload = json.loads(state_path.read_text())
        self.assertEqual(set(payload.keys()), {"last_unpark", "at"})
        self.assertEqual(payload["last_unpark"], "the-slug")
        # ISO 8601 with seconds precision, no microseconds, no timezone suffix
        # required (datetime.now().isoformat(timespec="seconds") emits naive).
        self.assertRegex(
            payload["at"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        )

    def test_record_unpark_creates_state_dir_if_missing(self):
        """Robustness: don't require the caller to have run ensure_park_dirs
        first. Park/unpark commands shouldn't fail on a fresh repo just
        because the breadcrumb directory isn't materialized yet.
        """
        key = "fresh-repo"
        # Deliberately skip ensure_park_dirs — start from bare root.
        ps.record_unpark(key, session_id="sess-new", slug="bootstrap", root=self.root)
        self.assertEqual(
            ps.read_last_unpark(key, "sess-new", root=self.root), "bootstrap"
        )

    def test_read_last_unpark_no_side_effects_when_missing(self):
        """read_* is pure: missing file returns None, doesn't create anything."""
        key = "quiet-repo"
        self.assertIsNone(
            ps.read_last_unpark(key, "never-recorded", root=self.root)
        )
        # Nothing should have been created on disk.
        self.assertFalse((self.root / key).exists())

    def test_read_last_unpark_raises_on_corrupt_json(self):
        """Malformed state is a real bug — surface it, don't pretend it's
        absent. Silent recovery here would hide a disk-level problem.
        """
        key = "test-repo"
        ps.ensure_park_dirs(key, root=self.root)
        state_path = self.root / key / ".state" / "sess-bad.json"
        state_path.write_text("this is not json {{{")
        with self.assertRaises(json.JSONDecodeError):
            ps.read_last_unpark(key, "sess-bad", root=self.root)


def _minimal_park_text(*, slug: str, branch: str) -> str:
    return textwrap.dedent(f"""\
        ---
        name: park-{slug}
        type: park
        status: parked
        slug: {slug}
        parked_at: 2026-04-19T10:23:00
        branch: {branch}
        ---
        body
        """)


if __name__ == "__main__":
    unittest.main()

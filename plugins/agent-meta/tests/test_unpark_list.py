"""Tests for scripts/unpark-list.py.

Subprocess-invocation tests, mirroring test_park_resolve.py: the script is
run as a child process so we exercise the same integration surface the
unpark SKILL.md uses at runtime.

Run from plugins/agent-meta/:
    python3 -m unittest discover tests -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

THIS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = THIS_DIR.parent
SCRIPT = PLUGIN_DIR / "scripts" / "unpark-list.py"

# Make `lib` importable so we can populate fixtures via park_storage.
sys.path.insert(0, str(PLUGIN_DIR))

from lib import park_storage as ps  # noqa: E402


def _run(cwd: Path, *args: str, parks_root: Path | None = None) -> list:
    """Invoke unpark-list.py and parse its stdout JSON."""
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


def _write_park(
    active_dir: Path,
    *,
    slug: str,
    parked_at: str,
    branch: str = "feat/x",
    status: str = "parked",
    unparked_at: str | None = None,
    body: str = "",
) -> Path:
    """Write a park file using Park.save() so on-disk shape stays canonical."""
    path = active_dir / f"{parked_at[:10]}-{slug}.md"
    ps.Park(
        slug=slug,
        status=status,
        parked_at=parked_at,
        branch=branch,
        unparked_at=unparked_at,
        name=f"park-{slug}",
        body=body,
    ).save(path)
    return path


class EmptyDirTests(unittest.TestCase):
    def test_empty_park_dir_returns_empty_list(self):
        """Fresh repo, no parks yet: script prints `[]`, exits 0."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            out = _run(repo, parks_root=parks_root)
            self.assertEqual(out, [])

    def test_nonexistent_park_dir_returns_empty_list(self):
        """Repo key has never been seen: no directory at all, still `[]`."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            # Point at a parks_root that exists but has no entry for this key.
            parks_root = Path(tmp) / "empty-parks"
            parks_root.mkdir()
            out = _run(repo, parks_root=parks_root)
            self.assertEqual(out, [])


class OrderingTests(unittest.TestCase):
    def test_sorted_by_parked_at_descending(self):
        """Most recent park first, oldest last."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)

            _write_park(active, slug="oldest",
                        parked_at="2026-04-10T09:00:00", branch="feat/a")
            _write_park(active, slug="middle",
                        parked_at="2026-04-15T09:00:00", branch="feat/b")
            _write_park(active, slug="newest",
                        parked_at="2026-04-18T09:00:00", branch="feat/c")

            out = _run(repo, parks_root=parks_root)
            slugs = [p["slug"] for p in out]
            self.assertEqual(slugs, ["newest", "middle", "oldest"])


class SubdirExclusionTests(unittest.TestCase):
    def test_done_and_stale_are_excluded(self):
        """Only top-level active parks appear. done/, stale/, .state/ are
        skipped (list_active contract)."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)

            _write_park(active, slug="active-one",
                        parked_at="2026-04-18T09:00:00")
            _write_park(active / "done", slug="finished",
                        parked_at="2026-04-01T09:00:00")
            _write_park(active / "stale", slug="abandoned",
                        parked_at="2026-03-15T09:00:00")
            # Bonus: arbitrary .state file shouldn't affect output.
            (active / ".state" / "sess-1.json").write_text("{}")

            out = _run(repo, parks_root=parks_root)
            slugs = [p["slug"] for p in out]
            self.assertEqual(slugs, ["active-one"])


class EntryShapeTests(unittest.TestCase):
    REQUIRED_KEYS = {
        "slug",
        "parked_at",
        "unparked_at",
        "status",
        "branch",
        "summary",
        "path",
    }

    def test_entry_has_all_required_keys(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)
            _write_park(active, slug="a",
                        parked_at="2026-04-18T09:00:00",
                        branch="feat/a",
                        body="one-line summary\n")

            out = _run(repo, parks_root=parks_root)
            self.assertEqual(len(out), 1)
            self.assertEqual(set(out[0].keys()), self.REQUIRED_KEYS)

    def test_path_is_absolute_and_points_to_park_file(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)
            written = _write_park(active, slug="a",
                                  parked_at="2026-04-18T09:00:00")

            out = _run(repo, parks_root=parks_root)
            entry = out[0]
            self.assertTrue(Path(entry["path"]).is_absolute())
            self.assertEqual(Path(entry["path"]).resolve(), written.resolve())


class SummaryHeuristicTests(unittest.TestCase):
    """Summary is derived from the body: first non-empty, non-heading line
    trimmed to ~100 chars. Empty body → empty string. Documented in
    unpark-list.py and the unpark SKILL."""

    def test_empty_body_yields_empty_summary(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)
            _write_park(active, slug="a",
                        parked_at="2026-04-18T09:00:00",
                        body="")

            out = _run(repo, parks_root=parks_root)
            self.assertEqual(out[0]["summary"], "")

    def test_multiline_body_uses_first_non_heading_line(self):
        body = textwrap.dedent("""\
            ## Current State

            Halfway through the JWT refactor, stuck on token refresh.

            ## Next Steps
            1. Fix refresh flow.
            """)
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)
            _write_park(active, slug="a",
                        parked_at="2026-04-18T09:00:00",
                        body=body)

            out = _run(repo, parks_root=parks_root)
            self.assertEqual(
                out[0]["summary"],
                "Halfway through the JWT refactor, stuck on token refresh.",
            )

    def test_long_line_is_truncated(self):
        body = "x" * 300 + "\n"
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)
            _write_park(active, slug="a",
                        parked_at="2026-04-18T09:00:00",
                        body=body)

            out = _run(repo, parks_root=parks_root)
            self.assertLessEqual(len(out[0]["summary"]), 100)

    def test_heading_only_body_yields_empty_summary(self):
        """If every non-empty line starts with `#`, there's no meaningful
        text to surface. Fall back to empty string."""
        body = "## Current State\n## Next Steps\n"
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)
            _write_park(active, slug="a",
                        parked_at="2026-04-18T09:00:00",
                        body=body)

            out = _run(repo, parks_root=parks_root)
            self.assertEqual(out[0]["summary"], "")


class OutsideRepoTests(unittest.TestCase):
    def test_outside_git_repo_returns_empty_list(self):
        """Stray cwd: no parks, no crash. Exit 0, stdout `[]`."""
        with TemporaryDirectory() as tmp:
            # Sanity: don't accidentally run inside a parent repo.
            probe = subprocess.run(
                ["git", "rev-parse", "--git-common-dir"],
                cwd=tmp, capture_output=True, text=True,
            )
            if probe.returncode == 0 and probe.stdout.strip():
                self.skipTest(
                    f"TemporaryDirectory inside git repo: "
                    f"{probe.stdout.strip()}"
                )
            parks_root = Path(tmp) / "parks"
            out = _run(Path(tmp), parks_root=parks_root)
            self.assertEqual(out, [])


class StatusFieldTests(unittest.TestCase):
    """Active dir can contain both `parked` and `unparked` (unpark only flips
    status; the file stays until the audit skill moves it). list_active is
    status-agnostic, so our listing must surface both."""

    def test_lists_parked_and_unparked_alike(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _init_repo(repo)
            parks_root = Path(tmp) / "parks"
            key = ps._slugify(str(repo.resolve()))
            active = ps.ensure_park_dirs(key, root=parks_root)

            _write_park(active, slug="parked-one",
                        parked_at="2026-04-18T09:00:00",
                        status="parked")
            _write_park(active, slug="unparked-one",
                        parked_at="2026-04-17T09:00:00",
                        status="unparked",
                        unparked_at="2026-04-17T10:00:00")

            out = _run(repo, parks_root=parks_root)
            by_slug = {p["slug"]: p for p in out}
            self.assertEqual(by_slug["parked-one"]["status"], "parked")
            self.assertEqual(by_slug["unparked-one"]["status"], "unparked")
            self.assertEqual(
                by_slug["unparked-one"]["unparked_at"],
                "2026-04-17T10:00:00",
            )


if __name__ == "__main__":
    unittest.main()

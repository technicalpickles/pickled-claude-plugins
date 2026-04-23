#!/usr/bin/env python3
"""park-resolve: emit git + parent-chain context for the park skill.

The ``park`` SKILL.md invokes this script so a single Bash call yields all
the metadata it needs to build a park file:

  - ``repo_key``: same slug ``park_storage.repo_key()`` would produce for
    the current working directory. Every worktree of a given repo MUST
    produce the same key — that invariant is why parks survive across
    worktrees.
  - ``branch``: ``git rev-parse --abbrev-ref HEAD``, or ``null`` outside
    a repo.
  - ``worktree`` / ``is_worktree``: if the current checkout is a linked
    worktree (i.e. ``--show-toplevel`` differs from the main repo root
    derived from ``--git-common-dir``), ``worktree`` is the absolute
    worktree path and ``is_worktree`` is ``true``. Otherwise ``worktree``
    is ``null`` and ``is_worktree`` is ``false``.
  - ``parent``: when ``--session-id`` is passed, the slug this session
    most recently unparked in this repo (from ``.state/<sid>.json``).
    ``null`` if no session-id, no state file, or the file is missing.

Exits 0 even outside a git repo: the skill still wants a repo_key for
filing parks (the cwd-slug fallback). Crashing here would break park on
stray directories.

CLI:
    park-resolve.py [--session-id SID] [--parks-root PATH]

``--parks-root`` exists for test isolation. Production invocations pass
no root, and ``park_storage.PARKS_ROOT`` (``~/.claude/parks``) is used.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Import park_storage from ../lib/, same pattern the hooks use.
THIS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = THIS_DIR.parent
sys.path.insert(0, str(PLUGIN_DIR / "lib"))

import park_storage  # noqa: E402


def _git(*args: str, cwd: Optional[str] = None) -> Optional[str]:
    """Run a git command, return stripped stdout or None on any failure.

    We deliberately swallow errors: this script must not crash when run
    outside a repo, when git isn't installed, or when the working copy
    is in some half-initialized state.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def _resolve_worktree(cwd: str) -> tuple[Optional[str], bool]:
    """Return (worktree_path_or_None, is_worktree) for ``cwd``.

    The detection mirrors ``park_storage.repo_key``'s logic: the main repo
    root is ``git rev-parse --git-common-dir``'s parent (resolved to
    absolute). The current toplevel is ``git rev-parse --show-toplevel``.
    If they differ, this is a linked worktree and its path is the toplevel.

    If either call fails (not a repo), returns ``(None, False)``.
    """
    common_dir = _git("rev-parse", "--git-common-dir", cwd=cwd)
    toplevel = _git("rev-parse", "--show-toplevel", cwd=cwd)
    if not common_dir or not toplevel:
        return None, False

    common_path = Path(common_dir)
    if not common_path.is_absolute():
        common_path = Path(cwd) / common_path
    main_root = common_path.resolve().parent
    toplevel_resolved = Path(toplevel).resolve()

    if main_root != toplevel_resolved:
        return str(toplevel_resolved), True
    return None, False


def resolve(session_id: Optional[str], parks_root: Optional[Path]) -> dict:
    """Gather all context the park skill needs.

    Kept as a plain function so future callers (tests, other scripts)
    can use it without going through ``sys.argv``.
    """
    cwd = os.getcwd()
    repo_key = park_storage.repo_key()
    branch = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    worktree, is_worktree = _resolve_worktree(cwd)

    parent: Optional[str] = None
    if session_id:
        # read_last_unpark silently returns None for missing files — the
        # "fresh session, nothing unparked yet" case. Corrupt JSON WILL
        # surface as an uncaught exception: that's a real disk bug worth
        # crashing on, matching park_storage's contract.
        root = parks_root if parks_root is not None else park_storage.PARKS_ROOT
        parent = park_storage.read_last_unpark(repo_key, session_id, root=root)

    return {
        "repo_key": repo_key,
        "branch": branch,
        "worktree": worktree,
        "is_worktree": is_worktree,
        "parent": parent,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit git + parent-chain context for the park skill.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session ID for parent-chain lookup. Omit to skip the lookup.",
    )
    parser.add_argument(
        "--parks-root",
        default=None,
        help="Override ~/.claude/parks root (for tests).",
    )
    args = parser.parse_args(argv)

    parks_root = Path(args.parks_root) if args.parks_root else None
    payload = resolve(args.session_id, parks_root)
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

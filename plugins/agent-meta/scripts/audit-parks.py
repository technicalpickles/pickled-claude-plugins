#!/usr/bin/env python3
"""Classify and take lifecycle actions on active parks.

Modes:
  --list              Print JSON array of classified parks for current repo.
  --action SLUG ACTION  Apply action (d=done, s=stale, k=keep, x=delete).
  --parks-root PATH   Override parks root (default: ~/.claude/parks/).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import park_storage as ps

ORPHAN_DAYS = 30
MAYBE_DONE_DAYS = 7


def _branch_exists_locally(branch: str, cwd: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "branch", "--list", branch],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _branch_exists_remotely(branch: str, cwd: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def classify_park(park: ps.Park, now: datetime, cwd: str | None = None) -> str:
    """Classify a park for the audit workflow.

    Priority: branch_gone > orphan > maybe_done > healthy.
    """
    cwd = cwd or os.getcwd()

    if park.branch:
        local = _branch_exists_locally(park.branch, cwd)
        if not local:
            remote = _branch_exists_remotely(park.branch, cwd)
            if not remote:
                return "branch_gone"

    if park.status == "parked":
        anchor = park.last_kept_at or park.parked_at
        try:
            anchor_dt = datetime.fromisoformat(anchor)
            if (now - anchor_dt).days > ORPHAN_DAYS:
                return "orphan"
        except (ValueError, TypeError):
            pass

    if park.status == "unparked" and park.unparked_at:
        try:
            unparked_dt = datetime.fromisoformat(park.unparked_at)
            if (now - unparked_dt).days > MAYBE_DONE_DAYS:
                return "maybe_done"
        except (ValueError, TypeError):
            pass

    return "healthy"


def cmd_list(parks_root: Path, cwd: str) -> None:
    key = ps.repo_key()
    parks = ps.list_active(key, root=parks_root)
    now = datetime.now()
    results = []
    for park in parks:
        classification = classify_park(park, now=now, cwd=cwd)
        results.append({
            "slug": park.slug,
            "classification": classification,
            "status": park.status,
            "branch": park.branch,
            "parked_at": park.parked_at,
            "unparked_at": park.unparked_at,
            "path": str(ps.park_dir(key, root=parks_root) / f"{park.slug}.md"),
        })
    print(json.dumps(results, indent=2))


def cmd_action(slug: str, action: str, parks_root: Path) -> None:
    key = ps.repo_key()
    active_dir = ps.park_dir(key, root=parks_root)
    src = active_dir / f"{slug}.md"

    if not src.exists():
        print(f"Park not found: {slug}", file=sys.stderr)
        sys.exit(1)

    if action == "d":
        dst = active_dir / "done" / f"{slug}.md"
        src.rename(dst)
        print(f"Moved {slug} to done/")
    elif action == "s":
        dst = active_dir / "stale" / f"{slug}.md"
        src.rename(dst)
        print(f"Moved {slug} to stale/")
    elif action == "k":
        park = ps.Park.load(src)
        park.last_kept_at = datetime.now().isoformat(timespec="seconds")
        park.save(src)
        print(f"Kept {slug} (last_kept_at updated)")
    elif action == "x":
        src.unlink()
        print(f"Deleted {slug}")
    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parks-root", type=Path, default=ps.PARKS_ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--action", nargs=2, metavar=("SLUG", "ACTION"))
    args = parser.parse_args()

    if args.list:
        cmd_list(args.parks_root, os.getcwd())
    else:
        slug, action = args.action
        if action not in ("d", "s", "k", "x"):
            print(f"Unknown action '{action}'. Use d/s/k/x.", file=sys.stderr)
            sys.exit(1)
        cmd_action(slug, action, args.parks_root)


if __name__ == "__main__":
    main()

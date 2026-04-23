#!/usr/bin/env python3
"""unpark-list: list active parks for the current repo as JSON.

The ``unpark`` SKILL.md invokes this script to fetch candidate parks in a
single Bash call. Output is a JSON array, sorted by ``parked_at``
descending (most recent first). Each entry:

    {
      "slug": "jwt-auth",
      "parked_at": "2026-04-17T10:23:00",
      "unparked_at": null,
      "status": "parked",
      "branch": "feat/auth",
      "summary": "Short one-liner derived from body",
      "path": "/abs/path/to/park.md"
    }

Exits 0 even outside a git repo: the skill should handle "nothing to
unpark" without crashing. Outside a repo, the ``repo_key`` is the slug
of cwd — if a park happens to live there we'll list it; otherwise
``[]``.

CLI:
    unpark-list.py [--parks-root PATH]

``--parks-root`` exists for test isolation. Production callers omit it
and ``park_storage.PARKS_ROOT`` (``~/.claude/parks``) is used.

## Summary heuristic

Parks don't have a formal ``summary`` frontmatter field. We derive one
from the body using this rule:

    First non-empty line that is NOT a Markdown heading (i.e. doesn't
    start with ``#``), with leading/trailing whitespace stripped and
    truncated to 100 chars.

If no such line exists (empty body, or body is only headings), the
summary is an empty string.

Rationale: park bodies written by the park skill start with a ``##``
heading (e.g. ``## Current State``). Using "first non-empty line" would
show ``## Current State`` for every park — useless. Skipping heading
lines surfaces the first paragraph of actual content, which is what a
human skimming a list wants. If a user writes a park with no paragraph
text (just headings and bullet points), we fall back to empty — that's
rare enough to not warrant a cleverer heuristic.

**Design note (possible followup):** if richer summaries become valuable
(e.g. rendering the first bullet from ``## Current State``), the right
move is probably to add an explicit ``summary`` / ``description`` field
to the ``Park`` dataclass rather than bolting on more heuristics here.
Flagged but not acted on — that's a plan amendment, not a unilateral
change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Import park_storage from ../lib/ — same pattern park-resolve.py uses.
THIS_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = THIS_DIR.parent
sys.path.insert(0, str(PLUGIN_DIR / "lib"))

import park_storage  # noqa: E402

_SUMMARY_MAX_LEN = 100


def _derive_summary(body: str) -> str:
    """Pick the first non-empty, non-heading line of ``body``, trimmed.

    See module docstring for full rationale. Kept tolerant: any line
    that starts with ``#`` after stripping is treated as a heading.
    """
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if len(line) > _SUMMARY_MAX_LEN:
            return line[:_SUMMARY_MAX_LEN]
        return line
    return ""


def list_parks(parks_root: Optional[Path]) -> list[dict]:
    """Return the JSON-serializable park list for the current repo.

    Kept separate from ``main`` so tests and other Python callers can
    use it directly.
    """
    key = park_storage.repo_key()
    root = parks_root if parks_root is not None else park_storage.PARKS_ROOT
    parks = park_storage.list_active(key, root=root)

    active_dir = park_storage.park_dir(key, root=root)
    entries: list[dict] = []
    for park in parks:
        filename = f"{park.parked_at[:10]}-{park.slug}.md"
        entries.append({
            "slug": park.slug,
            "parked_at": park.parked_at,
            "unparked_at": park.unparked_at,
            "status": park.status,
            "branch": park.branch,
            "summary": _derive_summary(park.body),
            "path": str((active_dir / filename).resolve()),
        })

    # Most-recent-first. parked_at is ISO-formatted, so string sort ==
    # chronological sort. Ties are rare (second precision) — if they
    # happen, slug provides a stable tiebreaker.
    entries.sort(key=lambda e: (e["parked_at"], e["slug"]), reverse=True)
    return entries


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="List active parks for the current repo as JSON.",
    )
    parser.add_argument(
        "--parks-root",
        default=None,
        help="Override ~/.claude/parks root (for tests).",
    )
    args = parser.parse_args(argv)

    parks_root = Path(args.parks_root) if args.parks_root else None
    payload = list_parks(parks_root)
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

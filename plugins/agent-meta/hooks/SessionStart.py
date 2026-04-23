#!/usr/bin/env python3
"""SessionStart hook: surface active parks for the current repo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import park_storage as ps

THRESHOLD = 8


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if not isinstance(payload, dict):
        sys.exit(0)

    key = ps.repo_key()
    parks = ps.list_active(key)
    if not parks:
        sys.exit(0)

    if len(parks) > THRESHOLD:
        msg = f"{len(parks)} active parks in this repo. Run /audit to review."
    else:
        lines = [f"Active parks ({len(parks)}):"]
        for p in parks:
            age = ps.age_days(p.parked_at)
            lines.append(
                f"  {p.slug:<30} branch: {p.branch:<25} {p.status} {age}d ago"
            )
        msg = "\n".join(lines)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }))


if __name__ == "__main__":
    main()

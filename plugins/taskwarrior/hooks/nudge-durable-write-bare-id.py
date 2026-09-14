#!/usr/bin/env python3
"""
PreToolUse:Write|Edit hook that nudges taskwarrior UUID-safety whenever the
content being written cites a bare integer task ID.

Why content-only, no file-path scoping: an earlier version of this check
(in dotfiles' claude/roles/home.jsonc) restricted itself to three
hardcoded "durable artifact" directories (.parkinglot/, .beans/, the
auto-memory dir). That allowlist missed a bare integer ID landing
repeatedly in CLAUDE.md and a docs file, neither of which was in it. A
bare-content match with no path filter is strictly broader, and the cost
of a false positive is one extra line of additionalContext, so there is
no reason to maintain a path allowlist that will always be one directory
behind wherever the model actually writes prose. See
plugins/taskwarrior/skills/taskwarrior/SKILL.md's "Durable references"
section for the underlying policy.

This intentionally does not try to distinguish a genuine short UUID that
happens to be all-digits (e.g. "09351263") from a real integer ID -- that
ambiguity already existed in the dotfiles version of this check and an
occasional unnecessary nudge is cheap.
"""
import json
import re
import sys

_BARE_ID_RE = re.compile(
    r"\b(?:taskwarrior|task)\s*#?\s*([0-9]{1,6})\b",
    re.IGNORECASE,
)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        tool_input = payload.get("tool_input") or {}
        content = tool_input.get("content")
        if content is None:
            content = tool_input.get("new_string")
        if not isinstance(content, str):
            sys.exit(0)

        match = _BARE_ID_RE.search(content)
        if not match:
            sys.exit(0)

        task_id = match.group(1)
        file_path = tool_input.get("file_path") or "(unknown file)"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": (
                    f"This write to {file_path} cites a bare numeric task "
                    f"reference ({task_id}). Integer taskwarrior IDs are "
                    "reused as the pending list reorders, so anything that "
                    "outlives this shell (docs, CLAUDE.md, commit messages, "
                    "memory, handoffs, PRs) should cite the UUID instead -- "
                    f"verify it first with `task {task_id} info` or "
                    "`task <uuid> info`, don't just reuse a cached ID. See "
                    "the taskwarrior skill's Durable references section."
                ),
            }
        }
        print(json.dumps(output))
    except Exception:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PreToolUse:Bash hook guarding two risky bare-integer-ID patterns in a
single `task` or `git` command:

1. A mutating `task <N> done|annotate|modify|depends|delete|start|stop`
   call by plain decimal ID. Numeric IDs are reused as the pending list
   reorders; if this ID was captured more than a couple of commands ago,
   or anything else touched taskwarrior in between, it may no longer
   point at the intended task.

2. A `git commit` whose message text (via -m or a heredoc body) cites a
   bare integer ID. This is the gap the task-add-time UUID resolver
   (resolve-added-task-uuid.py) can't cover: that hook only fires when
   *creating* a task, so it has nothing to say about citing an
   *existing* task from memory hours or days later, which is exactly
   how a bare ID has landed in a real commit message before.

Formerly two separate hooks living in dotfiles' claude/roles/home.jsonc
(the mutation check) and nowhere at all (the commit-message check).
Consolidated here so this plugin, not personal dotfiles config, is the
single owner of taskwarrior safety behavior -- see plugins/taskwarrior/
skills/taskwarrior/SKILL.md's "Durable references" section.
"""
import json
import re
import sys

_MUTATION_RE = re.compile(
    r"\btask\s+([0-9]{1,6})\s+"
    r"(done|annotate|modify|depends|delete|start|stop)\b"
)
_BARE_ID_RE = re.compile(
    r"\b(?:taskwarrior|task)\s*#?\s*([0-9]{1,6})\b",
    re.IGNORECASE,
)
_GIT_COMMIT_RE = re.compile(r"\bgit\s+commit\b")


def _mutation_context(command: str) -> str | None:
    match = _MUTATION_RE.search(command)
    if not match:
        return None
    task_id, verb = match.group(1), match.group(2)
    return (
        f"This mutates taskwarrior task {task_id} by its plain numeric ID "
        f"(`{verb}`). Numeric IDs are reused as the pending list reorders "
        f"-- if this ID was captured more than a couple of commands ago "
        "(or anything else touched taskwarrior in between), re-resolve it "
        f"first: `task {task_id} info` (or re-grep by description) to "
        "confirm it still points at the task you mean. See the "
        "taskwarrior skill's Durable references section."
    )


def _commit_context(command: str) -> str | None:
    if not _GIT_COMMIT_RE.search(command):
        return None
    match = _BARE_ID_RE.search(command)
    if not match:
        return None
    task_id = match.group(1)
    return (
        f"This commit message cites a bare numeric task reference "
        f"({task_id}). Commit messages outlive the shell they were "
        "written in -- verify this resolves to the intended task "
        f"(`task {task_id} info`) and cite the UUID instead. See the "
        "taskwarrior skill's Durable references section."
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        tool_input = payload.get("tool_input") or {}
        command = tool_input.get("command")
        if not isinstance(command, str):
            sys.exit(0)

        contexts = [
            ctx
            for ctx in (_mutation_context(command), _commit_context(command))
            if ctx
        ]
        if not contexts:
            sys.exit(0)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": " ".join(contexts),
            }
        }
        print(json.dumps(output))
    except Exception:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()

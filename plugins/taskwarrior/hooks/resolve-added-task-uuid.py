#!/usr/bin/env python3
"""
PostToolUse:Bash hook that resolves the UUID of a task just created with
`task add`, without requiring a follow-up model tool call.

Why: `task add` prints "Created task <N>." (a numeric ID), and in practice
the model almost never issues the follow-up `export`/`uuid` call the
taskwarrior skill recommends before citing a task anywhere durable --
checked via cq against a week of sessions, 32 of 33 `task add` calls had
no inline UUID resolution. The numeric ID is what's sitting in context
when the model later writes a park file or commit message, so that's
what gets cited, and it can point at a different task by the time
anything reads it back.

This hook removes the need for the model to remember the follow-up: it
resolves the UUID itself, as a subprocess, and injects it into the same
turn via additionalContext. It only touches `task add` invocations
(detected from the command text) and only fires on a real "Created task
N." success message, so it never runs `task add` itself and never
duplicates a task.

Deliberately scoped to the Bash tool, not to any particular skill --
whatever ran `task add` (a skill, a raw command, some future plugin)
gets the same treatment without this hook needing to know who called it.
"""
import json
import re
import subprocess
import sys

# Matches a `task add` invocation as its own shell segment, requiring
# whitespace or end-of-string after "add" so `task add.after:... list`
# (a filter on the built-in `add` attribute, not the `add` command) does
# not false-positive.
_TASK_ADD_RE = re.compile(r"(?:^|[;&|]|&&)\s*task\s+add(?:\s|$)")

# "Created task 197." (numeric ID) -- the default `new-id` verbose message.
_CREATED_ID_RE = re.compile(r"[Cc]reated task (\d+)\.")

# "Created task <uuid>." -- if `new-uuid` is already configured, the
# message carries a UUID instead and there's nothing to resolve.
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def _result_text(tool_result) -> str:
    """Flatten tool_result to a single string regardless of its shape."""
    if isinstance(tool_result, str):
        return tool_result
    if isinstance(tool_result, dict):
        for key in ("stdout", "output", "text"):
            val = tool_result.get(key)
            if isinstance(val, str):
                return val
        return json.dumps(tool_result, default=str)
    return str(tool_result or "")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        tool_input = payload.get("tool_input") or {}
        command = tool_input.get("command") or ""
        if not _TASK_ADD_RE.search(command):
            sys.exit(0)

        result_text = _result_text(payload.get("tool_result"))

        # new-uuid already configured -- the message already carries a
        # UUID, nothing to resolve.
        if _UUID_RE.search(result_text):
            sys.exit(0)

        match = _CREATED_ID_RE.search(result_text)
        if not match:
            # add failed, or the verbose message is off entirely -- nothing
            # to resolve either way.
            sys.exit(0)

        task_id = match.group(1)
        proc = subprocess.run(
            ["task", "_get", f"{task_id}.uuid"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        uuid = proc.stdout.strip()
        if proc.returncode != 0 or not _UUID_RE.match(uuid):
            sys.exit(0)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"Task {task_id} was created with uuid {uuid}. Cite the "
                    f"uuid, not {task_id}, in anything that outlives this "
                    "shell (park/handoff, commit messages, memory, PRs) -- "
                    "see the taskwarrior skill's Durable references section."
                ),
            }
        }
        print(json.dumps(output))
    except Exception:
        # Never block a tool call over this hook's own failure.
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PostToolUse:Skill hook that injects the current session ID and transcript
path into context when an agent-meta skill that needs them is invoked.

Why: the `park` skill needs the Claude Code session ID to write a durable
record of where this session lived. Previously it ran a Bash script that
echoed $CLAUDE_SESSION_ID, but that env var is not reliably exported to
Bash tool calls, so park often wrote "unknown" as the session.

Hook payloads, on the other hand, always contain `session_id` and
`transcript_path` as guaranteed top-level fields. By reading them here and
emitting `hookSpecificOutput.additionalContext`, Claude sees the session
details right after the Skill tool result, before it starts executing the
skill's steps.

This hook only injects context for skills that actually need it. Other
Skill calls are silently ignored (no context pollution).
"""
import json
import sys

# Skills in the agent-meta plugin that benefit from knowing the session ID.
# Keep this narrow: unparking a session doesn't need the current one, and
# snapshot has its own flow.
TARGET_SKILLS = {
    "agent-meta:park",
}

try:
    payload = json.load(sys.stdin)
except json.JSONDecodeError:
    # Malformed stdin - fail silently so we never block a tool call.
    sys.exit(0)

tool_input = payload.get("tool_input") or {}
skill_name = tool_input.get("skill", "")

if skill_name not in TARGET_SKILLS:
    sys.exit(0)

session_id = payload.get("session_id", "")
transcript_path = payload.get("transcript_path", "")

if not session_id:
    # Nothing useful to inject; let park fall back to its script.
    sys.exit(0)

lines = [f"Session ID: {session_id}"]
if transcript_path:
    lines.append(f"Transcript: {transcript_path}")

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n".join(lines),
    }
}
print(json.dumps(output))
sys.exit(0)

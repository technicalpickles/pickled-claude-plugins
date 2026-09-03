#!/usr/bin/env python3
"""
PostToolUse:Skill hook that injects the current session ID, transcript
path, and (for park) a configured destination command into context when
an agent-meta skill that needs them is invoked.

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

Destination command: park can optionally hand its output to an external
command (e.g. filing it into a second-brain vault) instead of only
writing a local file. This is configured via env vars, resolved here
rather than hardcoded into the skill, so the plugin stays agnostic about
where a "destination" actually is:

- AGENT_PARK_DESTINATION_HELPER: a no-arg command, run once by this hook;
  its trimmed stdout is used as the destination command template. Lets
  the destination be computed at park-time (e.g. by inspecting the
  project) rather than being a fixed string. Wins over the literal var
  below if both are set.
- AGENT_PARK_DESTINATION: a literal destination command template, used
  as-is when no helper is set (or the helper produces nothing usable).

Either way the result is a single-line command template containing
{file}/{title}/{mode} placeholders, injected as a `Park destination:`
line. The skill body - not this hook - is responsible for substituting
the placeholders and actually running the command, visibly, via Bash.
This hook never executes the destination command itself, only (when a
helper is configured) the helper that produces its template.
"""
import json
import os
import subprocess
import sys

# Skills in the agent-meta plugin that benefit from knowing the session ID.
# Keep this narrow: unparking a session doesn't need the current one, and
# snapshot has its own flow.
TARGET_SKILLS = {
    "agent-meta:park",
}

# Guardrails against a misbehaving helper: a destination template is a
# single command line, not a blob. Reject anything that doesn't look like
# one rather than silently forwarding garbage into context.
MAX_TEMPLATE_LENGTH = 2000


def resolve_destination_template():
    """Return a validated destination command template, or None."""
    helper = os.environ.get("AGENT_PARK_DESTINATION_HELPER", "").strip()
    if helper:
        try:
            result = subprocess.run(
                helper,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except Exception:
            result = None

        if result is not None and result.returncode == 0:
            candidate = result.stdout.strip()
            if _is_valid_template(candidate):
                return candidate
        # Helper failed, timed out, or produced something unusable - fall
        # through to the literal env var rather than erroring out.

    literal = os.environ.get("AGENT_PARK_DESTINATION", "").strip()
    if _is_valid_template(literal):
        return literal

    return None


def _is_valid_template(candidate):
    if not candidate:
        return False
    if len(candidate) > MAX_TEMPLATE_LENGTH:
        return False
    if "\n" in candidate or "\r" in candidate:
        return False
    return True


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

lines = []
if session_id:
    lines.append(f"Session ID: {session_id}")
    if transcript_path:
        lines.append(f"Transcript: {transcript_path}")

destination_template = resolve_destination_template()
if destination_template:
    lines.append(f"Park destination: {destination_template}")

if not lines:
    # Nothing useful to inject; let park fall back to its script.
    sys.exit(0)

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n".join(lines),
    }
}
print(json.dumps(output))
sys.exit(0)

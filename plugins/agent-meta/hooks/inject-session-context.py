#!/usr/bin/env python3
"""
PostToolUse:Skill hook that injects park's configured destination command
into context when `agent-meta:park` is invoked through the Skill tool.

The session ID is not injected here. A /agent-meta:park slash invocation
makes no Skill tool call, so this hook never fires for it. Park gets the ID
from the ${CLAUDE_SESSION_ID} substitution in its SKILL.md instead, which
Claude Code fills in on both paths.

This hook only injects context for skills that actually need it. Other
Skill calls are silently ignored (no context pollution).

Destination command: park can optionally hand its output to an external
command (e.g. filing it into a second-brain vault) instead of only
writing a local file. This is configured via env vars, resolved here
rather than hardcoded into the skill, so the plugin stays agnostic about
where a "destination" actually is:

- Plugin settings `destination_helper` and `destination` (exported as
  CLAUDE_PLUGIN_OPTION_DESTINATION_HELPER / CLAUDE_PLUGIN_OPTION_DESTINATION)
  are the preferred way. The env vars below still work as a fallback.
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

# Skills that take a destination command. Keep this narrow.
TARGET_SKILLS = {
    "agent-meta:park",
}

# Guardrails against a misbehaving helper: a destination template is a
# single command line, not a blob. Reject anything that doesn't look like
# one rather than silently forwarding garbage into context.
MAX_TEMPLATE_LENGTH = 2000


def _run_helper(helper):
    try:
        result = subprocess.run(
            helper,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    candidate = result.stdout.strip()
    return candidate if _is_valid_template(candidate) else None


def resolve_destination_template():
    """Return a validated destination command template, or None.

    Plugin settings (`destination_helper`, `destination`) come first, as
    Claude Code exports them to hooks. The legacy AGENT_PARK_DESTINATION_HELPER
    and AGENT_PARK_DESTINATION env vars are the fallback. Within each pair the
    helper wins, and a helper that fails or yields nothing usable falls through
    to the literal rather than erroring out.
    """
    sources = (
        ("CLAUDE_PLUGIN_OPTION_DESTINATION_HELPER", "CLAUDE_PLUGIN_OPTION_DESTINATION"),
        ("AGENT_PARK_DESTINATION_HELPER", "AGENT_PARK_DESTINATION"),
    )
    for helper_var, literal_var in sources:
        helper = os.environ.get(helper_var, "").strip()
        if helper:
            candidate = _run_helper(helper)
            if candidate:
                return candidate
        literal = os.environ.get(literal_var, "").strip()
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

destination_template = resolve_destination_template()
if not destination_template:
    sys.exit(0)

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": f"Park destination: {destination_template}",
    }
}
print(json.dumps(output))
sys.exit(0)

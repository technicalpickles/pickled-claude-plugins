#!/usr/bin/env python3
"""
PostToolUse:Skill hook that runs the sb CLI diagnostic when a sb-dependent
second-brain skill activates, so a broken npx/sb setup surfaces before the
skill's first sb call - without spending a model turn on a proactive check
in the common case where sb is fine.

Stays completely silent (no additionalContext) when sb is healthy. Only
injects context when scripts/diagnose-sb.sh actually finds a problem.
"""
import json
import os
import subprocess
import sys

# second-brain skills/commands whose first step calls the sb CLI.
TARGET_SKILLS = {
    "second-brain:distill-conversation",
    "second-brain:route",
    "second-brain:setup",
    "second-brain:insight",
    "second-brain:capture",
    "second-brain:process-inbox",
    "second-brain:search",
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

plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
script = os.path.join(plugin_root, "scripts", "diagnose-sb.sh")

if not os.path.isfile(script):
    sys.exit(0)

try:
    result = subprocess.run([script], capture_output=True, text=True, timeout=15)
except Exception:
    # Never block a skill because this hook itself broke.
    sys.exit(0)

if result.returncode == 0:
    sys.exit(0)  # sb is healthy - inject nothing

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": (
            "sb CLI diagnostic found a problem before this skill's first sb "
            f"call:\n{result.stdout.strip()}"
        ),
    }
}
print(json.dumps(output))
sys.exit(0)

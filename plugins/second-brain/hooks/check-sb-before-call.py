#!/usr/bin/env python3
"""
PreToolUse:Bash hook, declared in the frontmatter of the sb-dependent
second-brain skills/commands (not the plugin's own hooks/hooks.json - this
only registers while one of those skills is active).

Runs the sb CLI diagnostic in front of the actual `npx @techpickles/sb` Bash
call it's about to allow, so a broken npx/sb setup surfaces before the real
call fails - without spending a model turn on a proactive check. Ignores
every other Bash call outright, and stays silent (plain allow, no
additionalContext) when sb is healthy.
"""
import json
import os
import subprocess
import sys

try:
    payload = json.load(sys.stdin)
except json.JSONDecodeError:
    # Malformed stdin - fail silently so we never block a tool call.
    sys.exit(0)

tool_input = payload.get("tool_input") or {}
command = tool_input.get("command", "")

if "@techpickles/sb" not in command:
    sys.exit(0)  # not an sb call - nothing to check

plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
script = os.path.join(plugin_root, "scripts", "diagnose-sb.sh")

if not os.path.isfile(script):
    sys.exit(0)

try:
    result = subprocess.run([script], capture_output=True, text=True, timeout=15)
except Exception:
    # Never block the real call because this hook itself broke.
    sys.exit(0)

if result.returncode == 0:
    sys.exit(0)  # sb is healthy - allow silently, inject nothing

output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "additionalContext": (
            "sb CLI diagnostic found a problem before this call:\n"
            f"{result.stdout.strip()}"
        ),
    }
}
print(json.dumps(output))
sys.exit(0)

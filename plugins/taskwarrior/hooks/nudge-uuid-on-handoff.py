#!/usr/bin/env python3
"""
PostToolUse:Skill hook that nudges taskwarrior UUID-safety when a skill
that writes a durable, resumed-later artifact (currently: agent-meta's
`park`) is invoked.

Why here and not in the other skill: the taskwarrior UUID-drift problem
belongs to this plugin, not to every skill that might happen to write a
handoff. Putting the reminder in park's own instructions would couple a
general-purpose skill to one specific tool it knows nothing else about,
and the coupling would need to be repeated for every other skill that
writes a durable artifact. A hook keyed off `tool_input.skill` lets this
plugin own the reminder and attach it to whichever skills warrant it,
without editing their instructions.

This hook only fires for skills in TARGET_SKILLS. Other Skill calls are
silently ignored (no context pollution).
"""
import json
import sys

# Skills that write durable, resumed-later artifacts where a taskwarrior
# reference might get baked in stale. Add to this set as other such skills
# come up; each addition should be a one-line change here, not an edit to
# the target skill's own instructions.
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

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": (
            "If this handoff cites a taskwarrior task, cite it by UUID and verify "
            "the UUID resolves to the intended task first (`task <uuid> info`) -- "
            "a wrong-but-correctly-formatted UUID has landed in a handoff before. "
            "Never cite the bare integer ID; it can be reassigned to a different "
            "task by the time the handoff is resumed. See the taskwarrior skill's "
            "Durable references section."
        ),
    }
}
print(json.dumps(output))
sys.exit(0)

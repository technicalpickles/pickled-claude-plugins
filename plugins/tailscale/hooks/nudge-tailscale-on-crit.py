#!/usr/bin/env python3
"""PreToolUse hook: nudge toward the tailnet-URL helper before crit runs.

crit's own skill (crit:crit) launches a local review server and, when
reviewing over Tailscale, needs a tailnet URL to hand back. Several past
sessions re-derived "find tailscale, read status --json, strip the
trailing dot off DNSName" from scratch each time. This hook fires right
before crit:crit runs and points at the shared helper script instead, so
that logic lives in one place.

Reads the PreToolUse JSON payload from stdin. If tool_name is "Skill" and
tool_input.skill == "crit:crit", emits
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": ...}}
so Claude sees the reminder before crit's own skill content loads. Any
non-match (wrong tool, wrong skill, unparseable payload) exits 0 silently
-- this hook only ever adds context, never blocks.
"""

from __future__ import annotations

import json
import sys

TARGET_SKILL = "crit:crit"
ADVICE = (
    "Before launching crit with a Tailscale --public-url, resolve the URL with "
    '"${CLAUDE_PLUGIN_ROOT}/scripts/resolve-tailnet-url.sh" <port> (from the '
    "tailscale plugin) instead of re-deriving it from `tailscale status --json` "
    "by hand -- it already handles the GUI-app-not-on-PATH lookup, the "
    "trailing dot on Self.DNSName, and checking BackendState before promising "
    "a URL. Note: reading tailscaled's status requires the sandbox bypass "
    "(dangerouslyDisableSandbox), same as any other tailscale command."
)


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0

    if not isinstance(payload, dict):
        return 0
    if payload.get("tool_name") != "Skill":
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0
    if tool_input.get("skill") != TARGET_SKILL:
        return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": ADVICE,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())

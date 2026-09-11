#!/usr/bin/env python3
"""Conditional advice emitter for PreToolUse hooks on the Skill tool.

Reads the PreToolUse JSON payload from stdin. If tool_name is "Skill" and
tool_input.skill matches --skill, optionally checks --if-file (resolved
against payload.cwd or os.getcwd() if relative), and on success emits
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": ...}}
to stdout. Any non-match exits 0 silently. Misconfiguration (missing
required args) exits non-zero so settings.json mistakes surface during
development.

Wired in settings.json via:

    {
      "hooks": {
        "PreToolUse": [{
          "matcher": "Skill",
          "hooks": [{
            "type": "command",
            "command": "python3 \\"${CLAUDE_PLUGIN_ROOT}/scripts/skill-advice.py\\" --skill <name> --advice <text>"
          }]
        }]
      }
    }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Conditional advice emitter for Skill PreToolUse hooks.",
    )
    parser.add_argument("--skill", required=True, help="Target skill name to match.")
    parser.add_argument(
        "--if-file",
        dest="if_file",
        help="Optional path. Skip emission if the file does not exist.",
    )
    parser.add_argument(
        "--advice",
        required=True,
        help="Text emitted as additionalContext when the match succeeds.",
    )
    args = parser.parse_args(argv)

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
    if tool_input.get("skill") != args.skill:
        return 0

    if args.if_file:
        cwd = payload.get("cwd") or os.getcwd()
        candidate = Path(args.if_file)
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        if not candidate.exists():
            return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": args.advice,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command-line interface for writing-tools."""

import argparse
import json
import os
import sys

from writing_tools.checker import check_tool_call
from writing_tools.config import load_config

DEBUG = os.environ.get("WRITING_TOOLS_DEBUG", "").lower() in ("1", "true", "yes")


def cmd_check(args: argparse.Namespace) -> int:
    """PreToolUse hook entry point: block outbound em-dashes.

    Reads the tool call JSON from stdin, decides, and on a block emits the
    Claude Code deny decision to stdout. Always exits 0 (fail open); a crash
    or malformed input must never wedge the tool it's gating.
    """
    try:
        raw_input = sys.stdin.read()
        tool_call = json.loads(raw_input)
    except (json.JSONDecodeError, ValueError):
        return 0

    try:
        result = check_tool_call(tool_call, load_config)
    except Exception as e:  # noqa: BLE001 - fail open on any checker error
        if DEBUG:
            print(f"writing-tools check errored (allowing): {e}", file=sys.stderr)
        return 0

    if result.blocked:
        if DEBUG:
            print(f"❌ writing-tools: {result.reason}", file=sys.stderr)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": result.reason,
            }
        }
        print(json.dumps(output))
        return 0

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="writing-tools",
        description="Writing hygiene checks for Claude Code",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="Check a tool call for outbound em-dashes (hook entry point)",
    )
    check_parser.set_defaults(func=cmd_check)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

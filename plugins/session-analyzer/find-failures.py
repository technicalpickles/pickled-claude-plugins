#!/usr/bin/env python3
"""Find failed tool calls in Claude session logs."""

import argparse
import json
import signal
import sys
from pathlib import Path

# Handle broken pipe gracefully (e.g., when piping to `less` and quitting early)
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

ALLOWED_ROOT = Path.home() / ".claude" / "projects"


def is_allowed_path(path: Path) -> bool:
    """Check if path is within ~/.claude/projects."""
    try:
        resolved = path.resolve()
        return resolved.is_relative_to(ALLOWED_ROOT)
    except (OSError, ValueError):
        return False


def collect_jsonl_files(paths: list[Path]) -> list[Path]:
    """Expand paths to individual .jsonl files, filtering to allowed locations."""
    jsonl_files = []

    for path in paths:
        if not path.exists():
            print(f"Warning: Path not found: {path}", file=sys.stderr)
            continue

        if not is_allowed_path(path):
            print(f"Warning: Skipping path outside ~/.claude/projects: {path}", file=sys.stderr)
            continue

        if path.is_file():
            if path.suffix == ".jsonl":
                jsonl_files.append(path)
            else:
                print(f"Warning: Skipping non-JSONL file: {path}", file=sys.stderr)
        elif path.is_dir():
            # Recursively find all .jsonl files
            jsonl_files.extend(sorted(path.rglob("*.jsonl")))

    return jsonl_files


def parse_session(jsonl_path: Path) -> dict[str, dict]:
    """Parse JSONL file and return entries indexed by UUID."""
    entries = {}

    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            uuid = entry.get("uuid")
            if uuid:
                entries[uuid] = entry

    return entries


def find_tool_use(entries: dict[str, dict], tool_use_id: str, start_uuid: str) -> dict | None:
    """Walk parent chain to find the tool_use message matching tool_use_id."""
    current_uuid = entries.get(start_uuid, {}).get("parentUuid")

    while current_uuid:
        entry = entries.get(current_uuid)
        if not entry:
            break

        message = entry.get("message", {})
        content = message.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    if item.get("id") == tool_use_id:
                        return {
                            "uuid": current_uuid,
                            "name": item.get("name", "unknown"),
                            "input": item.get("input", {}),
                        }

        current_uuid = entry.get("parentUuid")

    return None


def find_failures(jsonl_path: Path) -> list[dict]:
    """Parse JSONL file and extract failed tool calls."""
    entries = parse_session(jsonl_path)
    failures = []

    for entry in entries.values():
        # Look for tool_result with is_error: true
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            continue

        for item in content:
            if isinstance(item, dict) and item.get("is_error") is True:
                tool_use_id = item.get("tool_use_id", "unknown")
                tool_use = find_tool_use(entries, tool_use_id, entry.get("uuid", ""))

                failures.append({
                    "file_path": str(jsonl_path.resolve()),
                    "request_uuid": tool_use["uuid"] if tool_use else "unknown",
                    "response_uuid": entry.get("uuid", "unknown"),
                    "tool_use_id": tool_use_id,
                    "tool_name": tool_use["name"] if tool_use else "unknown",
                    "tool_input": tool_use["input"] if tool_use else {},
                    "error_content": item.get("content", ""),
                })

    return failures


def format_tool_input(tool_name: str, tool_input: dict, indent: str) -> list[str]:
    """Format tool input based on tool type."""
    lines = []

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        if desc:
            lines.append(f"{indent}Description: {desc}")
        lines.append(f"{indent}Command:")
        for cmd_line in command.split("\n"):
            lines.append(f"{indent}  {cmd_line}")
    elif tool_name in ("Read", "Write", "Edit", "Glob"):
        # File operations - show key params
        for key, value in tool_input.items():
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            lines.append(f"{indent}{key}: {value}")
    else:
        # Generic: dump as JSON
        input_str = json.dumps(tool_input, indent=2)
        for input_line in input_str.split("\n"):
            lines.append(f"{indent}{input_line}")

    return lines


def format_failure(index: int, failure: dict) -> str:
    """Format a failure for human-readable output."""
    indent = "  "
    lines = [
        f"━━━ Failure #{index} ━━━",
        f"{indent}{failure['file_path']}",
        f"{indent}Tool: {failure['tool_name']}",
        f"{indent}Request UUID: {failure['request_uuid']}",
    ]

    # Add tool input
    lines.append(f"{indent}Input:")
    lines.extend(format_tool_input(failure["tool_name"], failure["tool_input"], indent + indent))

    # Add error with response UUID
    lines.append(f"{indent}Response UUID: {failure['response_uuid']}")
    lines.append(f"{indent}Error:")
    for error_line in failure["error_content"].split("\n"):
        lines.append(f"{indent}{indent}{error_line}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Find failed tool calls in Claude session logs.",
        epilog="Only files within ~/.claude/projects are allowed.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        metavar="PATH",
        help="JSONL file(s) or directory(ies) to scan",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (one object per line)",
    )
    args = parser.parse_args()

    jsonl_files = collect_jsonl_files(args.paths)

    if not jsonl_files:
        print("No valid JSONL files found.", file=sys.stderr)
        sys.exit(1)

    all_failures = []
    for jsonl_file in jsonl_files:
        all_failures.extend(find_failures(jsonl_file))

    if args.json:
        for failure in all_failures:
            print(json.dumps(failure))
        sys.exit(0)

    if not all_failures:
        print(f"No failures found in {len(jsonl_files)} file(s).")
        sys.exit(0)

    print(f"Found {len(all_failures)} failure(s) in {len(jsonl_files)} file(s):\n")

    for i, failure in enumerate(all_failures, 1):
        print(format_failure(i, failure))
        print()


if __name__ == "__main__":
    main()

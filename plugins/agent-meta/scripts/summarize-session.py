#!/usr/bin/env python3
"""Summarize a Claude session into key events.

Extracts:
- Tool call counts by type
- Files touched (read, written, edited)
- Failed tool calls
- Session duration estimate
- Key patterns and pain points
"""

import argparse
import json
import signal
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

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
            jsonl_files.extend(sorted(path.rglob("*.jsonl")))

    return jsonl_files


def parse_session(jsonl_path: Path) -> list[dict]:
    """Parse JSONL file and return entries in order."""
    entries = []

    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    return entries


def extract_tool_calls(entries: list[dict]) -> list[dict]:
    """Extract all tool calls from session entries."""
    tool_calls = []

    for entry in entries:
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            continue

        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_calls.append({
                    "uuid": entry.get("uuid"),
                    "timestamp": entry.get("timestamp"),
                    "name": item.get("name", "unknown"),
                    "input": item.get("input", {}),
                    "id": item.get("id"),
                })

    return tool_calls


def extract_tool_results(entries: list[dict]) -> dict[str, dict]:
    """Extract tool results indexed by tool_use_id."""
    results = {}

    for entry in entries:
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            continue

        for item in content:
            if isinstance(item, dict) and item.get("tool_use_id"):
                results[item["tool_use_id"]] = {
                    "is_error": item.get("is_error", False),
                    "content": item.get("content", ""),
                }

    return results


def extract_files_touched(tool_calls: list[dict]) -> dict[str, set[str]]:
    """Extract files that were read, written, or edited."""
    files = {
        "read": set(),
        "written": set(),
        "edited": set(),
        "globbed": set(),
    }

    for call in tool_calls:
        name = call["name"]
        inp = call["input"]

        if name == "Read":
            path = inp.get("file_path", "")
            if path:
                files["read"].add(path)
        elif name == "Write":
            path = inp.get("file_path", "")
            if path:
                files["written"].add(path)
        elif name == "Edit":
            path = inp.get("file_path", "")
            if path:
                files["edited"].add(path)
        elif name == "Glob":
            pattern = inp.get("pattern", "")
            if pattern:
                files["globbed"].add(pattern)

    return files


def extract_bash_commands(tool_calls: list[dict]) -> list[dict]:
    """Extract Bash commands with their descriptions."""
    commands = []

    for call in tool_calls:
        if call["name"] == "Bash":
            inp = call["input"]
            commands.append({
                "command": inp.get("command", ""),
                "description": inp.get("description", ""),
                "uuid": call["uuid"],
            })

    return commands


def estimate_duration(entries: list[dict]) -> str | None:
    """Estimate session duration from timestamps."""
    timestamps = []

    for entry in entries:
        ts = entry.get("timestamp")
        if ts:
            try:
                # Handle ISO format timestamps
                if isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    timestamps.append(dt)
                elif isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(ts / 1000)  # milliseconds
                    timestamps.append(dt)
            except (ValueError, OSError):
                continue

    if len(timestamps) < 2:
        return None

    duration = max(timestamps) - min(timestamps)
    total_seconds = int(duration.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds} seconds"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"~{minutes} minutes"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"~{hours}h {minutes}m"


def find_repeated_failures(tool_calls: list[dict], tool_results: dict[str, dict]) -> list[dict]:
    """Find patterns of repeated failures."""
    failure_patterns = defaultdict(list)

    for call in tool_calls:
        result = tool_results.get(call["id"], {})
        if result.get("is_error"):
            # Group by tool name and error content prefix
            error_content = result.get("content", "")[:100]
            key = (call["name"], error_content)
            failure_patterns[key].append(call)

    repeated = []
    for (tool_name, error_prefix), calls in failure_patterns.items():
        if len(calls) >= 2:
            repeated.append({
                "tool": tool_name,
                "error_prefix": error_prefix,
                "count": len(calls),
                "calls": calls,
            })

    return sorted(repeated, key=lambda x: x["count"], reverse=True)


def summarize_session(jsonl_path: Path) -> dict:
    """Generate a summary of a session."""
    entries = parse_session(jsonl_path)
    tool_calls = extract_tool_calls(entries)
    tool_results = extract_tool_results(entries)

    # Count tool calls by type
    tool_counts = defaultdict(int)
    for call in tool_calls:
        tool_counts[call["name"]] += 1

    # Count failures
    failure_count = sum(1 for r in tool_results.values() if r.get("is_error"))

    # Extract files
    files_touched = extract_files_touched(tool_calls)

    # Find repeated failures
    repeated_failures = find_repeated_failures(tool_calls, tool_results)

    # Extract bash commands
    bash_commands = extract_bash_commands(tool_calls)

    return {
        "file_path": str(jsonl_path.resolve()),
        "duration": estimate_duration(entries),
        "entry_count": len(entries),
        "tool_calls": {
            "total": len(tool_calls),
            "failures": failure_count,
            "by_type": dict(tool_counts),
        },
        "files": {
            "read": sorted(files_touched["read"]),
            "written": sorted(files_touched["written"]),
            "edited": sorted(files_touched["edited"]),
            "glob_patterns": sorted(files_touched["globbed"]),
        },
        "bash_commands": bash_commands,
        "repeated_failures": repeated_failures,
    }


def format_summary(summary: dict) -> str:
    """Format summary for human-readable output."""
    lines = ["━━━ Session Summary ━━━"]

    # Basic stats
    duration = summary["duration"] or "unknown"
    lines.append(f"Duration: {duration}")
    lines.append(f"Entries: {summary['entry_count']}")

    tc = summary["tool_calls"]
    lines.append(f"Tool calls: {tc['total']} ({tc['failures']} failed)")
    lines.append("")

    # Tool breakdown
    lines.append("Tool usage:")
    for tool, count in sorted(tc["by_type"].items(), key=lambda x: -x[1]):
        lines.append(f"  {tool}: {count}")
    lines.append("")

    # Files touched
    files = summary["files"]
    all_files = set(files["read"]) | set(files["written"]) | set(files["edited"])

    if all_files:
        lines.append("Files touched:")
        for f in sorted(all_files):
            markers = []
            if f in files["written"]:
                markers.append("new")
            if f in files["edited"]:
                markers.append("modified")
            if f in files["read"] and f not in files["written"] and f not in files["edited"]:
                markers.append("read")

            marker_str = f" ({', '.join(markers)})" if markers else ""
            # Truncate long paths
            display_path = f if len(f) < 60 else "..." + f[-57:]
            lines.append(f"  {display_path}{marker_str}")
        lines.append("")

    # Repeated failures (pain points)
    if summary["repeated_failures"]:
        lines.append("Pain points (repeated failures):")
        for rf in summary["repeated_failures"][:5]:
            lines.append(f"  {rf['tool']} failed {rf['count']}x: {rf['error_prefix'][:50]}...")
        lines.append("")

    # Sample bash commands
    bash = summary["bash_commands"]
    if bash:
        lines.append(f"Bash commands: {len(bash)} total")
        # Show first few with descriptions
        for cmd in bash[:5]:
            desc = cmd["description"]
            if desc:
                lines.append(f"  - {desc}")
            else:
                cmd_preview = cmd["command"][:50]
                if len(cmd["command"]) > 50:
                    cmd_preview += "..."
                lines.append(f"  - {cmd_preview}")
        if len(bash) > 5:
            lines.append(f"  ... and {len(bash) - 5} more")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Summarize a Claude session into key events.",
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
        help="Output results as JSON",
    )
    args = parser.parse_args()

    jsonl_files = collect_jsonl_files(args.paths)

    if not jsonl_files:
        print("No valid JSONL files found.", file=sys.stderr)
        sys.exit(1)

    for jsonl_file in jsonl_files:
        summary = summarize_session(jsonl_file)

        if args.json:
            print(json.dumps(summary))
        else:
            if len(jsonl_files) > 1:
                print(f"\n=== {jsonl_file} ===\n")
            print(format_summary(summary))
            print()


if __name__ == "__main__":
    main()

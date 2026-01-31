#!/usr/bin/env python3
"""Trace hook execution through Claude session logs.

Finds:
- Hook output injected into conversations
- System reminders from hooks
- PreToolUse/PostToolUse modifications
- SessionStart hook content
"""

import argparse
import json
import re
import signal
import sys
from collections import defaultdict
from pathlib import Path

signal.signal(signal.SIGPIPE, signal.SIG_DFL)

ALLOWED_ROOT = Path.home() / ".claude" / "projects"

# Patterns that indicate hook-generated content
HOOK_PATTERNS = [
    # SessionStart hooks often inject these
    (r"<system-reminder>.*?</system-reminder>", "system-reminder"),
    (r"SessionStart:?\s*\w+\s*hook", "session-start"),
    (r"SessionStart hook", "session-start"),
    # PreToolUse suggestions
    (r"Suggestion:\s*Use\s+\w+\s+instead", "tool-routing"),
    (r"Consider using\s+\w+\s+tool", "tool-routing"),
    # Common hook output markers
    (r"hook success:", "hook-success"),
    (r"hook failed:", "hook-failed"),
    (r"hook additional context:", "hook-context"),
]


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


def extract_text_content(entry: dict) -> str:
    """Extract all text content from an entry."""
    message = entry.get("message", {})
    content = message.get("content", [])

    texts = []

    if isinstance(content, str):
        texts.append(content)
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
                elif item.get("type") == "tool_result":
                    result_content = item.get("content", "")
                    if isinstance(result_content, str):
                        texts.append(result_content)

    return "\n".join(texts)


def find_hook_traces(entries: list[dict]) -> list[dict]:
    """Find entries that contain hook-related content."""
    traces = []

    for entry in entries:
        text = extract_text_content(entry)
        if not text:
            continue

        # Check for hook patterns
        matches = []
        for pattern, hook_type in HOOK_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                matches.append({
                    "type": hook_type,
                    "match": match.group()[:200],  # Truncate long matches
                    "position": match.start(),
                })

        # Also check for system-reminder tags specifically
        system_reminders = re.findall(
            r"<system-reminder>(.*?)</system-reminder>",
            text,
            re.DOTALL
        )

        if matches or system_reminders:
            trace = {
                "uuid": entry.get("uuid"),
                "timestamp": entry.get("timestamp"),
                "type": entry.get("type"),
                "role": entry.get("message", {}).get("role"),
                "hook_matches": matches,
                "system_reminders": [r[:500] for r in system_reminders],  # Truncate
            }
            traces.append(trace)

    return traces


def categorize_hooks(traces: list[dict]) -> dict[str, list[dict]]:
    """Categorize hook traces by type."""
    categories = defaultdict(list)

    for trace in traces:
        # Categorize by hook match types
        for match in trace.get("hook_matches", []):
            categories[match["type"]].append({
                "uuid": trace["uuid"],
                "match": match["match"],
            })

        # System reminders get their own category
        for reminder in trace.get("system_reminders", []):
            categories["system-reminder"].append({
                "uuid": trace["uuid"],
                "content": reminder,
            })

    return dict(categories)


def trace_hooks(jsonl_path: Path) -> dict:
    """Generate hook trace for a session."""
    entries = parse_session(jsonl_path)
    traces = find_hook_traces(entries)
    categories = categorize_hooks(traces)

    return {
        "file_path": str(jsonl_path.resolve()),
        "entry_count": len(entries),
        "hook_traces": len(traces),
        "categories": categories,
        "traces": traces,
    }


def format_trace(result: dict) -> str:
    """Format hook trace for human-readable output."""
    lines = ["━━━ Hook Traces ━━━"]
    lines.append(f"Session entries: {result['entry_count']}")
    lines.append(f"Entries with hooks: {result['hook_traces']}")
    lines.append("")

    categories = result["categories"]

    if not categories:
        lines.append("No hook traces found.")
        return "\n".join(lines)

    # Summary by category
    lines.append("Hook types detected:")
    for cat, items in sorted(categories.items()):
        lines.append(f"  {cat}: {len(items)} occurrence(s)")
    lines.append("")

    # Details by category
    for cat, items in sorted(categories.items()):
        lines.append(f"━━ {cat} ━━")

        # Show up to 3 examples per category
        for item in items[:3]:
            if "content" in item:
                # System reminder
                content_preview = item["content"][:100].replace("\n", " ")
                if len(item["content"]) > 100:
                    content_preview += "..."
                lines.append(f"  [{item['uuid'][:8]}] {content_preview}")
            elif "match" in item:
                # Pattern match
                match_preview = item["match"][:80].replace("\n", " ")
                lines.append(f"  [{item['uuid'][:8]}] {match_preview}")

        if len(items) > 3:
            lines.append(f"  ... and {len(items) - 3} more")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Trace hook execution through Claude session logs.",
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
        result = trace_hooks(jsonl_file)

        if args.json:
            print(json.dumps(result))
        else:
            if len(jsonl_files) > 1:
                print(f"\n=== {jsonl_file} ===\n")
            print(format_trace(result))
            print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Analyze tool-routing suggestions and outcomes.

Tracks:
- Suggestions made by tool-routing hooks
- Whether suggestions were followed
- Patterns of ignored suggestions
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

# Patterns for tool-routing suggestions
SUGGESTION_PATTERNS = [
    # "Suggestion: Use Read instead of Bash"
    r"Suggestion:\s*Use\s+(\w+)\s+instead\s+of\s+(\w+)",
    # "Consider using Grep tool instead"
    r"Consider using\s+(\w+)\s+(?:tool\s+)?instead",
    # "Prefer Read over cat"
    r"Prefer\s+(\w+)\s+over\s+(\w+)",
    # Tool routing specific format
    r"tool-routing.*?suggests?\s+(\w+)",
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


def extract_tool_calls(entries: list[dict]) -> list[dict]:
    """Extract all tool calls with their entry index."""
    tool_calls = []

    for i, entry in enumerate(entries):
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            continue

        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_calls.append({
                    "index": i,
                    "uuid": entry.get("uuid"),
                    "name": item.get("name", "unknown"),
                    "input": item.get("input", {}),
                    "id": item.get("id"),
                })

    return tool_calls


def find_suggestions(entries: list[dict]) -> list[dict]:
    """Find tool-routing suggestions in session entries."""
    suggestions = []

    for i, entry in enumerate(entries):
        text = extract_text_content(entry)
        if not text:
            continue

        for pattern in SUGGESTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = match.groups()

                suggestion = {
                    "index": i,
                    "uuid": entry.get("uuid"),
                    "match_text": match.group(),
                    "suggested_tool": groups[0] if groups else None,
                    "instead_of": groups[1] if len(groups) > 1 else None,
                }
                suggestions.append(suggestion)

    return suggestions


def analyze_suggestion_outcomes(
    suggestions: list[dict],
    tool_calls: list[dict],
    entries: list[dict]
) -> list[dict]:
    """Analyze whether suggestions were followed."""
    analyzed = []

    for suggestion in suggestions:
        suggestion_idx = suggestion["index"]
        suggested_tool = suggestion["suggested_tool"]
        instead_of = suggestion["instead_of"]

        # Find the next tool call after this suggestion
        next_calls = [tc for tc in tool_calls if tc["index"] > suggestion_idx]

        if not next_calls:
            outcome = "no_subsequent_call"
            next_tool = None
        else:
            next_call = next_calls[0]
            next_tool = next_call["name"]

            if suggested_tool and next_tool.lower() == suggested_tool.lower():
                outcome = "followed"
            elif instead_of and next_tool.lower() == instead_of.lower():
                outcome = "ignored"
            else:
                outcome = "different_tool"

        analyzed.append({
            **suggestion,
            "outcome": outcome,
            "next_tool": next_tool,
        })

    return analyzed


def aggregate_outcomes(analyzed: list[dict]) -> dict:
    """Aggregate outcomes into summary statistics."""
    total = len(analyzed)
    followed = sum(1 for a in analyzed if a["outcome"] == "followed")
    ignored = sum(1 for a in analyzed if a["outcome"] == "ignored")
    different = sum(1 for a in analyzed if a["outcome"] == "different_tool")
    no_call = sum(1 for a in analyzed if a["outcome"] == "no_subsequent_call")

    # Group ignored suggestions
    ignored_patterns = defaultdict(int)
    for a in analyzed:
        if a["outcome"] == "ignored":
            key = f"Use {a['suggested_tool']} instead of {a['instead_of']}"
            ignored_patterns[key] += 1

    return {
        "total": total,
        "followed": followed,
        "ignored": ignored,
        "different_tool": different,
        "no_subsequent_call": no_call,
        "follow_rate": (followed / total * 100) if total > 0 else 0,
        "ignored_patterns": dict(ignored_patterns),
    }


def analyze_routing(jsonl_path: Path) -> dict:
    """Analyze tool-routing for a session."""
    entries = parse_session(jsonl_path)
    tool_calls = extract_tool_calls(entries)
    suggestions = find_suggestions(entries)
    analyzed = analyze_suggestion_outcomes(suggestions, tool_calls, entries)
    summary = aggregate_outcomes(analyzed)

    return {
        "file_path": str(jsonl_path.resolve()),
        "entry_count": len(entries),
        "tool_call_count": len(tool_calls),
        "summary": summary,
        "suggestions": analyzed,
    }


def format_analysis(result: dict) -> str:
    """Format analysis for human-readable output."""
    lines = ["━━━ Routing Analysis ━━━"]

    summary = result["summary"]
    total = summary["total"]

    if total == 0:
        lines.append("No tool-routing suggestions found.")
        return "\n".join(lines)

    lines.append(f"Suggestions made: {total}")
    lines.append(f"Suggestions followed: {summary['followed']} ({summary['follow_rate']:.0f}%)")
    lines.append(f"Suggestions ignored: {summary['ignored']}")
    lines.append(f"Different tool used: {summary['different_tool']}")
    lines.append(f"No subsequent call: {summary['no_subsequent_call']}")
    lines.append("")

    # Ignored patterns
    ignored = summary["ignored_patterns"]
    if ignored:
        lines.append("Ignored suggestions (potential user preferences):")
        for pattern, count in sorted(ignored.items(), key=lambda x: -x[1]):
            lines.append(f"  \"{pattern}\" ({count}x)")
        lines.append("")

    # Sample suggestions
    suggestions = result["suggestions"]
    if suggestions:
        lines.append("Recent suggestions:")
        for s in suggestions[-5:]:
            outcome_symbol = {
                "followed": "✓",
                "ignored": "✗",
                "different_tool": "~",
                "no_subsequent_call": "?",
            }.get(s["outcome"], "?")

            text = s["match_text"][:60]
            if len(s["match_text"]) > 60:
                text += "..."
            lines.append(f"  {outcome_symbol} {text}")
            if s["next_tool"]:
                lines.append(f"    → Used: {s['next_tool']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze tool-routing suggestions and outcomes.",
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
        result = analyze_routing(jsonl_file)

        if args.json:
            print(json.dumps(result))
        else:
            if len(jsonl_files) > 1:
                print(f"\n=== {jsonl_file} ===\n")
            print(format_analysis(result))
            print()


if __name__ == "__main__":
    main()

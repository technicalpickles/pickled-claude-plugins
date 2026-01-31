#!/usr/bin/env python3
"""Identify patterns that suggest new skills or hooks.

Detects:
- Repeated failure patterns (same error type multiple times)
- Manual workarounds (user repeatedly giving same instruction)
- Unused tool suggestions (suggestions made but not followed)
- Directory confusion (commands run in wrong directory)
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


def extract_tool_calls_with_results(entries: list[dict]) -> list[dict]:
    """Extract tool calls paired with their results."""
    # First pass: collect tool calls
    tool_calls = {}
    for entry in entries:
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            continue

        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_calls[item.get("id")] = {
                    "uuid": entry.get("uuid"),
                    "name": item.get("name", "unknown"),
                    "input": item.get("input", {}),
                    "result": None,
                    "is_error": False,
                }

    # Second pass: match results
    for entry in entries:
        message = entry.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            continue

        for item in content:
            if isinstance(item, dict) and item.get("tool_use_id"):
                tool_id = item.get("tool_use_id")
                if tool_id in tool_calls:
                    tool_calls[tool_id]["result"] = item.get("content", "")
                    tool_calls[tool_id]["is_error"] = item.get("is_error", False)

    return list(tool_calls.values())


def extract_user_messages(entries: list[dict]) -> list[str]:
    """Extract user message content."""
    messages = []

    for entry in entries:
        message = entry.get("message", {})
        if message.get("role") != "user":
            continue

        content = message.get("content", [])
        if isinstance(content, str):
            messages.append(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    messages.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    messages.append(item.get("text", ""))

    return messages


def find_repeated_failures(tool_calls: list[dict]) -> list[dict]:
    """Find patterns of repeated failures."""
    failure_patterns = defaultdict(list)

    for call in tool_calls:
        if not call["is_error"]:
            continue

        result = call["result"] or ""

        # Normalize error message for grouping
        # Remove specific paths, numbers, etc.
        normalized = re.sub(r"/[\w/.-]+", "<path>", result)
        normalized = re.sub(r"\d+", "<n>", normalized)
        normalized = normalized[:150]  # Truncate for grouping

        key = (call["name"], normalized)
        failure_patterns[key].append(call)

    candidates = []
    for (tool_name, error_pattern), calls in failure_patterns.items():
        if len(calls) >= 2:
            candidates.append({
                "type": "repeated_failure",
                "confidence": "high" if len(calls) >= 3 else "medium",
                "tool": tool_name,
                "pattern": error_pattern,
                "count": len(calls),
                "suggestion": f"Hook to prevent {tool_name} failures matching this pattern",
                "examples": [c["result"][:100] for c in calls[:3]],
            })

    return sorted(candidates, key=lambda x: x["count"], reverse=True)


def find_directory_confusion(tool_calls: list[dict]) -> list[dict]:
    """Find cases where commands were run in wrong directory."""
    candidates = []

    # Look for Bash calls with directory-related errors
    dir_error_patterns = [
        r"no such file or directory",
        r"not found",
        r"does not exist",
        r"cannot find",
        r"ENOENT",
    ]

    dir_errors = defaultdict(list)

    for call in tool_calls:
        if call["name"] != "Bash" or not call["is_error"]:
            continue

        result = (call["result"] or "").lower()
        for pattern in dir_error_patterns:
            if re.search(pattern, result, re.IGNORECASE):
                # Extract command for grouping
                command = call["input"].get("command", "")[:50]
                dir_errors[command].append(call)
                break

    for command, calls in dir_errors.items():
        if len(calls) >= 2:
            candidates.append({
                "type": "directory_confusion",
                "confidence": "high" if len(calls) >= 3 else "medium",
                "command_prefix": command,
                "count": len(calls),
                "suggestion": "Hook to validate working directory before Bash commands",
            })

    return candidates


def find_repeated_instructions(user_messages: list[str]) -> list[dict]:
    """Find cases where user gave similar instructions repeatedly."""
    candidates = []

    # Normalize messages for comparison
    normalized_messages = []
    for msg in user_messages:
        # Lowercase, remove punctuation, collapse whitespace
        normalized = re.sub(r"[^\w\s]", "", msg.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if len(normalized) > 10:  # Skip very short messages
            normalized_messages.append((normalized[:100], msg))

    # Group similar messages
    message_groups = defaultdict(list)
    for normalized, original in normalized_messages:
        # Use first few words as key
        key = " ".join(normalized.split()[:5])
        message_groups[key].append(original)

    for key, messages in message_groups.items():
        if len(messages) >= 2:
            candidates.append({
                "type": "repeated_instruction",
                "confidence": "medium" if len(messages) >= 3 else "low",
                "pattern": key,
                "count": len(messages),
                "suggestion": "Skill to automate this repeated instruction",
                "examples": messages[:3],
            })

    return sorted(candidates, key=lambda x: x["count"], reverse=True)[:5]


def find_tool_misuse(tool_calls: list[dict]) -> list[dict]:
    """Find patterns suggesting wrong tool was used."""
    candidates = []

    # Look for Bash calls that could have used native tools
    bash_patterns = {
        r"\bcat\s+": ("Read", "Use Read tool instead of cat"),
        r"\bhead\s+": ("Read", "Use Read tool with limit instead of head"),
        r"\btail\s+": ("Read", "Use Read tool with offset instead of tail"),
        r"\bgrep\s+": ("Grep", "Use Grep tool instead of grep/rg"),
        r"\brg\s+": ("Grep", "Use Grep tool instead of rg"),
        r"\bfind\s+": ("Glob", "Use Glob tool instead of find"),
        r"\bls\s+.*\*": ("Glob", "Use Glob tool instead of ls with wildcards"),
    }

    misuse_counts = defaultdict(int)

    for call in tool_calls:
        if call["name"] != "Bash":
            continue

        command = call["input"].get("command", "")
        for pattern, (better_tool, suggestion) in bash_patterns.items():
            if re.search(pattern, command):
                misuse_counts[(pattern, better_tool, suggestion)] += 1

    for (pattern, better_tool, suggestion), count in misuse_counts.items():
        if count >= 2:
            candidates.append({
                "type": "tool_misuse",
                "confidence": "medium",
                "pattern": pattern,
                "better_tool": better_tool,
                "count": count,
                "suggestion": suggestion,
            })

    return sorted(candidates, key=lambda x: x["count"], reverse=True)


def identify_skills(jsonl_path: Path) -> dict:
    """Identify skill/hook opportunities in a session."""
    entries = parse_session(jsonl_path)
    tool_calls = extract_tool_calls_with_results(entries)
    user_messages = extract_user_messages(entries)

    candidates = []
    candidates.extend(find_repeated_failures(tool_calls))
    candidates.extend(find_directory_confusion(tool_calls))
    candidates.extend(find_repeated_instructions(user_messages))
    candidates.extend(find_tool_misuse(tool_calls))

    # Sort by confidence and count
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda x: (confidence_order.get(x.get("confidence", "low"), 3), -x.get("count", 0)))

    return {
        "file_path": str(jsonl_path.resolve()),
        "entry_count": len(entries),
        "tool_call_count": len(tool_calls),
        "candidates": candidates,
    }


def format_candidates(result: dict) -> str:
    """Format skill candidates for human-readable output."""
    lines = ["━━━ Skill Candidates ━━━"]

    candidates = result["candidates"]

    if not candidates:
        lines.append("No skill/hook opportunities identified.")
        return "\n".join(lines)

    lines.append(f"Found {len(candidates)} potential improvement(s):")
    lines.append("")

    for candidate in candidates:
        confidence = candidate.get("confidence", "low").upper()
        ctype = candidate.get("type", "unknown")
        count = candidate.get("count", 0)

        lines.append(f"[{confidence}] {ctype} ({count}x)")

        if candidate.get("tool"):
            lines.append(f"  Tool: {candidate['tool']}")
        if candidate.get("pattern"):
            pattern = str(candidate["pattern"])[:60]
            lines.append(f"  Pattern: {pattern}")
        if candidate.get("suggestion"):
            lines.append(f"  → {candidate['suggestion']}")
        if candidate.get("examples"):
            lines.append("  Examples:")
            for ex in candidate["examples"][:2]:
                ex_preview = str(ex)[:70].replace("\n", " ")
                if len(str(ex)) > 70:
                    ex_preview += "..."
                lines.append(f"    - {ex_preview}")

        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Identify patterns that suggest new skills or hooks.",
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

    all_candidates = []

    for jsonl_file in jsonl_files:
        result = identify_skills(jsonl_file)
        all_candidates.extend(result["candidates"])

        if args.json:
            print(json.dumps(result))
        else:
            if len(jsonl_files) > 1:
                print(f"\n=== {jsonl_file} ===\n")
            print(format_candidates(result))
            print()

    # If multiple files, show aggregate summary
    if len(jsonl_files) > 1 and not args.json:
        print("━━━ Aggregate Summary ━━━")
        print(f"Analyzed {len(jsonl_files)} session(s)")
        print(f"Total candidates: {len(all_candidates)}")

        # Group by type
        by_type = defaultdict(int)
        for c in all_candidates:
            by_type[c.get("type", "unknown")] += 1

        if by_type:
            print("\nBy type:")
            for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
                print(f"  {t}: {count}")


if __name__ == "__main__":
    main()

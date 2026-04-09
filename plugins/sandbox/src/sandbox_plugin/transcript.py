"""Read Claude Code transcript JSONL and find recent sandboxed Bash failures."""

import json


def find_recent_sandboxed_failure(transcript_path: str, lookback: int = 10) -> bool:
    """Check if there's a recent sandboxed Bash failure in the transcript.

    Reads the last `lookback` entries and looks for a Bash tool_use
    without dangerouslyDisableSandbox followed by an error tool_result.
    """
    entries = _read_tail(transcript_path, lookback)

    for i in range(len(entries) - 1, -1, -1):
        if _is_sandboxed_bash_failure(entries, i):
            return True

    return False


def _read_tail(path: str, n: int) -> list[dict]:
    """Read the last n lines of a JSONL file, skipping malformed lines."""
    entries = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return []

    return entries[-n:] if len(entries) > n else entries


def _is_sandboxed_bash_failure(entries: list[dict], index: int) -> bool:
    """Check if entry at index is a tool error following a sandboxed Bash call."""
    entry = entries[index]
    msg = entry.get("message", {})
    if msg.get("role") != "tool":
        return False

    content = msg.get("content", [])
    if not isinstance(content, list):
        return False

    is_error = any(
        isinstance(block, dict) and block.get("is_error")
        for block in content
    )
    if not is_error:
        return False

    # Look backwards for the preceding Bash tool_use (sandboxed)
    for j in range(index - 1, -1, -1):
        prev = entries[j]
        prev_msg = prev.get("message", {})
        if prev_msg.get("role") != "assistant":
            continue
        prev_content = prev_msg.get("content", [])
        if not isinstance(prev_content, list):
            continue
        for block in prev_content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                tool_input = block.get("input", {})
                if tool_input.get("dangerouslyDisableSandbox"):
                    return False  # Was unsandboxed, doesn't count
                return True
        break  # Only check the immediately preceding assistant message

    return False

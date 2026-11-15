#!/usr/bin/env python3
"""
PreToolUse:WebFetch hook, declared in the capture skill's frontmatter (not the
plugin's own hooks/hooks.json). Skill-scoped hooks register when the skill
loads and stay registered for the rest of the session, so this also applies
to WebFetch calls made after a capture finishes.

WebFetch is a summarizer, not a fetcher: it paraphrases, invents details, and
silently truncates long pages. When the lightpanda CLI is on PATH, this denies
WebFetch for a host until a lightpanda fetch of that host has been tried and
failed, then lets WebFetch through as the fallback.

Reads the session transcript to find the most recent `lightpanda` Bash call
for the same host (lowercased, leading `www.` stripped):
  - none, or it succeeded  -> deny, suggest lightpanda
  - still running in the background -> deny, say to wait for it
  - failed (is_error, or under 200 chars of output) -> allow

Fails open: malformed stdin or an unreadable transcript allows the call, so a
broken hook never blocks real work.
"""
import json
import re
import shutil
import sys
from urllib.parse import urlparse

MIN_USEFUL_CHARS = 200
URL_RE = re.compile(r"https?://[^\s'\"]+")

TRY_FIRST = (
    "Try lightpanda before WebFetch: lightpanda fetch --dump markdown {url} "
    "(add the host to allowed_domains). If that fails, WebFetch is allowed - "
    "mark the note fetched-via: webfetch."
)
WAIT = (
    "A lightpanda fetch for this host is still running in the background. "
    "Wait for it to finish instead of falling back to WebFetch."
)


def host_of(url):
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def result_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return ""


def message_items(entry):
    content = (entry.get("message") or {}).get("content")
    return content if isinstance(content, list) else []


def latest_attempt(transcript_path, host):
    """Return the tool_result for the most recent lightpanda call on host, or
    {} if there was a call with no result yet, or None if there was no call."""
    attempts = []  # tool_use ids, in order
    results = {}
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            for item in message_items(entry):
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "tool_use" and item.get("name") == "Bash":
                    command = (item.get("input") or {}).get("command", "")
                    if "lightpanda" in command and any(
                        host_of(u) == host for u in URL_RE.findall(command)
                    ):
                        attempts.append(item.get("id"))
                elif item.get("type") == "tool_result":
                    results[item.get("tool_use_id")] = item
    if not attempts:
        return None
    return results.get(attempts[-1], {})


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    url = (payload.get("tool_input") or {}).get("url", "")
    if not url or shutil.which("lightpanda") is None:
        sys.exit(0)

    try:
        result = latest_attempt(payload.get("transcript_path", ""), host_of(url))
    except OSError:
        sys.exit(0)

    if result is None:
        deny(TRY_FIRST.format(url=url))

    text = result_text(result.get("content")).strip()
    if "running in background" in text:
        deny(WAIT)
    if result.get("is_error") or len(text) < MIN_USEFUL_CHARS:
        sys.exit(0)
    deny(TRY_FIRST.format(url=url))


if __name__ == "__main__":
    main()

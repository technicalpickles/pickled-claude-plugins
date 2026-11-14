#!/usr/bin/env python3
"""
PostToolUse and PostToolUseFailure hook on WebFetch, registered plugin-wide in
hooks/hooks.json so it also fires in research subagents that never load a
second-brain skill. That is where WebFetch failures cost the most: an agent
with only WebFetch hits a 403 or a bot-check page and marks the source
unverified, when a real browser would have read it.

When WebFetch didn't get the page, this adds context naming the other ways to
read it. It never blocks.

Probed on Claude Code 2.1 (2026-11-14): a 403 arrives as PostToolUse with
`tool_response.code` 403 and no body; a DNS failure arrives as
PostToolUseFailure with an `error` string. A bot-check page arrives as a
normal 200.

Fails open: malformed stdin, or a payload this doesn't recognize, prints
nothing.
"""
import json
import re
import sys

BOT_CHECK_MAX_CHARS = 5000
BOT_CHECK_RE = re.compile(
    r"just a moment|attention required|verify you are human|are you a robot|"
    r"captcha|enable javascript and cookies|access denied|unusual traffic",
    re.IGNORECASE,
)
BLOCKED_ERROR_RE = re.compile(
    r"\b(401|403|429|451)\b|forbidden|too many requests|timed? ?out|econnreset",
    re.IGNORECASE,
)
CONTENT_RE = re.compile(r"<fetched-web-content>(.*?)(?:</fetched-web-content>|$)", re.DOTALL)

LADDER = (
    "WebFetch didn't get {url} ({why}). Don't mark the source unverified or move on "
    "yet. Try, in order, whichever of these you have:\n"
    "1. `lightpanda fetch --dump markdown <url>` via Bash.\n"
    "2. Claude in Chrome (a real browser with the user's sign-ins), or the built-in "
    "browser pane.\n"
    "3. For a paywalled post (Medium and the like), the author's own site or a mirror.\n"
    "4. For a PDF that comes back as a bot-check page, open it in a browser and read "
    "the text layer (pdf.js).\n"
    "5. Secondary sources (recaps, show notes, talks), labeled as secondary.\n"
    "If you have none of these, say which fetch failed and why, so the caller can "
    "retry with a browser."
)


def why_post_tool_use(response):
    code = response.get("code")
    if isinstance(code, int) and code >= 400:
        return f"HTTP {code}"
    if response.get("bytes") == 0:
        return "the page came back empty"
    result = response.get("result")
    if not isinstance(result, str):
        return None
    match = CONTENT_RE.search(result)
    body = (match.group(1) if match else result).strip()
    if len(body) < BOT_CHECK_MAX_CHARS and BOT_CHECK_RE.search(body):
        return "it looks like a bot-check page"
    return None


def why_failure(error):
    if isinstance(error, str) and BLOCKED_ERROR_RE.search(error):
        return error.strip()[:120]
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    event = payload.get("hook_event_name")
    if event == "PostToolUse":
        response = payload.get("tool_response")
        why = why_post_tool_use(response) if isinstance(response, dict) else None
    elif event == "PostToolUseFailure":
        why = why_failure(payload.get("error"))
    else:
        return
    if not why:
        return
    url = (payload.get("tool_input") or {}).get("url", "this page")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": LADDER.format(url=url, why=why),
        }
    }))


if __name__ == "__main__":
    main()

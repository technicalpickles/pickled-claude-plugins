"""Em-dash detection and tool/command gating for outbound content.

The rule: block an em-dash (U+2014) only when it appears in a send-time call
for a tool the config opts in (Slack sends, gh PR/issue authoring). Everything
else, including arbitrary Bash and the Write/Edit tools, is left alone so
docs/code and my own cleanup commands never get blocked.
"""

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from writing_tools.config import Config

EMDASH = "—"  # —

BLOCK_MESSAGE = (
    "Em-dash (—) in outbound-as-you content. Rewrite it before sending: "
    "use a comma, colon, parentheses, or split into two sentences."
)

# gh flags that point at a file whose contents become the outbound body.
_BODY_FILE_FLAGS = ("--body-file", "-F")


@dataclass
class CheckResult:
    """Result of checking a tool call."""

    blocked: bool
    reason: Optional[str] = None


def _serialize(tool_input: dict) -> str:
    """Serialize tool_input for scanning.

    ``ensure_ascii=False`` is required so an em-dash stays as the literal
    character rather than being escaped to ``\\u2014``.
    """
    try:
        return json.dumps(tool_input, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(tool_input)


def _matches_bash_prefix(command: str, prefixes: list[str]) -> bool:
    """True if the command starts with a configured prefix at a command boundary.

    Matches at the start of the string or right after a shell separator
    (``;`` ``&&`` ``||`` ``|``), so ``gh pr create ...`` matches but
    ``grep "gh pr create" foo`` (the prefix quoted inside an argument) does not.
    """
    for prefix in prefixes:
        pattern = r"(?:^|[;&|]\s*)" + re.escape(prefix)
        if re.search(pattern, command):
            return True
    return False


def _body_file_paths(command: str) -> list[str]:
    """Extract file paths referenced by gh's --body-file/-F flags."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return []

    paths: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # --body-file=path or -F=path
        matched_inline = False
        for flag in _BODY_FILE_FLAGS:
            if token.startswith(flag + "="):
                paths.append(token[len(flag) + 1 :])
                matched_inline = True
                break
        if matched_inline:
            i += 1
            continue
        # --body-file path or -F path
        if token in _BODY_FILE_FLAGS and i + 1 < len(tokens):
            paths.append(tokens[i + 1])
            i += 2
            continue
        i += 1
    return paths


def _body_file_has_emdash(command: str) -> bool:
    for path in _body_file_paths(command):
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if EMDASH in content:
            return True
    return False


def check_tool_call(tool_call: dict, load_config: Callable[[], Config]) -> CheckResult:
    """Check a PreToolUse tool call for outbound em-dashes.

    ``load_config`` is a zero-arg callable returning a :class:`Config`. It's
    passed lazily so the config is only loaded when there's actually something
    to check (the common no-em-dash case stays cheap).
    """
    tool_name = tool_call.get("tool_name", "")
    tool_input = tool_call.get("tool_input", {}) or {}

    serialized = _serialize(tool_input)
    command = tool_input.get("command", "") if tool_name == "Bash" else ""
    has_body_file = bool(command) and any(f in command for f in _BODY_FILE_FLAGS)

    # Fast path: no em-dash in the direct input and no body-file to chase means
    # there is nothing to block. Skip loading the config entirely.
    if EMDASH not in serialized and not has_body_file:
        return CheckResult(blocked=False)

    config = load_config()
    if config.is_empty():
        # Inert: no tools opted in (e.g. a fresh installer). Never block.
        return CheckResult(blocked=False)

    if tool_name.startswith("mcp__"):
        if tool_name in config.mcp_tools and EMDASH in serialized:
            return CheckResult(blocked=True, reason=BLOCK_MESSAGE)
        return CheckResult(blocked=False)

    if tool_name == "Bash":
        if not _matches_bash_prefix(command, config.bash_commands):
            # Arbitrary bash (incl. my own grep/perl em-dash cleanup): allow.
            return CheckResult(blocked=False)
        if EMDASH in command or _body_file_has_emdash(command):
            return CheckResult(blocked=True, reason=BLOCK_MESSAGE)
        return CheckResult(blocked=False)

    # Any other tool (Write, Edit, unmonitored MCP tools): leave it alone.
    return CheckResult(blocked=False)

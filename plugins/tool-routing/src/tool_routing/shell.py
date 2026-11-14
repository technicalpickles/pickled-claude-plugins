"""Reduce a shell command to the text the shell would run as commands.

Bash routes match against this instead of the raw command, so a tool named
inside a heredoc body, a quoted string or a commit message is not mistaken
for a call to that tool.
"""

from __future__ import annotations

_WORD_END = " \t\n;&|<>()"


def strip_literals(command: str) -> str:
    """Drop heredoc bodies and empty every quoted string.

    Quotes stay as `''` or `""` so a route can still see that an argument was
    there. A heredoc keeps its `<<` and delimiter; only the body lines and the
    closing delimiter line go. Command substitutions inside double quotes are
    part of the string and go with it. Unterminated quotes run to the end.
    """
    text, _ = _scan(command, 0, closer=None)
    return text


def _scan(s: str, i: int, closer: str | None) -> tuple[str, int]:
    """Copy unquoted shell text from s[i:] until closer (or the end).

    Returns the stripped text and the index just past closer.
    """
    out: list[str] = []
    heredocs: list[tuple[str, bool]] = []
    depth = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == closer and depth == 0:
            return "".join(out), i + 1
        if c == "\\":
            out.append(s[i : i + 2])
            i += 2
        elif c == "'" or s.startswith("$'", i):
            if c == "$":
                out.append("$")
                i += 1
            out.append("''")
            i = _skip_single(s, i + 1, escapes=c == "$")
        elif c == '"':
            out.append('""')
            i = _skip_double(s, i + 1)
        elif s.startswith("$(", i):
            inner, i = _scan(s, i + 2, ")")
            out.append("$(" + inner + ")")
        elif c == "`":
            inner, i = _scan(s, i + 1, "`")
            out.append("`" + inner + "`")
        elif s.startswith("<<<", i):
            out.append("<<<")
            i += 3
        elif s.startswith("<<", i):
            i = _read_heredoc_op(s, i, out, heredocs)
        elif c == "\n":
            out.append(c)
            i = _skip_heredoc_bodies(s, i + 1, heredocs)
            heredocs = []
        else:
            if closer == ")":
                depth += {"(": 1, ")": -1}.get(c, 0)
            out.append(c)
            i += 1
    return "".join(out), i


def _skip_single(s: str, i: int, escapes: bool) -> int:
    while i < len(s):
        if escapes and s[i] == "\\":
            i += 2
        elif s[i] == "'":
            return i + 1
        else:
            i += 1
    return i


def _skip_double(s: str, i: int) -> int:
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
        elif c == '"':
            return i + 1
        elif s.startswith("$(", i):
            _, i = _scan(s, i + 2, ")")
        elif c == "`":
            _, i = _scan(s, i + 1, "`")
        else:
            i += 1
    return i


def _read_heredoc_op(s: str, i: int, out: list[str], heredocs: list[tuple[str, bool]]) -> int:
    """Copy `<<[-] WORD` to out and queue its body for skipping."""
    start = i
    i += 2
    strip_tabs = i < len(s) and s[i] == "-"
    if strip_tabs:
        i += 1
    while i < len(s) and s[i] in " \t":
        i += 1
    word_start = i
    quote = None
    while i < len(s):
        c = s[i]
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c in _WORD_END:
            break
        i += 1
    word = s[word_start:i]
    delimiter = word.replace("'", "").replace('"', "").replace("\\", "")
    if delimiter:
        heredocs.append((delimiter, strip_tabs))
    out.append(s[start:i])
    return i


def _skip_heredoc_bodies(s: str, i: int, heredocs: list[tuple[str, bool]]) -> int:
    """Skip each queued heredoc's body lines and closing line, starting at s[i]."""
    for delimiter, strip_tabs in heredocs:
        while i < len(s):
            end = s.find("\n", i)
            line = s[i:] if end == -1 else s[i:end]
            i = len(s) if end == -1 else end + 1
            if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                break
    return i

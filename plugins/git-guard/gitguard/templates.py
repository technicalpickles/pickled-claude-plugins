"""Installer templates: the config keys and hook scripts that legitimate installers write.

Pure module: no IO. These templates are an allowlist, so too loose is a bypass and too tight is only
a revert the human can `accept`. Every regex is applied with `re.fullmatch`, so it has to account for
the whole value or file. A hook body regex fixes every line and leaves a slot only where an installer
varies (a message, a binary path), and a slot's character class never admits `"`, `$`, a backtick, a
backslash or a newline, the characters that would let text escape its double quotes.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Optional

from gitguard.model import ConfigEntry, FileAtom, Surface


@dataclass(frozen=True)
class HookTemplate:
    """A hook script an installer writes.

    name: the template name reported to the caller.
    hook_names: the hook files this template may appear as.
    body_regex: applied with fullmatch to the decoded file. A named group `n`, if present, must equal
        the file's own hook name. A named group `bin`, if present, is the slot a notice reports.
    notice: True when a pass should still be mentioned to the user.
    """

    name: str
    hook_names: tuple[str, ...]
    body_regex: re.Pattern[str]
    notice: bool


@dataclass(frozen=True)
class Templates:
    """lfs filter values and hk command shape (config), plus hook templates and exact lfs hook hashes."""

    lfs_filter: frozenset[tuple[str, str]]  # (variable, value) for the `lfs` filter driver
    hk_command: re.Pattern[str]  # group `e` is the event name
    hooks: tuple[HookTemplate, ...]
    hook_sha256: frozenset[tuple[str, str]]  # (hook name, sha256) of known lfs hook scripts


# -- config: lfs filter, hk --------------------------------------------------------------------

_LFS_FILTER = frozenset(
    {
        ("clean", "git-lfs clean -- %f"),
        ("smudge", "git-lfs smudge -- %f"),
        ("process", "git-lfs filter-process"),
        ("required", "true"),
    }
)

_EVENT = r"[a-z-]+"
_HK_COMMAND = re.compile(r'test "\$\{HK:-1\}" = "0" \|\| hk run (?P<e>' + _EVENT + r") --from-hook")
_EVENT_RE = re.compile(_EVENT)

# -- hooks: lfs --------------------------------------------------------------------------------

_LFS_HOOKS = ("post-checkout", "post-commit", "post-merge", "pre-push")

_LFS_SHA256 = {
    "post-checkout": (
        "8d606e58cce98604696a4abcf3ae1ebde6f9f31ac72bb0d44e2444cc39f26030",
        "791471b4ff472aab844a4fceaa48bbb0a12193616f971e8e940625498b4938a6",
    ),
    "post-commit": (
        "f3eb4d1f62924c09d481a0563a84b158c66eb2feb3431cfdb3e6760aab4d661d",
        "21e961572bb3f43a5f2fbafc1cc764d86046cc2e5f0bbecebfe9684a0b73b664",
    ),
    "post-merge": (
        "cecb594e8fa65831654fc95e96db9f1249e09c52810c6fbb2b428280aac22158",
        "75da0da66a803b4b030ad50801ba57062c6196105eb1d2251590d100edb9390b",
    ),
    "pre-push": (
        "a52d0510d0f8c75e27852156ec6f7791f0d8ed65fc58fcc368dd1de0a60a1d74",
        "df5417b2daa3aa144c19681d1e997df7ebfe144fb7e3e05138bd80ae998008e4",
    ),
}

# A message: no `"`, `$`, backtick, backslash, CR or LF, except the two-character `\n` that echo and
# printf turn into a newline. Nothing in it can end the string or start a substitution.
_MSG = r'(?:[^"$`\\\r\n\x00]|\\n)*'
_LFS_BODY = re.compile(
    r"#!/bin/sh\n"
    r"command -v git-lfs >/dev/null 2>&1 \|\| \{ "
    r'(?:echo >&2 "' + _MSG + r'"|printf >&2 "\\n%s\\n\\n" "' + _MSG + r'"); exit 2; \}\n'
    r'git lfs (?P<n>[a-z-]+) "\$@"\n'
)

# -- hooks: portool ----------------------------------------------------------------------------

# Slot: an absolute path ending in /portool, without `"`, `$`, backtick, backslash, CR or LF.
_PORTOOL_BIN = r'(?P<bin>/(?:[^"$`\\\r\n\x00]*/)?portool)'
_PORTOOL_LINES = (
    "#!/bin/sh",
    "# installed by portool",
    "\0",  # the PORTOOL_BIN="..." line
    'if ! [ -x "$PORTOOL_BIN" ]; then PORTOOL_BIN=portool; fi',
    'if command -v "$PORTOOL_BIN" >/dev/null 2>&1; then',
    "  \"$PORTOOL_BIN\" sync --quiet || echo 'portool: sync failed; Git was not blocked' >&2",
    "fi",
    "exit 0",
)
_PORTOOL_BODY = re.compile(
    "".join(
        ('PORTOOL_BIN="' + _PORTOOL_BIN + '"' if line == "\0" else re.escape(line)) + "\n"
        for line in _PORTOOL_LINES
    )
)

_LFS = HookTemplate("lfs", _LFS_HOOKS, _LFS_BODY, notice=False)
_PORTOOL = HookTemplate("portool", ("post-checkout", "post-merge"), _PORTOOL_BODY, notice=True)

DEFAULT_TEMPLATES = Templates(
    lfs_filter=_LFS_FILTER,
    hk_command=_HK_COMMAND,
    hooks=(_LFS, _PORTOOL),
    hook_sha256=frozenset((name, sha) for name, shas in _LFS_SHA256.items() for sha in shas),
)


# -- config matching ---------------------------------------------------------------------------


def _is_hk_command(command: str, event: str, templates: Templates) -> bool:
    """`command` is hk's own command line for `event`."""
    found = templates.hk_command.fullmatch(command)
    return found is not None and found["e"] == event


def _hk_match(entry: ConfigEntry, surface: Surface, templates: Templates) -> bool:
    """`hook.hk-<E>.command` and `.event` pass as a pair, within one file.

    A command passes when it is hk's command for E and the file has an event entry E. An event passes
    when it is E and EVERY command entry for that hook in the file is hk's command for E, so an extra
    command planted beside a real one cannot ride on the event."""
    key = entry.key
    if key.section != "hook" or key.subsection is None or not key.subsection.startswith("hk-"):
        return False
    event = key.subsection[len("hk-"):]
    if _EVENT_RE.fullmatch(event) is None:
        return False
    peers = [e for e in surface.entries if e.file == entry.file and e.key.section == "hook"
             and e.key.subsection == key.subsection]
    commands = [e.value for e in peers if e.key.variable == "command"]
    events = [e.value for e in peers if e.key.variable == "event"]
    if key.variable == "command":
        return _is_hk_command(entry.value, event, templates) and event in events
    if key.variable == "event":
        return entry.value == event and bool(commands) and all(
            _is_hk_command(c, event, templates) for c in commands
        )
    return False


def config_template_match(entry: ConfigEntry, surface: Surface, templates: Templates) -> Optional[str]:
    """The name of the installer template `entry` matches, or None."""
    key = entry.key
    if key.section == "filter" and key.subsection == "lfs":
        return "lfs-filter" if (key.variable, entry.value) in templates.lfs_filter else None
    if key.section == "hook" and _hk_match(entry, surface, templates):
        return "hk"
    return None


# -- hook matching -----------------------------------------------------------------------------


def hook_template_match(atom: FileAtom, templates: Templates) -> Optional[HookTemplate]:
    """The installer template a hook file matches, or None. Only regular files can match: a symlink
    runs whatever its target holds at fire time, however its target bytes look today."""
    if atom.role != "hook" or atom.kind != "file":
        return None
    name = atom.path.name
    digest = atom.sha256
    if atom.content is not None:
        digest = hashlib.sha256(atom.content).hexdigest()
        if atom.sha256 is not None and atom.sha256 != digest:
            return None
    if digest is not None and (name, digest) in templates.hook_sha256:
        return next((t for t in templates.hooks if t.name == "lfs"), None)
    if atom.content is None:
        return None
    try:
        text = atom.content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    for template in templates.hooks:
        if name not in template.hook_names:
            continue
        found = template.body_regex.fullmatch(text)
        if found is None:
            continue
        if "n" in template.body_regex.groupindex and found["n"] != name:
            continue
        return template
    return None


def hook_notice_slot(atom: FileAtom, template: HookTemplate) -> Optional[str]:
    """The slot value a notice template reports for `atom` (portool: the binary path), or None when
    the template has no such slot, the file has no content, or the content does not match."""
    if atom.content is None or "bin" not in template.body_regex.groupindex:
        return None
    try:
        text = atom.content.decode("utf-8")
    except UnicodeDecodeError:
        return None
    found = template.body_regex.fullmatch(text)
    return found["bin"] if found is not None else None

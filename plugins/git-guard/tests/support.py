"""Shared test builders. Test code, so it may read fixtures from disk."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional

from gitguard.model import (
    Anchor,
    ConfigEntry,
    ConfigKey,
    FileAtom,
    Fingerprint,
    MemberRef,
    Surface,
    Trigger,
    TriggerKind,
)

FIXTURES = Path(__file__).parent / "fixtures"

ANCHOR = Anchor(PurePosixPath("/r/a"))
COMMON = MemberRef(PurePosixPath("/r/a/.git"), "common")

# Where each link role lives relative to the common git dir (gitfile lives at the anchor's `.git`).
_LINK_PATHS = {
    "hooks-dir": "/r/a/.git/hooks",
    "guard-state": "/r/a/.git/guard-state",
    "gitfile": "/r/a/.git",
    "commondir": "/r/a/.git/commondir",
    "admin-gitdir": "/r/a/.git/gitdir",
    "alternates": "/r/a/.git/objects/info/alternates",
    "attributes": "/r/a/.git/info/attributes",
}


def entry(
    dotted: str,
    value: str,
    *,
    file: str = "/r/a/.git/config",
    member: MemberRef = COMMON,
    scope: str = "local",
) -> ConfigEntry:
    return ConfigEntry(member, PurePosixPath(file), scope, ConfigKey.parse(dotted), value)


def _atom(
    role: str,
    path: PurePosixPath,
    content: Optional[bytes],
    *,
    kind: str,
    executable: bool,
    member: Optional[MemberRef],
) -> FileAtom:
    digest = hashlib.sha256(content).hexdigest() if content is not None else None
    return FileAtom(member, path, role, kind, digest, executable, content)


def hook(
    name: str,
    content: bytes,
    *,
    kind: str = "file",
    executable: bool = True,
    member: MemberRef = COMMON,
) -> FileAtom:
    path = member.git_dir / "hooks" / name
    return _atom("hook", path, content, kind=kind, executable=executable, member=member)


def link(
    role: str,
    content: Optional[bytes],
    *,
    path: Optional[str] = None,
    kind: Optional[str] = None,
    executable: bool = False,
) -> FileAtom:
    """A non-hook file atom. `content=None` means the file is absent. `kind` overrides the default
    ("absent" without content, else "file"); every role has a default path."""
    where = PurePosixPath(path if path is not None else _LINK_PATHS[role])
    member = None if role == "gitfile" else COMMON
    if kind is None:
        kind = "absent" if content is None else "file"
    return _atom(role, where, content, kind=kind, executable=executable, member=member)


def surface(
    entries: Iterable[ConfigEntry] = (),
    files: Iterable[FileAtom] = (),
    *,
    toplevels: Iterable[str] = ("/r/a",),
    tracked_dirs: Iterable[str] = (),
    home: str = "/home/u",
    anchor: Anchor = ANCHOR,
    common_dir: str = "/r/a/.git",
) -> Surface:
    entries, files = tuple(entries), tuple(files)
    common = PurePosixPath(common_dir)
    members: list[MemberRef] = [MemberRef(common, "common")]
    for m in [e.member for e in entries] + [f.member for f in files]:
        if m is not None and m not in members:
            members.append(m)
    return Surface(
        anchor=anchor,
        common_dir=common,
        toplevels=tuple(PurePosixPath(t) for t in toplevels),
        members=tuple(members),
        entries=entries,
        files=files,
        fingerprint=Fingerprint.EMPTY,
        tracked_dirs=frozenset(PurePosixPath(d) for d in tracked_dirs),
        home=PurePosixPath(home),
    )


def trigger(
    kind: TriggerKind = TriggerKind.POST_TOOL,
    *,
    may_revert: bool = True,
    may_block: bool = False,
    first_sight: bool = False,
) -> Trigger:
    return Trigger(kind, "s-test", may_revert, may_block, first_sight)


_ROW = re.compile(r"^(?P<anchor>.+?)/\.git/(?P<rel>.+)$")
_WORKTREE = re.compile(r"^worktrees/(?P<name>[^/]+)/config\.worktree$")
_MODULE = re.compile(r"^modules/(?P<name>.+)/config$")


def _classify_rel(anchor: PurePosixPath, rel: str) -> tuple[MemberRef, str]:
    """Map a config path relative to `<anchor>/.git` to (member, scope)."""
    git = anchor / ".git"
    if m := _WORKTREE.match(rel):
        return MemberRef(git / "worktrees" / m["name"], "admin"), "worktree"
    if m := _MODULE.match(rel):
        return MemberRef(git / "modules" / m["name"], "module"), "module"
    if rel in ("config", "config.worktree"):
        return MemberRef(git, "common"), "worktree" if rel == "config.worktree" else "local"
    raise ValueError(f"unrecognised corpus config path: {rel}")


def corpus_surfaces() -> list[Surface]:
    """One Surface per anchor (`/home/u/src/repo-NN`) in corpus.tsv, in first-seen order."""
    tracked = [
        PurePosixPath(line)
        for line in (FIXTURES / "corpus_tracked_dirs.txt").read_text().splitlines()
        if line
    ]
    grouped: dict[PurePosixPath, list[ConfigEntry]] = {}
    for line in (FIXTURES / "corpus.tsv").read_text().splitlines():
        if not line:
            continue
        path, key, value = line.split("\t", 2)
        match = _ROW.match(path)
        anchor = PurePosixPath(match["anchor"])
        member, scope = _classify_rel(anchor, match["rel"])
        file = PurePosixPath(path)
        grouped.setdefault(anchor, []).append(
            ConfigEntry(member, file, scope, ConfigKey.parse(key), value)
        )
    surfaces = []
    for anchor, entries in grouped.items():
        s = surface(
            entries,
            toplevels=[str(anchor)],
            tracked_dirs=[str(d) for d in tracked if d.is_relative_to(anchor)],
            anchor=Anchor(anchor),
            common_dir=str(anchor / ".git"),
        )
        surfaces.append(s)
    return surfaces

"""Frozen data model for git-guard's verdict core. Data only, no logic beyond ConfigKey.

Pure module: no IO. Everything `judge()` needs is carried by these types.
`Row` and `Templates` live in later modules; they appear here only as type hints.
"""
from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, ClassVar, Literal, Mapping, Optional, Union

if TYPE_CHECKING:
    from gitguard.rules import Row
    from gitguard.templates import Templates


@dataclass(frozen=True)
class StatSig:
    """Fingerprint of one path. ctime_ns is the point: user space cannot set it, so `touch -r` can't forge it."""

    mtime_ns: int
    ctime_ns: int
    size: int
    ino: int


@dataclass(frozen=True)
class Fingerprint:
    """stat() of every path the probe read, listed, or looked for and found absent.
    Equal fingerprint => skip the git subprocesses."""

    sigs: Mapping[str, Optional[StatSig]]  # None = absent

    EMPTY: ClassVar[Fingerprint]

    def __hash__(self) -> int:
        # sigs is a Mapping (unhashable dict in practice); hash its items so a Surface stays hashable.
        return hash(frozenset(self.sigs.items()))


Fingerprint.EMPTY = Fingerprint(sigs={})


@dataclass(frozen=True)
class Anchor:
    """The realpath of the directory that CONTAINS the `.git` entry (toplevel). LKG link atoms are keyed by
    this, never by the resolved common dir: a commondir/gitfile redirect changes the resolved dir, and keying
    by it would turn the redirect into a trust-on-first-sight bootstrap of attacker content."""

    path: PurePosixPath


@dataclass(frozen=True)
class MemberRef:
    """One git dir the surface covers: the common dir, a linked worktree's admin dir, or a submodule gitdir."""

    git_dir: PurePosixPath
    role: Literal["common", "admin", "module"]


@dataclass(frozen=True, order=True)
class ConfigKey:
    """git's own normalisation: section and variable lowercased, subsection verbatim."""

    section: str
    subsection: Optional[str]
    variable: str

    @classmethod
    def parse(cls, dotted: str) -> ConfigKey:
        """`section[.subsection].variable`. The subsection is everything between the first and last dot,
        verbatim, so it may itself contain dots (`url.https://Evil/.insteadOf`)."""
        first = dotted.find(".")
        last = dotted.rfind(".")
        if first < 0:
            raise ValueError(f"config key needs a section and a variable: {dotted!r}")
        section = dotted[:first].lower()
        variable = dotted[last + 1 :].lower()
        subsection = dotted[first + 1 : last] if last > first else None
        return cls(section, subsection, variable)

    def dotted(self) -> str:
        if self.subsection is None:
            return f"{self.section}.{self.variable}"
        return f"{self.section}.{self.subsection}.{self.variable}"


@dataclass(frozen=True)
class ConfigEntry:
    member: MemberRef
    file: PurePosixPath  # the file git says it came from (--show-origin), absolute. include targets show up here.
    scope: Literal["local", "worktree", "module"]
    key: ConfigKey
    value: str


@dataclass(frozen=True)
class FileAtom:
    """A non-config control file: hook script, info/attributes, alternates, commondir, gitdir, the `.git` gitfile,
    or the guard's own state. Small ones keep content so a revert is exact. Large ones keep only a hash, so they
    can be quarantined but never auto-restored. For a symlink, `sha256` is the hash of its readlink target."""

    member: Optional[MemberRef]
    path: PurePosixPath
    role: Literal[
        "hook",
        "attributes",
        "alternates",
        "commondir",
        "admin-gitdir",
        "gitfile",
        "hooks-dir",
        "guard-state",
    ]
    kind: Literal["file", "dir", "symlink", "absent"]
    sha256: Optional[str]
    executable: bool
    content: Optional[bytes]  # <= 64 KiB, else None


Atom = Union[ConfigEntry, FileAtom]


def atom_key(atom: Atom) -> str:
    """Stable identity of an atom: where it is and what it is called, not what it holds.

    Fields are joined with NUL, which git allows in no path, key or value; any printable
    separator can appear inside a subsection or a value and make two atoms share a key."""
    if isinstance(atom, ConfigEntry):
        return "\0".join(("cfg", str(atom.member.git_dir), str(atom.file), atom.key.dotted(), atom.value))
    return f"file\0{atom.path}"


def atom_hash(atom: Atom) -> str:
    """What an `accept` grant pins. A config entry is its own key (the value is in it); a file also
    covers its content hash, kind and exec bit, so changing any of them needs a fresh grant."""
    key = atom_key(atom)
    if isinstance(atom, ConfigEntry):
        raw = key
    else:
        raw = f"{key}\0{atom.sha256 or ''}\0{atom.kind}\0{atom.executable}"
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class Surface:
    """Everything observable about one anchor's git control surface at one instant. Immutable, hashable."""

    anchor: Anchor
    common_dir: PurePosixPath
    toplevels: tuple[PurePosixPath, ...]  # every worktree of this repo, for hooksPath targets
    members: tuple[MemberRef, ...]
    entries: tuple[ConfigEntry, ...]
    files: tuple[FileAtom, ...]
    fingerprint: Fingerprint
    tracked_dirs: frozenset[PurePosixPath]  # absolute tracked hooks dirs, computed by probe
    home: PurePosixPath


# -- Verdict vocabulary -------------------------------------------------------


class Kind(enum.Enum):
    """What an atom IS, independent of whether it passed."""

    ROUTINE = "routine"
    REDIRECT = "redirect"
    EXEC = "exec"
    WEAKEN = "weaken"  # integrity downgrade: commit.gpgsign=false, http.sslVerify=false, ...
    LINK = "link"  # gitfile / commondir / admin gitdir / alternates / attributes
    HOOKFILE = "hookfile"
    UNKNOWN = "unknown"  # in no table row: "any new key starts suspicious"


class Pass(enum.Enum):
    """HOW an atom was allowed. NONE means it was not, and is the only value that yields a Finding."""

    LITERAL = "literal"  # table row + value validator accepted
    VALUE_OK = "value-ok"  # redirect whose value check passed
    TEMPLATE = "template"  # matches a registered installer template (lfs, hk)
    LKG = "lkg"  # identical to what was allowed at the last clean tick
    TRUSTED = "trusted"  # a human ran `accept` for this exact (repo, atom-hash)
    NONE = "none"


class Action(enum.Enum):
    RECORD = "record"  # event log only, nothing shown
    WARN = "warn"  # tell the model and user. No mutation.
    REVERT = "revert"  # restore from LKG / quarantine, then tell. Only if may_revert and restore is exact.
    BLOCK = "block"  # PreToolUse deny, or Stop `decision: block`.


# Restore ops are DATA computed by judge() from LKG/state, never from command text.
@dataclass(frozen=True)
class UnsetKey:
    file: PurePosixPath
    key: ConfigKey
    value: str  # `git config --file F --fixed-value --unset-all K V`


@dataclass(frozen=True)
class SetKey:
    file: PurePosixPath
    key: ConfigKey
    old: str  # LKG value
    new: str  # offending value, kept in quarantine for `accept`


@dataclass(frozen=True)
class WriteFile:
    path: PurePosixPath
    content: bytes
    mode: int  # temp + os.replace


@dataclass(frozen=True)
class MoveAside:
    path: PurePosixPath  # into state/quarantine/<finding-id>/ ; never delete


RestoreOp = Union[UnsetKey, SetKey, WriteFile, MoveAside]


@dataclass(frozen=True)
class Finding:
    id: str  # "f-" + first 6 hex of sha256(f"{anchor.path}\0{atom_hash(atom)}"). Stable => dedupe + `accept <id>`
    atom: Atom
    kind: Kind
    why: str  # one factual sentence, shown to the model
    action: Action
    restore: tuple[RestoreOp, ...]  # empty => cannot be reverted exactly => action is capped at WARN


@dataclass(frozen=True)
class Verdict:
    anchor: Anchor
    findings: tuple[Finding, ...]  # only atoms with Pass.NONE
    allowed_atoms: frozenset[str]  # atom keys that passed: becomes the next LKG
    notes: tuple[str, ...]  # RECORD-level facts (e.g. "core.hooksPath respelled, same target")


class TriggerKind(enum.Enum):
    SESSION_START = "session-start"
    CWD_CHANGED = "cwd-changed"
    POST_TOOL = "post-tool"  # PostToolUse and PostToolUseFailure, identical on purpose
    FILE_CHANGED = "file-changed"
    STOP = "stop"
    SESSION_END = "session-end"
    SWEEP = "sweep"  # CLI / optional timer


@dataclass(frozen=True)
class Trigger:
    """The ONLY thing triggers differ by. judge() consumes may_revert; everything else is for render()."""

    kind: TriggerKind
    session_id: str
    may_revert: bool  # False for SESSION_START / CWD_CHANGED, and for anchors outside the session's scope
    may_block: bool  # True only for STOP
    first_sight_in_session: bool  # anchor first seen mid-session: judge() synthesizes an LKG of passing atoms only


@dataclass(frozen=True)
class Lkg:
    """Last known good, per anchor. Holds only good atoms: what passed at the last tick, plus the
    previous good atoms behind any finding still open (which makes it dirty)."""

    anchor: Anchor
    common_dir: PurePosixPath
    atoms: Mapping[str, Atom]  # keyed by atom_key()
    fingerprint: Fingerprint
    dirty: bool  # a revert failed or a finding is open => no fast path next tick


@dataclass(frozen=True)
class TrustSet:
    """Human grants: (anchor, atom-hash). The only persistent exception mechanism. No glob, no 'trust this key'."""

    grants: frozenset[tuple[str, str]]


@dataclass(frozen=True)
class RuleSet:
    """Loaded once: table rows + templates + user additions."""

    rows: tuple[Row, ...]
    templates: Templates
    trusted_hosts: frozenset[str]

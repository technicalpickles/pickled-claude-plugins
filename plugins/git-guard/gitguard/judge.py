"""The one verdict function: classify every atom, compute exact restore ops, pick an action.

Pure module: no IO, and no command text. A trigger only says whether a revert is allowed and whether
the anchor is new this session; it never changes what is found, only what is done about it.
"""
from __future__ import annotations

import hashlib
from typing import Optional

from gitguard.files import classify_file
from gitguard.model import (
    Action,
    Anchor,
    Atom,
    ConfigEntry,
    FileAtom,
    Finding,
    Kind,
    Lkg,
    MoveAside,
    Pass,
    RestoreOp,
    RuleSet,
    SetKey,
    Surface,
    Trigger,
    TrustSet,
    UnsetKey,
    Verdict,
    WriteFile,
    atom_hash,
    atom_key,
)
from gitguard.rules import ClassifyCtx, classify_entry, make_ctx

__all__ = [
    "atom_hash",
    "atom_key",
    "classify",
    "finding_id",
    "judge",
    "lkg_from",
    "restore_ops",
]

FIRST_SIGHT_NOTE = "first sight in session: synthetic LKG from passing atoms"

_REVERTIBLE = frozenset({Kind.REDIRECT, Kind.EXEC, Kind.HOOKFILE, Kind.LINK})


def _classify(atom: Atom, ctx: ClassifyCtx, rules: RuleSet) -> tuple[Kind, Pass, Optional[str]]:
    if isinstance(atom, ConfigEntry):
        kind, passed = classify_entry(atom, ctx, rules)
        return kind, passed, None
    return classify_file(atom, ctx, rules)


def classify(atom: Atom, ctx: ClassifyCtx, rules: RuleSet) -> tuple[Kind, Pass]:
    """Kind and how it passed. File notes are dropped here; `judge` collects them."""
    kind, passed, _ = _classify(atom, ctx, rules)
    return kind, passed


def finding_id(anchor: Anchor, atom: Atom) -> str:
    digest = hashlib.sha256(f"{anchor.path}\0{atom_hash(atom)}".encode()).hexdigest()
    return "f-" + digest[:6]


def _atoms(cur: Surface) -> tuple[Atom, ...]:
    return (*cur.entries, *cur.files)


def _values(entries, target: ConfigEntry) -> list[str]:
    """Values of `target`'s (git_dir, file, key) among `entries`."""
    return [
        e.value
        for e in entries
        if isinstance(e, ConfigEntry)
        and e.member.git_dir == target.member.git_dir
        and e.file == target.file
        and e.key == target.key
    ]


def _restore_entry(entry: ConfigEntry, cur: Surface, lkg: Lkg) -> tuple[RestoreOp, ...]:
    old = _values(lkg.atoms.values(), entry)
    now = _values(cur.entries, entry)
    if len(old) == 1 and len(now) == 1:
        if old[0] == entry.value:
            return ()  # setting the LKG value back changes nothing: not an exact restore
        return (SetKey(entry.file, entry.key, old=old[0], new=entry.value),)
    return (UnsetKey(entry.file, entry.key, entry.value),)


def _restore_file(atom: FileAtom, lkg: Lkg) -> tuple[RestoreOp, ...]:
    if atom.role == "alternates":
        return ()
    prior = lkg.atoms.get(atom_key(atom))
    if isinstance(prior, FileAtom) and prior.kind == "file" and prior.content is not None:
        return (WriteFile(atom.path, prior.content, 0o755 if prior.executable else 0o644),)
    unknown_before = prior is None or (isinstance(prior, FileAtom) and prior.kind == "absent")
    if unknown_before and atom.role in ("hook", "attributes") and atom.kind != "absent":
        return (MoveAside(atom.path),)
    return ()


def restore_ops(atom: Atom, cur: Surface, lkg: Optional[Lkg]) -> tuple[RestoreOp, ...]:
    """Exact ops that bring `atom` back to `lkg`, or () when that cannot be done exactly.

    A key with one value in both LKG and `cur` is set back; any other config entry is unset by its
    own value, so the good values of a multi-valued key are never touched. A file is rewritten from
    LKG bytes; a hook or attributes file LKG never had is moved aside."""
    if lkg is None:
        return ()
    if isinstance(atom, ConfigEntry):
        return _restore_entry(atom, cur, lkg)
    return _restore_file(atom, lkg)


def _base_action(atom: Atom, kind: Kind) -> Action:
    if isinstance(atom, FileAtom) and atom.role == "alternates":
        return Action.WARN
    return Action.REVERT if kind in _REVERTIBLE else Action.WARN


def _why(atom: Atom, kind: Kind) -> str:
    if isinstance(atom, ConfigEntry):
        return f"{atom.key.dotted()}={atom.value!r} in {atom.file} is {kind.value}, not an allowed value"
    return f"{atom.role} {atom.path} is {kind.value} and matches no allowed state"


def _lkg(cur: Surface, atoms) -> Lkg:
    return Lkg(
        anchor=cur.anchor,
        common_dir=cur.common_dir,
        atoms={atom_key(a): a for a in atoms},
        fingerprint=cur.fingerprint,
        dirty=False,
    )


def judge(cur: Surface, lkg: Optional[Lkg], trust: TrustSet, rules: RuleSet, trig: Trigger) -> Verdict:
    ctx = make_ctx(cur, lkg, rules)
    anchor = str(cur.anchor.path)
    classified = []
    notes: list[str] = []
    for atom in _atoms(cur):
        kind, passed, note = _classify(atom, ctx, rules)
        if passed is Pass.NONE and (anchor, atom_hash(atom)) in trust.grants:
            passed = Pass.TRUSTED
        if note is not None:
            notes.append(note)
        classified.append((atom, kind, passed))

    allowed = frozenset(atom_key(a) for a, _, passed in classified if passed is not Pass.NONE)

    restore_from = lkg
    if lkg is None and trig.first_sight_in_session:
        restore_from = _lkg(cur, (a for a, _, passed in classified if passed is not Pass.NONE))
        notes.insert(0, FIRST_SIGHT_NOTE)

    findings = []
    seen: set[str] = set()
    for atom, kind, passed in classified:
        if passed is not Pass.NONE:
            continue
        fid = finding_id(cur.anchor, atom)
        if fid in seen:
            continue  # the same value twice in one file: one finding, and --unset-all removes both
        seen.add(fid)
        restore = restore_ops(atom, cur, restore_from)
        action = _base_action(atom, kind)
        if not trig.may_revert or restore == ():
            action = Action.WARN
        findings.append(Finding(fid, atom, kind, _why(atom, kind), action, restore))

    if lkg is not None:
        present = {atom_key(a) for a in _atoms(cur)}
        notes.extend(f"removed: {key}" for key in lkg.atoms if key not in present)

    return Verdict(cur.anchor, tuple(findings), allowed, tuple(notes))


def lkg_from(verdict: Verdict, cur: Surface) -> Lkg:
    """The next LKG: only the atoms of `cur` that `verdict` allowed."""
    return _lkg(cur, (a for a in _atoms(cur) if atom_key(a) in verdict.allowed_atoms))

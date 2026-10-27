"""Classifier for non-config control files: hook scripts and link files.

Pure module: no IO. Content and hashes come from the probe's FileAtom; path math is posixpath only.
Only a regular file can pass by template or by literal check. A symlink runs or points at whatever
its target holds at use time, so it passes only when it is identical to the last known good atom.
"""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
from typing import Optional

from gitguard.model import FileAtom, Kind, Lkg, Pass, RuleSet, atom_key
from gitguard.rules import ClassifyCtx
from gitguard.templates import hook_notice_slot, hook_template_match

# githooks(5), git 2.54.
HOOK_NAMES = frozenset(
    """applypatch-msg pre-applypatch post-applypatch pre-commit pre-merge-commit prepare-commit-msg
    commit-msg post-commit pre-rebase post-checkout post-merge pre-push pre-receive update
    proc-receive post-receive post-update reference-transaction push-to-checkout pre-auto-gc
    post-rewrite sendemail-validate fsmonitor-watchman p4-changelist p4-prepare-changelist
    p4-post-changelist p4-pre-submit post-index-change""".split()
)

Result = tuple[Kind, Pass, Optional[str]]


def lkg_equal(atom: FileAtom, lkg: Optional[Lkg]) -> bool:
    """`atom` is identical to the LKG atom of the same key: same sha256, kind and exec bit."""
    if lkg is None:
        return False
    prior = lkg.atoms.get(atom_key(atom))
    if not isinstance(prior, FileAtom):
        return False
    if atom.kind != "absent" and atom.sha256 is None:
        return False  # no hash, nothing to compare: it cannot be vouched for
    return (prior.sha256, prior.kind, prior.executable) == (atom.sha256, atom.kind, atom.executable)


def _text(atom: FileAtom) -> Optional[str]:
    if atom.kind != "file" or atom.content is None:
        return None
    try:
        return atom.content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _classify_hook(atom: FileAtom, ctx: ClassifyCtx, rules: RuleSet) -> Result:
    name = atom.path.name
    folded = name.casefold()  # case-insensitive filesystems run `Pre-Commit` as `pre-commit`
    if folded not in HOOK_NAMES or folded.endswith(".sample") or atom.kind == "absent":
        return Kind.ROUTINE, Pass.LITERAL, None
    if lkg_equal(atom, ctx.lkg):
        return Kind.HOOKFILE, Pass.LKG, None
    if atom.kind == "file":
        template = hook_template_match(atom, rules.templates)
        if template is not None:
            note = None
            if template.notice:
                slot = hook_notice_slot(atom, template)
                note = (
                    f"{name} hook installed by {template.name} names an executable: "
                    f"{slot if slot is not None else 'unknown'}"
                )
            return Kind.HOOKFILE, Pass.TEMPLATE, note
    return Kind.HOOKFILE, Pass.NONE, None


def _classify_commondir(atom: FileAtom, ctx: ClassifyCtx) -> Result:
    text = _text(atom)
    if text is not None and text.rstrip("\r\n") == "../..":  # git trims only line endings
        return Kind.LINK, Pass.LITERAL, None
    if lkg_equal(atom, ctx.lkg):
        return Kind.LINK, Pass.LKG, None
    return Kind.LINK, Pass.NONE, None


def _gitfile_target(text: str) -> Optional[str]:
    """The path git's read_gitfile_gently would use: exact `gitdir: ` prefix, trailing CR/LF stripped,
    nothing else trimmed. A CR, LF or NUL left inside the path makes git read something else."""
    if not text.startswith("gitdir: "):
        return None
    target = text[len("gitdir: "):].rstrip("\r\n")
    if not target or any(c in target for c in "\r\n\0"):
        return None
    return target


def _is_gitdir_of_checkout(resolved: str, common_dir: PurePosixPath) -> bool:
    """The common dir itself (a submodule checkout) or `<common>/worktrees/<one name>` (a linked worktree)."""
    path = PurePosixPath(posixpath.normpath(resolved))
    common = PurePosixPath(posixpath.normpath(str(common_dir)))
    if path == common:
        return True
    return path.parent == common / "worktrees" and path.name not in ("", ".", "..")


def _classify_gitfile(atom: FileAtom, ctx: ClassifyCtx) -> Result:
    text = _text(atom)
    target = _gitfile_target(text) if text is not None else None
    if target is not None:
        resolved = posixpath.join(str(ctx.surface.anchor.path), target)
        if _is_gitdir_of_checkout(resolved, ctx.surface.common_dir):
            return Kind.LINK, Pass.LITERAL, None
    return Kind.LINK, Pass.NONE, None


def _classify_admin_gitdir(atom: FileAtom, ctx: ClassifyCtx) -> Result:
    text = _text(atom)
    note = None
    if text is not None:
        content = text.strip()
        known = {posixpath.normpath(str(t)) for t in ctx.surface.toplevels}
        if posixpath.dirname(content) not in known:
            note = f"stale or foreign gitdir: {content}"
    return Kind.ROUTINE, Pass.LITERAL, note


def _classify_optional_link(atom: FileAtom, ctx: ClassifyCtx) -> Result:
    if atom.kind == "absent":
        return Kind.LINK, Pass.LITERAL, None
    if lkg_equal(atom, ctx.lkg):
        return Kind.LINK, Pass.LKG, None
    return Kind.LINK, Pass.NONE, None


def classify_file(atom: FileAtom, ctx: ClassifyCtx, rules: RuleSet) -> Result:
    """(kind, how it passed, optional note for `Verdict.notes`)."""
    role = atom.role
    if role == "hook":
        return _classify_hook(atom, ctx, rules)
    if role == "hooks-dir":
        return Kind.ROUTINE, Pass.LITERAL, None
    if role == "commondir":
        return _classify_commondir(atom, ctx)
    if role == "gitfile":
        return _classify_gitfile(atom, ctx)
    if role == "admin-gitdir":
        return _classify_admin_gitdir(atom, ctx)
    if role in ("attributes", "alternates"):
        return _classify_optional_link(atom, ctx)
    if role == "guard-state":
        raise NotImplementedError("guard-state is classified in v0.1")
    raise ValueError(f"unknown file role: {role!r}")

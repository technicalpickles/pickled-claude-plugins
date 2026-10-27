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
    assert len(HOOK_NAMES) == 28
    assert {"pre-commit", "post-checkout", "reference-transaction", "post-index-change"} <= HOOK_NAMES


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


def test_lkg_equal_same_atom_is_true():
    atom = hook("pre-commit", BAD)
    assert lkg_equal(atom, lkg_of(atom))


# -- commondir ----------------------------------------------------------------------------------


@pytest.mark.parametrize("content", [b"../..", b"../..\n", b"../..\r\n \n"])
def test_commondir_default_passes(content):
    assert classify(link("commondir", content)) == (Kind.LINK, Pass.LITERAL, None)


@pytest.mark.parametrize("content", [b"/tmp/evil/.git", b"/tmp/evil/.git\n", b"../../..", b" ../.."])
def test_commondir_redirect_fails(content):
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


@pytest.mark.parametrize("content", [b"", b"not a gitfile\n", b"gitdir:\n"])
def test_gitfile_malformed_fails(content):
    assert classify(gitfile(content), **WT_KW) == (Kind.LINK, Pass.NONE, None)


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

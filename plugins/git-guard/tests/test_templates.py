"""Tests for the installer templates (lfs, hk, portool) and the rules `template` check."""
from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from gitguard.model import FileAtom, Kind, Pass
from gitguard.rules import classify_entry, default_rules, make_ctx
from gitguard.templates import (
    DEFAULT_TEMPLATES,
    HookTemplate,
    config_template_match,
    hook_notice_slot,
    hook_template_match,
)
from tests.support import FIXTURES, entry, hook, surface

T = DEFAULT_TEMPLATES
LFS_DIRS = ("lfs-3.7.1", "lfs-echo")
LFS_HOOKS = ("post-checkout", "post-commit", "post-merge", "pre-push")
HK_CMD = 'test "${HK:-1}" = "0" || hk run pre-commit --from-hook'


def fixture(directory: str, name: str) -> bytes:
    return (FIXTURES / "hooks" / directory / name).read_bytes()


def match(e):
    return config_template_match(e, surface([e]), T)


# -- config: lfs filter -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key, value",
    [
        ("filter.lfs.clean", "git-lfs clean -- %f"),
        ("filter.lfs.smudge", "git-lfs smudge -- %f"),
        ("filter.lfs.process", "git-lfs filter-process"),
        ("filter.lfs.required", "true"),
    ],
)
def test_lfs_filter_values_pass(key, value):
    assert match(entry(key, value)) == "lfs-filter"


@pytest.mark.parametrize(
    "key, value",
    [
        ("filter.lfs.smudge", "sh -c x"),
        ("filter.lfs.clean", "git-lfs clean -- %f; id"),
        ("filter.lfs.clean", "git-lfs clean -- %f\n"),
        ("filter.lfs.clean", "git-lfs smudge -- %f"),  # right value, wrong variable
        ("filter.lfs.required", "false"),
        ("filter.lfs.textconv", "git-lfs clean -- %f"),
        ("filter.LFS.clean", "git-lfs clean -- %f"),  # subsection is case sensitive
        ("filter.other.clean", "git-lfs clean -- %f"),
    ],
)
def test_lfs_filter_wrong_value_fails(key, value):
    assert match(entry(key, value)) is None


# -- config: hk ---------------------------------------------------------------------------------


def hk_pair(event="pre-commit", command=HK_CMD, sub="hk-pre-commit", file="/r/a/.git/config"):
    return (
        entry(f"hook.{sub}.command", command, file=file),
        entry(f"hook.{sub}.event", event, file=file),
    )


def test_hk_pair_passes():
    cmd, ev = hk_pair()
    s = surface([cmd, ev])
    assert config_template_match(cmd, s, T) == "hk"
    assert config_template_match(ev, s, T) == "hk"


def test_hk_other_event_name_passes():
    command = 'test "${HK:-1}" = "0" || hk run pre-push --from-hook'
    cmd, ev = hk_pair(event="pre-push", command=command, sub="hk-pre-push")
    s = surface([cmd, ev])
    assert config_template_match(cmd, s, T) == "hk"
    assert config_template_match(ev, s, T) == "hk"


def test_hk_event_mismatch_fails_both():
    cmd, ev = hk_pair(event="post-checkout")
    s = surface([cmd, ev])
    assert config_template_match(cmd, s, T) is None
    assert config_template_match(ev, s, T) is None


def test_hk_command_name_mismatch_fails_both():
    cmd, ev = hk_pair(command='test "${HK:-1}" = "0" || hk run post-checkout --from-hook')
    s = surface([cmd, ev])
    assert config_template_match(cmd, s, T) is None
    assert config_template_match(ev, s, T) is None


def test_hk_wrong_subsection_fails():
    cmd, ev = hk_pair(sub="evil")
    s = surface([cmd, ev])
    assert config_template_match(cmd, s, T) is None
    assert config_template_match(ev, s, T) is None


def test_hk_command_alone_fails():
    cmd, _ = hk_pair()
    assert config_template_match(cmd, surface([cmd]), T) is None


def test_hk_event_alone_fails():
    _, ev = hk_pair()
    assert config_template_match(ev, surface([ev]), T) is None


def test_hk_peer_must_be_in_the_same_file():
    cmd = hk_pair()[0]
    ev = hk_pair(file="/r/a/.git/config.worktree")[1]
    s = surface([cmd, ev])
    assert config_template_match(cmd, s, T) is None
    assert config_template_match(ev, s, T) is None


@pytest.mark.parametrize(
    "command",
    [
        HK_CMD + "; id",
        HK_CMD + "\nid",
        HK_CMD + " ",
        "x" + HK_CMD,
        HK_CMD.replace("hk run", "evil run"),
        HK_CMD.replace(" --from-hook", ""),
        HK_CMD.replace("pre-commit", "$(id)"),
        HK_CMD.replace("pre-commit", "pre commit"),
        HK_CMD.replace("= \"0\"", "= \"1\""),
    ],
)
def test_hk_command_variants_fail(command):
    cmd, ev = hk_pair(command=command)
    s = surface([cmd, ev])
    assert config_template_match(cmd, s, T) is None
    assert config_template_match(ev, s, T) is None


def test_hk_extra_command_in_same_file_poisons_event():
    cmd, ev = hk_pair()
    evil = entry("hook.hk-pre-commit.command", "sh -c x")
    s = surface([cmd, evil, ev])
    assert config_template_match(cmd, s, T) == "hk"
    assert config_template_match(evil, s, T) is None
    assert config_template_match(ev, s, T) is None


def test_hk_extra_event_fails_alone():
    cmd, ev = hk_pair()
    extra = entry("hook.hk-pre-commit.event", "post-checkout")
    s = surface([cmd, ev, extra])
    assert config_template_match(ev, s, T) == "hk"
    assert config_template_match(extra, s, T) is None


def test_other_keys_have_no_template():
    assert match(entry("core.fsmonitor", "/tmp/x")) is None
    assert match(entry("hook.hk-pre-commit.enabled", "true")) is None


# -- hooks: lfs by sha --------------------------------------------------------------------------


@pytest.mark.parametrize("directory", LFS_DIRS)
@pytest.mark.parametrize("name", LFS_HOOKS)
def test_lfs_hook_fixtures_match_by_sha(directory, name):
    atom = hook(name, fixture(directory, name))
    found = hook_template_match(atom, T)
    assert found is not None and found.name == "lfs" and found.notice is False


@pytest.mark.parametrize("directory", LFS_DIRS)
@pytest.mark.parametrize("name", LFS_HOOKS)
def test_lfs_hook_sha_without_content_still_matches(directory, name):
    full = hook(name, fixture(directory, name))
    atom = FileAtom(full.member, full.path, "hook", "file", full.sha256, True, None)
    assert hook_template_match(atom, T) is not None


def test_lfs_sha_bound_to_hook_name():
    body = fixture("lfs-3.7.1", "pre-push")
    assert hook_template_match(hook("post-commit", body), T) is None


def test_sha_with_wrong_content_hash_fails():
    full = hook("pre-push", fixture("lfs-3.7.1", "pre-push"))
    forged = FileAtom(full.member, full.path, "hook", "file", full.sha256, True, b"#!/bin/sh\nid\n")
    assert hook_template_match(forged, T) is None


# -- hooks: lfs structural ----------------------------------------------------------------------


def lfs_body(name="post-checkout", msg="Something new. Tabs and 'quotes' %s are fine.", style="printf"):
    if style == "printf":
        fail = f'printf >&2 "\\n%s\\n\\n" "{msg}"'
    else:
        fail = f'echo >&2 "\\n{msg}\\n"'
    return (
        "#!/bin/sh\n"
        f"command -v git-lfs >/dev/null 2>&1 || {{ {fail}; exit 2; }}\n"
        f'git lfs {name} "$@"\n'
    ).encode()


@pytest.mark.parametrize("style", ["printf", "echo"])
@pytest.mark.parametrize("name", LFS_HOOKS)
def test_lfs_structural_accepts_new_message(name, style):
    atom = hook(name, lfs_body(name, style=style))
    found = hook_template_match(atom, T)
    assert found is not None and found.name == "lfs" and found.notice is False


def test_lfs_structural_matches_the_real_body_template():
    # The 3.7.1 body re-rendered by lfs_body() is not byte-identical, so this proves the regex path.
    real = fixture("lfs-3.7.1", "post-merge")
    assert lfs_body("post-merge") != real
    assert hook_template_match(hook("post-merge", lfs_body("post-merge")), T) is not None


@pytest.mark.parametrize(
    "msg",
    [
        "pwn $(id)",
        "pwn `id`",
        "pwn $HOME",
        'pwn " ; id ; "',
        "pwn \\x",
        "pwn \\\nid",
        "pwn\nid",
        "pwn\rid",
    ],
)
@pytest.mark.parametrize("style", ["printf", "echo"])
def test_lfs_structural_rejects_injection_in_message(msg, style):
    assert hook_template_match(hook("post-checkout", lfs_body(msg=msg, style=style)), T) is None


@pytest.mark.parametrize(
    "tail",
    [
        "id\n",
        "# x\n",
        "\n\n",
        " ; id\n",
        "\\\nid\n",
    ],
)
def test_lfs_structural_rejects_extra_lines_after_command(tail):
    body = lfs_body("post-checkout").rstrip(b"\n") + b"\n" + tail.encode()
    assert hook_template_match(hook("post-checkout", body), T) is None
    glued = lfs_body("post-checkout").rstrip(b"\n") + tail.encode()
    assert hook_template_match(hook("post-checkout", glued), T) is None


def test_lfs_structural_rejects_extra_line_before():
    body = lfs_body("post-checkout").replace(b"#!/bin/sh\n", b"#!/bin/sh\nid\n")
    assert hook_template_match(hook("post-checkout", body), T) is None


def test_lfs_structural_rejects_changed_skeleton():
    good = lfs_body("post-checkout")
    for bad in (
        good.replace(b"exit 2", b"exit 0; id"),
        good.replace(b"git-lfs >/dev/null", b"git-lfs-x >/dev/null"),
        good.replace(b"#!/bin/sh", b"#!/bin/bash"),
        good.replace(b'"$@"', b"$@"),
        good.replace(b'"$@"', b'"$@" extra'),
        good.replace(b"git lfs post-checkout", b"git lfs post-checkout;"),
        good.replace(b"||", b"&&"),
        good.rstrip(b"\n"),  # no trailing newline
        good.replace(b"\n", b"\r\n"),
    ):
        assert hook_template_match(hook("post-checkout", bad), T) is None, bad


def test_lfs_name_must_match_file():
    body = fixture("lfs-3.7.1", "pre-push")
    assert hook_template_match(hook("post-commit", body), T) is None
    assert hook_template_match(hook("post-commit", lfs_body("pre-push")), T) is None


def test_lfs_structural_only_for_the_four_hooks():
    assert hook_template_match(hook("pre-commit", lfs_body("pre-commit")), T) is None
    assert hook_template_match(hook("post-checkout", lfs_body("pre-commit")), T) is None


def test_non_utf8_content_returns_none():
    body = lfs_body("post-checkout").replace(b"Something", b"\xff\xfe")
    assert hook_template_match(hook("post-checkout", body), T) is None


# -- hooks: portool -----------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["post-checkout", "post-merge"])
def test_portool_matches_with_notice(name):
    found = hook_template_match(hook(name, fixture("portool", name)), T)
    assert found is not None and found.name == "portool" and found.notice is True


def portool_body(bin_value: str) -> bytes:
    real = fixture("portool", "post-checkout").decode()
    return real.replace('PORTOOL_BIN="/home/u/.cargo/bin/portool"', f'PORTOOL_BIN="{bin_value}"').encode()


@pytest.mark.parametrize("value", ["portool", "/tmp/evil", "/tmp/portool-evil", "relative/portool"])
def test_portool_rejects_relative_or_other_binary(value):
    assert hook_template_match(hook("post-checkout", portool_body(value)), T) is None


@pytest.mark.parametrize("value", ["/x/$(id)/portool", "/x/`id`/portool", "/x/$H/portool",
                                   '/x/"; id; "/portool', "/x/\\/portool", "/x\nid/portool"])
def test_portool_rejects_metacharacters_in_slot(value):
    assert hook_template_match(hook("post-checkout", portool_body(value)), T) is None


def test_portool_accepts_other_absolute_path():
    atom = hook("post-merge", portool_body("/opt/homebrew/bin/portool"))
    found = hook_template_match(atom, T)
    assert found is not None and found.name == "portool"


@pytest.mark.parametrize(
    "edit",
    [
        lambda b: b + b"id\n",
        lambda b: b.replace(b"exit 0", b"exit 0; id"),
        lambda b: b.replace(b"sync --quiet", b"sync --quiet; id"),
        lambda b: b.replace(b"# installed by portool", b"# installed by portool\nid"),
        lambda b: b.replace(b"fi\nexit", b"fi\nid\nexit"),
    ],
)
def test_portool_rejects_body_edits(edit):
    assert hook_template_match(hook("post-checkout", edit(fixture("portool", "post-checkout"))), T) is None


def test_portool_only_for_its_hooks():
    assert hook_template_match(hook("pre-commit", fixture("portool", "post-checkout")), T) is None


# -- safety shared by every hook template -------------------------------------------------------


@pytest.mark.parametrize("kind", ["symlink", "dir", "absent"])
@pytest.mark.parametrize("src", [("lfs-3.7.1", "pre-push"), ("portool", "post-merge")])
def test_non_file_hook_never_template_passes(kind, src):
    atom = hook(src[1], fixture(*src), kind=kind)
    assert hook_template_match(atom, T) is None


def test_non_hook_role_never_template_passes():
    full = hook("pre-push", fixture("lfs-3.7.1", "pre-push"))
    atom = FileAtom(full.member, full.path, "attributes", "file", full.sha256, True, full.content)
    assert hook_template_match(atom, T) is None


def test_unknown_hook_body_is_none():
    assert hook_template_match(hook("pre-commit", b"#!/bin/sh\nid\n"), T) is None


def test_hook_template_is_a_hooktemplate():
    found = hook_template_match(hook("pre-push", fixture("lfs-3.7.1", "pre-push")), T)
    assert isinstance(found, HookTemplate)
    assert PurePosixPath("pre-push").name in found.hook_names


# -- wiring into rules --------------------------------------------------------------------------


def test_rules_template_check_uses_templates():
    rules = default_rules()
    e = entry("filter.lfs.clean", "git-lfs clean -- %f")
    ctx = make_ctx(surface([e]), None, rules)
    assert classify_entry(e, ctx, rules) == (Kind.EXEC, Pass.TEMPLATE)


def test_rules_template_check_rejects_wrong_value():
    rules = default_rules()
    e = entry("filter.lfs.smudge", "sh -c x")
    ctx = make_ctx(surface([e]), None, rules)
    assert classify_entry(e, ctx, rules) == (Kind.EXEC, Pass.NONE)


def test_rules_template_check_hk_pair_and_orphan():
    rules = default_rules()
    cmd, ev = hk_pair()
    both = make_ctx(surface([cmd, ev]), None, rules)
    assert classify_entry(cmd, both, rules) == (Kind.EXEC, Pass.TEMPLATE)
    assert classify_entry(ev, both, rules) == (Kind.EXEC, Pass.TEMPLATE)
    alone = make_ctx(surface([cmd]), None, rules)
    assert classify_entry(cmd, alone, rules) == (Kind.EXEC, Pass.NONE)


def test_default_rules_carry_default_templates():
    assert default_rules().templates is DEFAULT_TEMPLATES


# -- hooks: notice slot -------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["post-checkout", "post-merge"])
def test_portool_notice_slot_is_the_binary_path(name):
    atom = hook(name, fixture("portool", name))
    template = hook_template_match(atom, T)
    assert hook_notice_slot(atom, template) == "/home/u/.cargo/bin/portool"


def test_notice_slot_none_for_template_without_slot():
    atom = hook("pre-push", fixture("lfs-echo", "pre-push"))
    template = hook_template_match(atom, T)
    assert hook_notice_slot(atom, template) is None


def test_notice_slot_none_without_content():
    atom = hook("post-checkout", fixture("portool", "post-checkout"))
    hashed_only = FileAtom(atom.member, atom.path, atom.role, atom.kind, atom.sha256, True, None)
    assert hook_notice_slot(hashed_only, T.hooks[1]) is None

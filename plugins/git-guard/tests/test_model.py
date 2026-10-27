"""Tests for the frozen data model and the shared test builders."""
from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path, PurePosixPath

import pytest

from gitguard.model import (
    Anchor,
    ConfigKey,
    Fingerprint,
    StatSig,
    TriggerKind,
    atom_hash,
    atom_key,
)
from tests.support import (
    ANCHOR,
    COMMON,
    corpus_surfaces,
    entry,
    hook,
    link,
    surface,
    trigger,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_lowercases_section_and_variable():
    assert ConfigKey.parse("Core.HooksPath") == ConfigKey("core", None, "hookspath")


def test_parse_keeps_dotted_subsection_verbatim():
    assert ConfigKey.parse("url.https://Evil/.insteadOf") == ConfigKey(
        "url", "https://Evil/", "insteadof"
    )
    assert ConfigKey.parse("submodule.vendor/vim-plug.url").subsection == "vendor/vim-plug"


@pytest.mark.parametrize(
    "dotted",
    ["core.hookspath", "url.https://Evil/.insteadof", "submodule.vendor/vim-plug.url"],
)
def test_dotted_round_trips(dotted):
    assert ConfigKey.parse(dotted).dotted() == dotted


def test_parse_rejects_key_without_section_and_variable():
    with pytest.raises(ValueError):
        ConfigKey.parse("nodots")


def test_dataclasses_are_frozen_and_hashable():
    s = surface(
        entries=[entry("core.hooksPath", ".githooks")],
        files=[hook("pre-commit", b"#!/bin/sh\n")],
    )
    assert hash(s) == hash(
        surface(
            entries=[entry("core.hooksPath", ".githooks")],
            files=[hook("pre-commit", b"#!/bin/sh\n")],
        )
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.home = PurePosixPath("/elsewhere")  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.entries[0].value = "x"  # type: ignore[misc]


def test_fingerprint_empty_and_hashable_with_sigs():
    assert Fingerprint.EMPTY == Fingerprint(sigs={})
    sig = StatSig(mtime_ns=1, ctime_ns=2, size=3, ino=4)
    assert hash(Fingerprint(sigs={"/a": sig, "/b": None})) == hash(
        Fingerprint(sigs={"/b": None, "/a": sig})
    )


def test_all_path_fields_are_pure_posix_paths():
    s = surface(entries=[entry("core.bare", "false")], tracked_dirs=["/r/a/.githooks"])
    paths = [s.common_dir, s.home, s.anchor.path, *s.toplevels, *s.tracked_dirs]
    paths += [s.entries[0].file, s.entries[0].member.git_dir]
    assert all(type(p) is PurePosixPath for p in paths)


def test_builders_defaults():
    e = entry("core.bare", "false")
    assert e.member == COMMON and e.scope == "local"
    assert e.file == PurePosixPath("/r/a/.git/config")

    h = hook("pre-commit", b"abc")
    assert h.path == PurePosixPath("/r/a/.git/hooks/pre-commit")
    assert h.role == "hook" and h.kind == "file" and h.executable
    assert h.sha256 and h.content == b"abc"

    absent = link("gitfile", None)
    assert absent.kind == "absent" and absent.sha256 is None and absent.content is None
    present = link("commondir", b"../..\n")
    assert present.kind == "file" and present.sha256

    t = trigger()
    assert t.kind is TriggerKind.POST_TOOL and t.may_revert and not t.may_block
    assert ANCHOR == Anchor(PurePosixPath("/r/a"))


def test_corpus_surfaces_cover_every_row():
    rows = [
        line for line in (FIXTURES / "corpus.tsv").read_text().splitlines() if line
    ]
    surfaces = corpus_surfaces()
    assert sum(len(s.entries) for s in surfaces) == len(rows)
    assert len({s.anchor for s in surfaces}) == len(surfaces)


def test_corpus_surfaces_classify_members_and_scopes():
    by_role: dict[tuple[str, str], int] = {}
    for s in corpus_surfaces():
        assert all(e.file.is_absolute() for e in s.entries)
        for e in s.entries:
            assert e.member in s.members
            by_role[(e.member.role, e.scope)] = by_role.get((e.member.role, e.scope), 0) + 1
    assert set(by_role) == {("common", "local"), ("admin", "worktree"), ("module", "module")}

    module_dirs = {m.git_dir.as_posix() for s in corpus_surfaces() for m in s.members if m.role == "module"}
    assert any(d.endswith("/.git/modules/vendor/vim-plug") for d in module_dirs)


def test_corpus_surfaces_attach_tracked_dirs():
    expected = {
        PurePosixPath(line)
        for line in (FIXTURES / "corpus_tracked_dirs.txt").read_text().splitlines()
        if line
    }
    got = {d for s in corpus_surfaces() for d in s.tracked_dirs}
    assert got == expected
    for s in corpus_surfaces():
        assert all(d.is_relative_to(s.anchor.path) for d in s.tracked_dirs)


# -- atom_key / atom_hash -----------------------------------------------------------------------


def test_atom_key_config_entry_format():
    e = entry("Core.HooksPath", ".githooks")
    assert atom_key(e) == "cfg|/r/a/.git|/r/a/.git/config|core.hookspath|.githooks"


def test_atom_key_keeps_dotted_subsection():
    e = entry("url.https://Evil/.insteadOf", "x")
    assert atom_key(e) == "cfg|/r/a/.git|/r/a/.git/config|url.https://Evil/.insteadof|x"


def test_atom_key_file_format():
    assert atom_key(hook("pre-commit", b"x")) == "file|/r/a/.git/hooks/pre-commit"


def test_atom_hash_config_entry_is_sha256_of_key():
    e = entry("core.hooksPath", ".githooks")
    assert atom_hash(e) == hashlib.sha256(atom_key(e).encode()).hexdigest()


def test_atom_hash_file_formula():
    a = hook("pre-commit", b"#!/bin/sh\n")
    raw = f"{atom_key(a)}\0{a.sha256}\0file\0True"
    assert atom_hash(a) == hashlib.sha256(raw.encode()).hexdigest()


def test_atom_hash_absent_file_uses_empty_sha():
    a = link("attributes", None)
    raw = f"{atom_key(a)}\0\0absent\0False"
    assert atom_hash(a) == hashlib.sha256(raw.encode()).hexdigest()


def test_atom_hash_changes_with_content_kind_and_exec_bit():
    base = hook("pre-commit", b"a")
    assert len({
        atom_hash(base),
        atom_hash(hook("pre-commit", b"b")),
        atom_hash(hook("pre-commit", b"a", kind="symlink")),
        atom_hash(hook("pre-commit", b"a", executable=False)),
    }) == 4

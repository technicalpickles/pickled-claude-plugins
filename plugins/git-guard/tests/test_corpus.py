"""The two proofs: the real key corpus yields no findings, and every attack row is caught."""
from __future__ import annotations

import pytest

from gitguard.judge import judge, lkg_from
from gitguard.model import ConfigEntry, ConfigKey, TriggerKind, TrustSet
from gitguard.rules import default_rules
from tests.support import FIXTURES, corpus_surfaces, entry, surface, trigger

RULES = default_rules()
NO_TRUST = TrustSet(frozenset())
HK_PRE_COMMIT = 'test "${HK:-1}" = "0" || hk run pre-commit --from-hook'


def test_corpus_first_sight_no_findings():
    surfaces = corpus_surfaces()
    assert sum(len(s.entries) for s in surfaces) == 1013
    for s in surfaces:
        verdict = judge(s, None, NO_TRUST, RULES, trigger(TriggerKind.SWEEP, may_revert=False))
        assert verdict.findings == (), s.anchor


def _attack_rows() -> list[tuple[str, str, str, str]]:
    rows = []
    for line in (FIXTURES / "attacks.tsv").read_text().splitlines():
        if line:
            key, value, kind, action = line.split("\t")
            rows.append((key, value, kind, action))
    return rows


ATTACKS = _attack_rows()


def _baseline():
    return surface(
        [
            entry("remote.origin.url", "git@github.com:a/b.git"),
            entry("remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"),
            entry("hook.hk-pre-commit.command", HK_PRE_COMMIT),
            entry("hook.hk-pre-commit.event", "pre-commit"),
        ]
    )


def _with(base, dotted: str, value: str):
    """`base` with `dotted` set to `value` in the common config: replaced if present, else added."""
    key = ConfigKey.parse(dotted)
    entries = list(base.entries)
    for i, e in enumerate(entries):
        if e.key == key:
            entries[i] = entry(dotted, value)
            break
    else:
        entries.append(entry(dotted, value))
    return surface(entries)


def test_attack_baseline_is_clean():
    base = _baseline()
    verdict = judge(base, None, NO_TRUST, RULES, trigger(TriggerKind.SWEEP, may_revert=False))
    assert verdict.findings == ()
    assert len(lkg_from(verdict, base).atoms) == 4


def test_attack_rows_cover_fixture():
    assert len(ATTACKS) == 38


@pytest.mark.parametrize("dotted, value, kind, action", ATTACKS)
def test_attack_rows_all_found(dotted, value, kind, action):
    base = _baseline()
    lkg = lkg_from(judge(base, None, NO_TRUST, RULES, trigger(TriggerKind.SWEEP)), base)
    cur = _with(base, dotted, value)
    verdict = judge(cur, lkg, NO_TRUST, RULES, trigger(TriggerKind.POST_TOOL))
    key = ConfigKey.parse(dotted)
    on_key = [
        f for f in verdict.findings
        if isinstance(f.atom, ConfigEntry) and f.atom.key == key and f.atom.value == value
    ]
    assert [(f.kind.value, f.action.value) for f in on_key] == [(kind, action)]

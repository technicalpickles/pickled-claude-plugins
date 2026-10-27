"""Sanity checks on the committed fixtures: the scrubbed key corpus, the
attack rows, the `git help --config` var list and the real hook files.

The scrub checks matter most: this repo is public and the corpus is derived
from private repos, so a leak here is a leak in the open.
"""
from __future__ import annotations

import re
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

PATH_RE = re.compile(r"^/home/u/src/repo-\d+/\.git/")
REL_RE = re.compile(
    r"^/home/u/src/repo-\d+/\.git/"
    r"(config|config\.worktree|worktrees/[^/]+/config\.worktree|modules/.+/config)$"
)
BRANCH_TOKEN = re.compile(r"^b-\d+$")
URL_PATH_RE = re.compile(r"^owner-\d+/repo-\d+(\.git)?$")
URLISH_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*://[^/]+/|[^@\s:/]+@[^:\s/]+:)(?P<path>.*)$")
KEPT_BRANCHES = {"main", "master"}
ATTACK_KINDS = {"exec", "redirect", "weaken"}
ATTACK_ACTIONS = {"revert", "warn"}


def corpus_rows() -> list[tuple[str, str, str]]:
    rows = []
    for line in (FIXTURES / "corpus.tsv").read_text().splitlines():
        path, key, value = line.split("\t")
        rows.append((path, key, value))
    return rows


def subsection(key: str) -> str | None:
    first, last = key.find("."), key.rfind(".")
    if first == last:
        return None
    return key[first + 1 : last]


def test_corpus_is_scrubbed():
    rows = corpus_rows()
    assert rows, "corpus.tsv is empty"
    for path, key, value in rows:
        assert PATH_RE.match(path), path

        if key.startswith("branch."):
            sub = subsection(key)
            assert sub is not None
            assert sub in KEPT_BRANCHES or BRANCH_TOKEN.match(sub), key

        for m in re.finditer(r"refs/heads/([^\s:*]+)", value):
            b = m.group(1)
            assert b in KEPT_BRANCHES or BRANCH_TOKEN.match(b), (key, value)
        for m in re.finditer(r"refs/remotes/[^/\s:*]+/([^\s:*]+)", value):
            b = m.group(1)
            assert b in KEPT_BRANCHES or BRANCH_TOKEN.match(b), (key, value)

        if key.startswith("worktrunk."):
            assert value in KEPT_BRANCHES or BRANCH_TOKEN.match(value), (key, value)

        m = URLISH_RE.match(value)
        if m:
            assert URL_PATH_RE.match(m.group("path")), (key, value)

        if key.endswith(".gh-resolved"):
            assert value == "base" or URL_PATH_RE.match(value), (key, value)

        if value.startswith("/"):
            assert re.match(r"^/home/u/src/repo-\d+(/|$)", value), (key, value)

        assert "technicalpickles" not in path + key + value
        assert "/Users/" not in path + key + value


def test_corpus_paths_have_known_shapes():
    rels = set()
    for path, _, _ in corpus_rows():
        assert REL_RE.match(path), path
        rels.add(path.split("/.git/", 1)[1].split("/")[0])
    # The two top-level `.git/config.worktree` files in the scan are empty, so
    # only `config`, `worktrees/*` and `modules/*` contribute rows.
    assert {"config", "worktrees", "modules"} <= rels


def test_corpus_keeps_git_normalized_keys():
    # section and variable lowercased; subsection verbatim (never lowercased by us)
    for _, key, _ in corpus_rows():
        first, last = key.find("."), key.rfind(".")
        assert first > 0
        section = key[:first]
        var = key[last + 1 :]
        assert section == section.lower(), key
        assert var == var.lower(), key


def test_corpus_has_worktree_rows():
    worktree = [r for r in corpus_rows() if r[0].endswith("/config.worktree")]
    assert len(worktree) >= 3
    hookspaths = [r for r in worktree if r[1] == "core.hookspath"]
    assert hookspaths and all(
        re.match(r"^/home/u/src/repo-\d+/\.githooks$", v) for _, _, v in hookspaths
    )
    assert any(k == "core.longpaths" for _, k, _ in worktree)


def test_corpus_tracked_dirs_scrubbed():
    lines = (FIXTURES / "corpus_tracked_dirs.txt").read_text().splitlines()
    assert len(lines) == 2
    for line in lines:
        assert re.match(r"^/home/u/src/repo-\d+/\.githooks$", line), line


def test_tracked_dirs_share_repo_mapping_with_corpus():
    corpus_repos = {p.split("/.git/")[0] for p, _, _ in corpus_rows()}
    for line in (FIXTURES / "corpus_tracked_dirs.txt").read_text().splitlines():
        assert line.rsplit("/", 1)[0] in corpus_repos, line


def test_attacks_count():
    rows = [
        line.split("\t")
        for line in (FIXTURES / "attacks.tsv").read_text().splitlines()
    ]
    assert len(rows) == 38
    for row in rows:
        assert len(row) == 4, row
        key, _value, kind, action = row
        assert key
        assert kind in ATTACK_KINDS, row
        assert action in ATTACK_ACTIONS, row
    # only weaken rows warn
    assert {r[3] for r in rows if r[2] == "weaken"} == {"warn"}
    assert {r[3] for r in rows if r[2] != "weaken"} == {"revert"}


def test_git_help_config_fixture():
    lines = (FIXTURES / "git-help-config.txt").read_text().splitlines()
    assert lines[0] == "# git 2.54.0"
    body = lines[1:]
    assert len(body) == 995
    assert "core.hooksPath" in body or any(l.startswith("core.hooksPath") for l in body)


def test_hook_fixtures_present():
    hooks = FIXTURES / "hooks"
    four = {"post-checkout", "post-commit", "post-merge", "pre-push"}
    assert {p.name for p in (hooks / "lfs-3.7.1").iterdir()} == four
    assert {p.name for p in (hooks / "lfs-echo").iterdir()} == four
    assert {p.name for p in (hooks / "portool").iterdir()} == {
        "post-checkout",
        "post-merge",
    }


def test_hook_fixtures_clean_and_distinct():
    hooks = FIXTURES / "hooks"
    for p in hooks.rglob("*"):
        if p.is_file():
            data = p.read_bytes()
            assert b"technicalpickles" not in data, p
            assert b"/Users/" not in data, p
            assert data.startswith(b"#!/bin/sh\n"), p
    # lfs-3.7.1 and lfs-echo differ only by how the warning is printed
    a = (hooks / "lfs-3.7.1" / "post-checkout").read_bytes()
    b = (hooks / "lfs-echo" / "post-checkout").read_bytes()
    assert a != b
    portool = (hooks / "portool" / "post-checkout").read_text()
    assert "installed by portool" in portool
    assert "/home/u/" in portool

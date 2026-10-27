"""Tests for the config-key classifier table and its value checks."""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

import pytest

from gitguard.model import ConfigKey, Fingerprint, Kind, Lkg, MemberRef, Pass
from gitguard.rules import (
    ROWS,
    classify_entry,
    default_rules,
    make_ctx,
    match_row,
    resolve_redirect,
    rows_for_key,
)
from tests.support import ANCHOR, COMMON, entry, surface

FIXTURES = Path(__file__).parent / "fixtures"

R, X, D, W, U = Kind.ROUTINE, Kind.REDIRECT, Kind.EXEC, Kind.WEAKEN, Kind.UNKNOWN
LIT, OK, TPL, NONE = Pass.LITERAL, Pass.VALUE_OK, Pass.TEMPLATE, Pass.NONE

MODULE = MemberRef(PurePosixPath("/r/a/.git/modules/sub"), "module")

# The surface every row example is judged against: one remote (origin, on github.com), a tracked
# `.githooks`, and a submodule member so include targets under its git dir resolve.
BASE = surface(
    [
        entry("remote.origin.url", "https://github.com/o/r.git"),
        entry("submodule.sub.active", "true", member=MODULE,
              file="/r/a/.git/modules/sub/config", scope="module"),
    ],
    tracked_dirs=["/r/a/.githooks"],
)


def classify(dotted: str, value: str, **kw):
    rules = default_rules()
    return classify_entry(entry(dotted, value, **kw), make_ctx(BASE, None, rules), rules)


# (dotted, value, kind, pass). Every Row in ROWS is covered: see test_every_row_has_examples.
ROW_EXAMPLES = [
    # -- WEAKEN, gated on is_false ------------------------------------------------------------
    ("commit.gpgsign", "false", W, NONE),
    ("commit.gpgSign", "FALSE", W, NONE),
    ("commit.gpgsign", "true", U, NONE),
    ("commit.gpgsign", "", W, NONE),
    ("tag.gpgsign", "no", W, NONE),
    ("tag.gpgsign", "yes", U, NONE),
    ("http.sslVerify", "false", W, NONE),
    ("http.https://x.example/.sslverify", "off", W, NONE),
    ("http.sslverify", "true", U, NONE),
    ("http.sslverify", " 0", W, NONE),
    ("http.sslverify", "0 ", W, NONE),
    ("transfer.fsckObjects", "0", W, NONE),
    ("transfer.fsckobjects", "1", U, NONE),
    ("fetch.fsckobjects", "false", W, NONE),
    ("fetch.fsckobjects", "true", U, NONE),
    ("receive.fsckobjects", "false", W, NONE),
    ("receive.fsckobjects", "true", U, NONE),
    ("core.protectHFS", "false", W, NONE),
    ("core.protecthfs", "true", U, NONE),
    ("core.protectNTFS", "false", W, NONE),
    ("core.protectntfs", "true", U, NONE),
    # -- WEAKEN, protocol allow ----------------------------------------------------------------
    ("protocol.ext.allow", "always", W, NONE),
    ("protocol.allow", "user", W, NONE),
    ("protocol.file.allow", "never", U, NONE),
    # -- WEAKEN, hooks disabled ----------------------------------------------------------------
    ("core.hookspath", "/dev/null", W, NONE),
    # -- ROUTINE -------------------------------------------------------------------------------
    ("core.repositoryformatversion", "0", R, LIT),
    ("core.repositoryformatversion", "1", R, LIT),
    ("core.repositoryformatversion", "2", U, NONE),
    ("core.filemode", "true", R, LIT),
    ("core.bare", "", R, LIT),
    ("core.ignorecase", "Yes", R, LIT),
    ("core.sparseCheckoutCone", "maybe", U, NONE),
    ("core.logallrefupdates", "always", R, LIT),
    ("core.logallrefupdates", "true", R, LIT),
    ("core.logallrefupdates", "sometimes", U, NONE),
    ("core.fsmonitor", "true", R, LIT),
    ("core.fsmonitor", "/tmp/x", D, NONE),
    ("extensions.worktreeConfig", "true", R, LIT),
    ("extensions.relativeworktrees", "x", U, NONE),
    ("extensions.objectformat", "sha256", R, LIT),
    ("extensions.objectformat", "md5", U, NONE),
    ("extensions.refstorage", "reftable", R, LIT),
    ("extensions.refstorage", "sql", U, NONE),
    ("branch.main.remote", "origin", R, LIT),
    ("branch.main.remote", ".", R, LIT),
    ("branch.main.pushRemote", "git@github.com:o/r.git", R, LIT),
    ("branch.main.remote", "https://evil.example/x.git", X, NONE),
    ("branch.main.remote", "nosuchremote", X, NONE),
    ("branch.main.merge", "refs/heads/main", R, LIT),
    ("branch.main.merge", "main", U, NONE),
    ("branch.main.rebase", "true", R, LIT),
    ("branch.main.description", "anything at all", R, LIT),
    ("remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*", R, LIT),
    ("remote.origin.fetch", "refs/heads/main:refs/remotes/origin/main", R, LIT),
    ("remote.origin.fetch", "+refs/heads/*:refs/remotes/evil/*", U, NONE),
    ("remote.origin.fetch", "+refs/heads/*:refs/heads/*", U, NONE),
    ("remote.origin.gh-resolved", "base", R, LIT),
    ("remote.origin.gh-resolved", "owner-1/repo.x", R, LIT),
    ("remote.origin.gh-resolved", "a b", U, NONE),
    ("remote.origin.prune", "true", R, LIT),
    ("submodule.vendor/vim-plug.active", "true", R, LIT),
    ("lfs.repositoryformatversion", "0", R, LIT),
    ("lfs.repositoryformatversion", "1", U, NONE),
    ("worktrunk.default-branch", "main", R, LIT),
    ("worktrunk.history", "feature/x-1", R, LIT),
    ("worktrunk.history", "$(x)", U, NONE),
    ("worktrunk.default-branch", "-x", U, NONE),
    ("maintenance.auto", "false", R, LIT),
    ("maintenance.auto", "sh", U, NONE),
    ("index.sparse", "true", R, LIT),
    ("index.sparse", "x", U, NONE),
    ("pager.log", "false", R, LIT),
    ("pager.log", "sh -c x", D, NONE),
    # -- REDIRECT ------------------------------------------------------------------------------
    ("remote.origin.url", "https://github.com/o/r.git", X, OK),
    ("remote.origin.url", "ext::sh -c x", X, NONE),
    ("remote.origin.pushurl", "git@github.com:o/r.git", X, OK),
    ("remote.origin.pushurl", "/tmp/evil.git", X, NONE),
    ("submodule.sub.url", "https://github.com/o/s.git", X, OK),
    ("submodule.sub.url", "../s.git", X, NONE),
    ("lfs.url", "https://github.com/o/r.git/info/lfs", X, OK),
    ("lfs.url", "https://evil.example/lfs", X, NONE),
    ("core.hooksPath", ".githooks", X, OK),
    ("core.hooksPath", "/tmp/evil", X, NONE),
    ("core.worktree", "..", X, OK),
    ("core.worktree", "../../elsewhere", X, NONE),
    ("include.path", "extra.cfg", X, OK),
    ("include.path", "/tmp/evil.cfg", X, NONE),
    ("includeIf.gitdir:/r/a/.path", "/r/a/.git/extra.cfg", X, OK),
    ("includeIf.gitdir:/r/a/.path", "~/evil.cfg", X, NONE),
    ("url.https://Evil/.insteadOf", "https://github.com/", X, NONE),
    ("url.https://github.com/.pushInsteadOf", "x", X, NONE),
    ("init.templateDir", "/tmp/tpl", X, NONE),
    ("core.attributesFile", "/tmp/a", X, NONE),
    ("core.excludesfile", "/tmp/e", X, NONE),
    ("http.proxy", "http://evil.example:8080", X, NONE),
    ("http.https://github.com/.proxy", "http://evil.example:8080", X, NONE),
    ("remote.pushDefault", "origin", X, OK),
    ("remote.pushDefault", "https://evil.example/x.git", X, NONE),
    ("remote.origin.proxy", "http://evil.example:8080", X, NONE),
    ("remotes.all", "origin fork", X, NONE),
    ("submodule.sub.gitdir", "/tmp/x", X, NONE),
    ("bundle.b.uri", "https://evil.example/b", X, NONE),
    ("fetch.bundleURI", "https://evil.example/b", X, NONE),
    ("promisor.acceptFromServer", "All", X, NONE),
    ("attr.tree", "HEAD~1", X, NONE),
    ("http.sslCAInfo", "/tmp/ca.pem", X, NONE),
    ("http.curloptResolve", "github.com:443:203.0.113.1", X, NONE),
    ("gpg.ssh.allowedSignersFile", "/tmp/signers", X, NONE),
    ("sendemail.smtpSSLCertPath", "/tmp/ca", X, NONE),
    ("imap.host", "imaps://evil.example", X, NONE),
    # -- EXEC ----------------------------------------------------------------------------------
    ("hook.evil.command", "sh -c x", D, NONE),
    ("filter.x.clean", "sh -c x", D, NONE),
    ("filter.lfs.smudge", "sh -c x", D, NONE),
    ("pager.diff", "less -R", D, NONE),
    ("alias.st", "!sh -c x", D, NONE),
    ("alias.co", "checkout", U, NONE),
    ("submodule.s.update", "!sh -c x", D, NONE),
    ("submodule.s.update", "checkout", U, NONE),
    ("difftool.x.path", "/tmp/x", D, NONE),
    ("mergetool.x.path", "/tmp/x", D, NONE),
    ("man.x.path", "/tmp/x", D, NONE),
    ("browser.x.path", "/tmp/x", D, NONE),
    ("gpg.ssh.path", "/tmp/x", D, NONE),
    ("lfs.customtransfer.x.path", "/tmp/x", D, NONE),
    ("lfs.customtransfer.x.args", "-c x", D, NONE),
    ("core.pager", "sh -c x", D, NONE),
    ("core.pager", "false", D, NONE),
    ("core.editor", "x", D, NONE),
    ("core.sshCommand", "x", D, NONE),
    ("core.askPass", "x", D, NONE),
    ("core.gitProxy", "x", D, NONE),
    ("credential.helper", "!f() { :; }; f", D, NONE),
    ("credential.https://github.com.helper", "store", D, NONE),
    ("diff.external", "/tmp/x", D, NONE),
    ("diff.x.textconv", "/tmp/x", D, NONE),
    ("diff.x.command", "/tmp/x", D, NONE),
    ("merge.x.driver", "/tmp/x", D, NONE),
    ("difftool.x.cmd", "x", D, NONE),
    ("gpg.program", "/tmp/x", D, NONE),
    ("gpg.ssh.defaultKeyCommand", "x", D, NONE),
    ("remote.origin.uploadpack", "/tmp/x", D, NONE),
    ("remote.origin.receivepack", "/tmp/x", D, NONE),
    ("remote.origin.vcs", "evil", D, NONE),
    ("tar.x.command", "x", D, NONE),
    ("interactive.diffFilter", "x", D, NONE),
    ("uploadpack.packObjectsHook", "/tmp/x", D, NONE),
    ("core.alternateRefsCommand", "x", D, NONE),
    ("sequence.editor", "x", D, NONE),
    ("gc.recentobjectshook", "/tmp/x", D, NONE),
    ("sendemail.smtpServer", "/tmp/x", D, NONE),
    ("sendemail.work.smtpServerOption", "-oX", D, NONE),
    ("imap.tunnel", "sh -c x", D, NONE),
    ("instaweb.httpd", "sh -c x", D, NONE),
    ("branch.main.mergeOptions", "-s evil", D, NONE),
    ("pull.twohead", "evil", D, NONE),
    ("sendemail.ccCmd", "x", D, NONE),
    ("sendemail.work.toCmd", "x", D, NONE),
    ("advice.ignoredhook", "false", U, NONE),
    ("core.fsmonitorhookversion", "2", U, NONE),
]


@pytest.mark.parametrize(("dotted", "value", "kind", "passed"), ROW_EXAMPLES)
def test_row_examples(dotted, value, kind, passed):
    assert classify(dotted, value) == (kind, passed)


def test_every_row_has_examples():
    """Each row is hit by an example, passes and fails where it can, and has a gate-miss example when gated."""
    rules = default_rules()
    ctx = make_ctx(BASE, None, rules)
    hit, passed, failed, gate_missed = set(), set(), set(), set()
    for dotted, value, _, _ in ROW_EXAMPLES:
        key = ConfigKey.parse(dotted)
        row = match_row(key, value)
        for named in rows_for_key(key):
            if named.when is not None and named is not row and ROWS.index(named) < (
                ROWS.index(row) if row is not None else len(ROWS)
            ):
                gate_missed.add(named)
        if row is None:
            continue
        hit.add(row)
        _, how = classify_entry(entry(dotted, value), ctx, rules)
        (failed if how is Pass.NONE else passed).add(row)
    for row in ROWS:
        assert row in hit, row.doc
        if row.value_check not in ("never", "template"):
            assert row in passed, f"no passing example: {row.doc}"
        if row.value_check != "any" and row.value_check != row.when:
            assert row in failed, f"no failing example: {row.doc}"
        if row.when is not None:
            assert row in gate_missed, f"no gate-miss example: {row.doc}"


def test_rows_ordered_weaken_routine_redirect_exec():
    order = [Kind.WEAKEN, Kind.ROUTINE, Kind.REDIRECT, Kind.EXEC]
    ranks = [order.index(row.kind) for row in ROWS]
    assert ranks == sorted(ranks)
    for row in ROWS:
        if row.kind is Kind.WEAKEN:
            assert row.when is not None and row.value_check == "never", row.doc
        assert row.doc


def test_mixed_case_keys_classify_like_lowercase():
    assert classify("Core.HooksPath", "/dev/null") == (W, NONE)
    assert classify("CORE.FSMONITOR", "/tmp/x") == (D, NONE)
    assert classify("Remote.origin.URL", "ext::sh -c x") == (X, NONE)


def test_url_rejects_transport_and_paths():
    rules = default_rules()
    ctx = make_ctx(surface(), None, rules)
    assert ctx.hosts == frozenset({"github.com"})

    def url(value):
        return classify_entry(entry("remote.origin.url", value), ctx, rules)

    for bad in (
        "ext::sh -c x",
        "fd::17",
        "file:///tmp/x",
        "/tmp/x.git",
        "-uhttps://github.com/a/b",
        "https://evil.example/x.git",
        "ssh://-oProxyCommand=x@github.com/a/b",
        "ssh://github.com:22/a b",
        "../x.git",
        "github.com:a/b",
    ):
        assert url(bad) == (X, NONE), bad
    for good in (
        "git@github.com:a/b.git",
        "https://github.com/a/b.git",
        "ssh://git@github.com:22/a/b.git",
        "git://GitHub.com/a/b",
    ):
        assert url(good) == (X, OK), good


def test_hookspath_relative_tracked_passes():
    rules = default_rules()
    s = surface(toplevels=["/r/a"], tracked_dirs=["/r/a/.githooks"])
    e = entry("core.hookspath", ".githooks")
    assert classify_entry(e, make_ctx(s, None, rules), rules) == (X, OK)
    assert resolve_redirect(e, make_ctx(s, None, rules)) == (PurePosixPath("/r/a/.githooks"),)


def test_hookspath_escape_fails():
    rules = default_rules()
    s = surface(toplevels=["/r/a"], tracked_dirs=["/r/a/.githooks"])
    e = entry("core.hookspath", "../../evil")
    assert classify_entry(e, make_ctx(s, None, rules), rules) == (X, NONE)


def test_hookspath_untracked_inside_toplevel_fails():
    rules = default_rules()
    s = surface(toplevels=["/r/a"], tracked_dirs=["/r/a/.githooks"])
    for value in (".git/hooks", "untracked", "~/hooks", "~other/hooks", "%(prefix)/hooks"):
        e = entry("core.hookspath", value)
        assert classify_entry(e, make_ctx(s, None, rules), rules) == (X, NONE), value


def test_hookspath_must_stay_inside_every_toplevel():
    """A relative path that resolves into one tracked dir but escapes another worktree still fails."""
    rules = default_rules()
    s = surface(toplevels=["/r/a", "/r/w/deep"], tracked_dirs=["/r/a/.githooks"])
    e = entry("core.hookspath", "../a/.githooks")
    # /r/a/../a/.githooks stays in /r/a; /r/w/deep/../a/.githooks escapes /r/w/deep.
    assert classify_entry(e, make_ctx(s, None, rules), rules) == (X, NONE)


def test_hookspath_absolute_rewrite_same_target_passes():
    rules = default_rules()
    admin = MemberRef(PurePosixPath("/r/a/.git/worktrees/w"), "admin")
    e = entry(
        "core.hookspath",
        "/r/a/.githooks",
        file="/r/a/.git/worktrees/w/config.worktree",
        member=admin,
        scope="worktree",
    )
    s = surface([e], toplevels=["/r/a", "/r/w"], tracked_dirs=["/r/a/.githooks"])
    assert classify_entry(e, make_ctx(s, None, rules), rules) == (X, OK)


def test_hookspath_respelled_same_as_lkg_passes():
    """Same resolved targets as the LKG value from the same file pass even when untracked."""
    rules = default_rules()
    s = surface(toplevels=["/r/a"], tracked_dirs=[])
    old = entry("core.hookspath", "hooks")
    new = entry("core.hookspath", "/r/a/./hooks")
    lkg = Lkg(ANCHOR, PurePosixPath("/r/a/.git"), {"k": old}, Fingerprint.EMPTY, False)
    assert classify_entry(new, make_ctx(s, lkg, rules), rules) == (X, OK)
    other_file = entry("core.hookspath", "/r/a/./hooks", file="/r/a/.git/config.worktree")
    assert classify_entry(other_file, make_ctx(s, lkg, rules), rules) == (X, NONE)
    assert classify_entry(new, make_ctx(s, None, rules), rules) == (X, NONE)


_MOD_CFG = {"member": MODULE, "file": "/r/a/.git/modules/sub/config", "scope": "module"}


def _module_hookspath(value: str, worktrees: list[str], tracked: list[str]):
    rules = default_rules()
    hp = entry("core.hooksPath", value, **_MOD_CFG)
    wts = [entry("core.worktree", w, **_MOD_CFG) for w in worktrees]
    s = surface([entry("core.hooksPath", ".githooks"), *wts, hp], tracked_dirs=tracked)
    ctx = make_ctx(s, None, rules)
    return classify_entry(hp, ctx, rules), resolve_redirect(hp, ctx)


def test_module_hookspath_resolves_against_its_own_worktree():
    """git runs a submodule's hooks from the submodule's worktree, so `.githooks` there is
    /r/a/sub/.githooks. The superproject tracking /r/a/.githooks says nothing about it."""
    got, targets = _module_hookspath(".githooks", ["../../../sub"], ["/r/a/.githooks"])
    assert got == (X, NONE)
    assert targets == (PurePosixPath("/r/a/sub/.githooks"),)


def test_module_hookspath_passes_when_its_own_dir_is_tracked():
    got, _ = _module_hookspath(".githooks", ["../../../sub"], ["/r/a/.githooks", "/r/a/sub/.githooks"])
    assert got == (X, OK)


def test_module_hookspath_must_stay_inside_its_worktree():
    got, _ = _module_hookspath("../.githooks", ["../../../sub"], ["/r/a/.githooks", "/r/a/sub/.githooks"])
    assert got == (X, NONE)


@pytest.mark.parametrize("worktrees", [[], ["../../../sub", "../../../other"], ["../../../x/../sub"]])
def test_module_hookspath_without_one_clear_worktree_fails_closed(worktrees):
    """No core.worktree, two different ones, or one git would read through a symlink: unresolvable."""
    got, targets = _module_hookspath(".githooks", worktrees, ["/r/a/.githooks", "/r/a/sub/.githooks"])
    assert got == (X, NONE)
    assert targets == ()


def test_core_worktree_under_superproject():
    rules = default_rules()
    ctx = make_ctx(surface(), None, rules)

    def wt(value):
        e = entry("core.worktree", value, member=MODULE, file="/r/a/.git/modules/sub/config",
                  scope="module")
        return classify_entry(e, ctx, rules)

    assert wt("../../../sub") == (X, OK)
    assert wt("../../../../elsewhere") == (X, NONE)
    assert wt("/tmp/x") == (X, NONE)


def test_include_path_resolves_against_including_file():
    rules = default_rules()
    s = surface(toplevels=["/r/a"], home="/r/a/.git")
    ctx = make_ctx(s, None, rules)
    assert resolve_redirect(entry("include.path", "../x.cfg"), ctx) == (PurePosixPath("/r/a/x.cfg"),)
    assert classify_entry(entry("include.path", "../x.cfg"), ctx, rules) == (X, NONE)
    assert classify_entry(entry("include.path", "~/x.cfg"), ctx, rules) == (X, OK)


def test_hosts_come_from_lkg_when_present():
    rules = default_rules()
    cur_url = entry("remote.origin.url", "https://gitlab.example/x.git")
    cur = surface([cur_url])
    lkg = Lkg(
        ANCHOR,
        PurePosixPath("/r/a/.git"),
        {"k": entry("remote.origin.url", "git@github.com:o/r.git")},
        Fingerprint.EMPTY,
        False,
    )
    assert classify_entry(cur_url, make_ctx(cur, lkg, rules), rules) == (X, NONE)
    # Without an LKG the current URLs define the host set, so the same entry passes.
    assert classify_entry(cur_url, make_ctx(cur, None, rules), rules) == (X, OK)


def test_make_ctx_collects_remotes_and_hosts():
    rules = default_rules()
    s = surface([
        entry("remote.origin.url", "git@gitlab.example:o/r.git"),
        entry("remote.fork.pushurl", "ssh://git@code.example:2222/o/r.git"),
        entry("submodule.s.url", "https://subs.example/o/s.git"),
        entry("remote.bad.url", "ext::sh -c x"),
        entry("lfs.url", "https://lfs.example/x"),
    ])
    ctx = make_ctx(s, None, rules)
    # Only names with a remote.<r>.url count: `fork` has just a pushurl. Keyed by member git_dir.
    assert ctx.remotes == {PurePosixPath("/r/a/.git"): frozenset({"origin", "bad"})}
    assert ctx.hosts == frozenset(
        {"github.com", "gitlab.example", "code.example", "subs.example"}
    )


# -- git help --config review --------------------------------------------------------------------

_VAR_LINE = re.compile(
    r"^[A-Za-z][A-Za-z0-9-]*(?:\.\S+)?\.(?:\*|<[^>]+>|[A-Za-z][A-Za-z0-9_-]*)$"
)
# Lines of git-help-config.txt that are not config vars, skipped by _VAR_LINE: the version header,
# the blank separator, git's trailer, and an includeIf *condition* (not a var: the var is
# `includeIf.<condition>.path`, which is listed separately).
_EXPECTED_SKIPPED = [
    "# git 2.54.0",
    "hasconfig:remote.*.url",
    "",
    "'git help config' for more information",
]
_SUSPICIOUS = re.compile(
    r"(cmd|command|program|hook|helper|driver|editor|pager|proxy|askpass|textconv|external|filter"
    r"|sshcommand)",
    re.IGNORECASE,
)


def _help_vars() -> tuple[list[str], list[str]]:
    lines = (FIXTURES / "git-help-config.txt").read_text().splitlines()
    kept = [line for line in lines if _VAR_LINE.match(line)]
    skipped = [line for line in lines if not _VAR_LINE.match(line)]
    return kept, skipped


def _placeholder_key(var: str) -> ConfigKey:
    return ConfigKey.parse(re.sub(r"<[^>]+>|(?<=\.)\*(?=\.|$)", "x", var))


def _reviewed() -> dict[str, str]:
    out = {}
    for line in (FIXTURES / "reviewed_unknown.txt").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        var, _, comment = line.partition("#")
        out[var.strip()] = comment.strip()
    return out


def test_git_help_config_skips_only_known_non_vars():
    _, skipped = _help_vars()
    assert skipped == _EXPECTED_SKIPPED


def test_git_help_config_fully_reviewed():
    kept, _ = _help_vars()
    reviewed = _reviewed()
    missing = [v for v in kept if not rows_for_key(_placeholder_key(v)) and v not in reviewed]
    assert missing == []
    for var, comment in reviewed.items():
        if _SUSPICIOUS.search(var):
            assert re.match(r"^reviewed: \S", comment), f"{var} needs '# reviewed: <reason>'"


def test_reviewed_unknown_has_no_stale_entries():
    kept, _ = _help_vars()
    for var in _reviewed():
        assert var in kept, f"{var} is not in git-help-config.txt"
        assert not rows_for_key(_placeholder_key(var)), f"{var} now has a row; drop it from the list"


# -- Fix round 1: hostile shapes -----------------------------------------------------------------

_ORIGIN = entry("remote.origin.url", "https://github.com/o/r.git")
_LKG = Lkg(ANCHOR, PurePosixPath("/r/a/.git"), {"k": _ORIGIN}, Fingerprint.EMPTY, False)


@pytest.mark.parametrize("phantom", ["../evil", "git@evil.example:x", "/tmp/evil"])
@pytest.mark.parametrize("lkg", [None, _LKG], ids=["no-lkg", "lkg"])
@pytest.mark.parametrize("dotted", ["branch.main.remote", "branch.main.pushremote",
                                    "remote.pushDefault"])
def test_phantom_remote_name_is_checked_as_url(phantom, lkg, dotted):
    """A URL-less remote's name is used as its URL, so a remote known only from
    remote.<r>.prune (or any non-url var) is not a remote name."""
    rules = default_rules()
    plant = entry(f"remote.{phantom}.prune", "true")
    pointer = entry(dotted, phantom)
    ctx = make_ctx(surface([_ORIGIN, plant, pointer]), lkg, rules)
    assert phantom not in ctx.remotes[COMMON.git_dir]
    assert classify_entry(pointer, ctx, rules) == (X, NONE)
    assert classify_entry(entry(dotted, "origin"), ctx, rules)[1] is not NONE


@pytest.mark.parametrize(
    ("dotted", "value", "kw"),
    [
        ("core.hookspath", "sym/../.githooks", {}),
        ("core.hookspath", "/r/a/sym/../.githooks", {}),
        ("core.hookspath", "../a/sym/../.githooks", {}),
        ("include.path", "sym/../extra.cfg", {}),
        ("includeIf.gitdir:/r/a/.path", "/r/a/.git/sym/../extra.cfg", {}),
        ("core.worktree", "sym/../..", {}),
        ("core.worktree", "../../../x/../sub",
         {"member": MODULE, "file": "/r/a/.git/modules/sub/config", "scope": "module"}),
    ],
)
def test_dotdot_after_a_segment_fails(dotted, value, kw):
    """`sym/..` normalizes away purely, but git follows the symlink first."""
    rules = default_rules()
    s = surface([entry("submodule.sub.active", "true", member=MODULE,
                       file="/r/a/.git/modules/sub/config", scope="module")],
                toplevels=["/r/a"], tracked_dirs=["/r/a/.githooks"])
    assert classify_entry(entry(dotted, value, **kw), make_ctx(s, None, rules), rules) == (X, NONE)


def test_leading_dotdot_still_allowed():
    rules = default_rules()
    s = surface([entry("submodule.sub.active", "true", member=MODULE,
                       file="/r/a/.git/modules/sub/config", scope="module")],
                toplevels=["/r/a"], tracked_dirs=["/r/a/.githooks"])
    ctx = make_ctx(s, None, rules)
    inc = entry("include.path", "../../config.extra", member=MODULE,
                file="/r/a/.git/modules/sub/config", scope="module")
    assert classify_entry(inc, ctx, rules) == (X, OK)  # /r/a/.git/config.extra
    sub = entry("core.worktree", "../../../sub", member=MODULE,
                file="/r/a/.git/modules/sub/config", scope="module")
    assert classify_entry(sub, ctx, rules) == (X, OK)
    assert classify_entry(entry("core.hookspath", "./.githooks"), ctx, rules) == (X, OK)


@pytest.mark.parametrize("value", [".", "", "./", "hooks", "/r/a/.git", "../.git/modules/sub"])
def test_core_worktree_inside_a_git_dir_fails(value):
    rules = default_rules()
    s = surface([entry("submodule.sub.active", "true", member=MODULE,
                       file="/r/a/.git/modules/sub/config", scope="module")])
    e = entry("core.worktree", value)
    assert classify_entry(e, make_ctx(s, None, rules), rules) == (X, NONE)


# -- Fix round 2: remote names are scoped to the config view that reads the pointer ---------------

ADMIN = MemberRef(PurePosixPath("/r/a/.git/worktrees/w"), "admin")
_WHERE = {
    "common": {},
    "main-wt": {"file": "/r/a/.git/config.worktree", "scope": "worktree"},
    "module": {"member": MODULE, "file": "/r/a/.git/modules/sub/config", "scope": "module"},
    "admin": {"member": ADMIN, "file": "/r/a/.git/worktrees/w/config.worktree",
              "scope": "worktree"},
}


@pytest.mark.parametrize(
    ("url_in", "pointer_in", "passes"),
    [
        ("module", "common", False),  # git never reads a submodule's config from the superproject
        ("admin", "common", False),  # a url only one worktree sees never validates common config
        ("main-wt", "common", False),  # main's config.worktree is not read by linked worktrees
        ("common", "common", True),
        ("common", "admin", True),  # a worktree reads common config plus its own config.worktree
        ("admin", "admin", True),
        ("module", "module", True),
        ("common", "module", False),
        ("admin", "module", False),
    ],
)
@pytest.mark.parametrize("lkg", [None, _LKG], ids=["no-lkg", "lkg"])
@pytest.mark.parametrize("dotted", ["branch.main.remote", "branch.main.pushremote",
                                    "remote.pushDefault"])
def test_remote_names_scoped_to_reading_member(url_in, pointer_in, passes, lkg, dotted):
    rules = default_rules()
    url = entry("remote.../evil.url", "https://github.com/o/r.git", **_WHERE[url_in])
    pointer = entry(dotted, "../evil", **_WHERE[pointer_in])
    s = surface([_ORIGIN, url, pointer], toplevels=["/r/a", "/r/w"])
    got = classify_entry(pointer, make_ctx(s, lkg, rules), rules)
    if not passes:
        assert got == (X, NONE)
    elif dotted == "remote.pushDefault":
        assert got == (X, OK)
    else:
        assert got == (R, LIT)

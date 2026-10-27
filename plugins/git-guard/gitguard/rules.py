"""The config-key classifier table and its value checks.

Pure module: no IO. Path math is `PurePosixPath` and `posixpath.normpath` only.

Each config entry is matched against the rows by name (section, subsection, variable), then by
an optional value gate (`when`). The first row that applies wins, and its `value_check` decides
whether the entry passed. Rows are ordered WEAKEN, ROUTINE, REDIRECT, EXEC, so a when-gated
WEAKEN or bool-valued ROUTINE row shadows the broader row behind it.
"""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Callable, Mapping, Optional, Sequence

from gitguard.model import ConfigEntry, ConfigKey, Kind, Lkg, Pass, RuleSet, Surface

if TYPE_CHECKING:
    from gitguard.templates import Templates


@dataclass(frozen=True)
class Row:
    """One table row.

    section: lowercase section, or "*" for any.
    subsection: None means the key must have none; "*" means any or none; a string ending in
        "*" is a case-insensitive prefix (`customtransfer.*`); any other string matches exactly.
    variables: lowercase variable names, or {"*"} for any. Ignored when var_regex is set.
    var_regex: searched against the lowercase variable instead of `variables`.
    when: a value predicate gating whether the row applies at all. Must be value-only.
    value_check: the predicate the value must pass once the row applies.
    on_fail: the Kind reported when value_check fails.
    """

    kind: Kind
    section: str
    subsection: Optional[str]
    variables: frozenset[str]
    var_regex: Optional[str]
    when: Optional[str]
    value_check: str
    on_fail: Kind
    doc: str


@dataclass(frozen=True)
class ClassifyCtx:
    surface: Surface
    lkg: Optional[Lkg]
    remotes: frozenset[str]  # every <r> in remote.<r>.* of the current surface
    hosts: frozenset[str]  # lowercase hosts a URL may point at


@dataclass(frozen=True)
class CheckEnv:
    """What a context-dependent value check sees besides the value."""

    entry: ConfigEntry
    ctx: ClassifyCtx
    rules: RuleSet


Predicate = Callable[[str, Optional[CheckEnv]], bool]


# -- Table --------------------------------------------------------------------------------------

W, R, X, D, U = Kind.WEAKEN, Kind.ROUTINE, Kind.REDIRECT, Kind.EXEC, Kind.UNKNOWN


def _v(*names: str) -> frozenset[str]:
    return frozenset(names)


ANY = _v("*")

# Variables that name a program, a command line, or a hook, in any section. `fsmonitor` and
# `pager` are here too: their bool-valued forms are caught first by ROUTINE rows.
EXEC_VARIABLES = _v(
    "command", "cmd", "driver", "clean", "smudge", "process", "textconv", "program", "helper",
    "pager", "editor", "sshcommand", "askpass", "gitproxy", "external", "packobjectshook", "vcs",
    "uploadpack", "receivepack", "difffilter", "defaultkeycommand", "alternaterefscommand",
    "fsmonitor",
)

# Field order: kind, section, subsection, variables, var_regex, when, value_check, on_fail, doc.
ROWS: tuple[Row, ...] = (
    # -- WEAKEN: integrity downgrades. Gated on the downgrading value; never pass. ---------------
    Row(W, "commit", None, _v("gpgsign"), None, "is_false", "never", W,
        "commit.gpgSign=false stops signing commits"),
    Row(W, "tag", None, _v("gpgsign"), None, "is_false", "never", W,
        "tag.gpgSign=false stops signing tags"),
    Row(W, "http", "*", _v("sslverify"), None, "is_false", "never", W,
        "http[.<url>].sslVerify=false accepts any TLS certificate"),
    Row(W, "transfer", None, _v("fsckobjects"), None, "is_false", "never", W,
        "transfer.fsckObjects=false skips object checks on fetch and push"),
    Row(W, "fetch", None, _v("fsckobjects"), None, "is_false", "never", W,
        "fetch.fsckObjects=false skips object checks on fetch"),
    Row(W, "receive", None, _v("fsckobjects"), None, "is_false", "never", W,
        "receive.fsckObjects=false skips object checks on push"),
    Row(W, "core", None, _v("protecthfs"), None, "is_false", "never", W,
        "core.protectHFS=false allows HFS+ .git aliases in paths"),
    Row(W, "core", None, _v("protectntfs"), None, "is_false", "never", W,
        "core.protectNTFS=false allows NTFS .git aliases in paths"),
    Row(W, "protocol", "*", _v("allow"), None, "in:always,user", "never", W,
        "protocol[.<name>].allow=always|user widens which transports git will use"),
    Row(W, "core", None, _v("hookspath"), None, "eq:/dev/null", "never", W,
        "core.hooksPath=/dev/null disables every hook"),
    # -- ROUTINE: what git, worktrunk and gh write in normal use. -------------------------------
    Row(R, "core", None, _v("repositoryformatversion"), None, None, "in:0,1", U,
        "repository format version"),
    Row(R, "core", None,
        _v("filemode", "bare", "ignorecase", "precomposeunicode", "symlinks", "longpaths",
           "sparsecheckout", "sparsecheckoutcone"),
        None, None, "bool", U, "core bool flags written by init/clone"),
    Row(R, "core", None, _v("logallrefupdates"), None, None, "bool_or:always", U,
        "reflog policy"),
    Row(R, "core", None, _v("fsmonitor"), None, "bool", "bool", D,
        "core.fsmonitor as a bool selects the builtin daemon; any other value is a command"),
    Row(R, "extensions", None, _v("worktreeconfig", "relativeworktrees"), None, None, "bool", U,
        "repository extensions (bool)"),
    Row(R, "extensions", None, _v("objectformat"), None, None, "in:sha1,sha256", U,
        "object hash"),
    Row(R, "extensions", None, _v("refstorage"), None, None, "in:files,reftable", U,
        "ref backend"),
    Row(R, "branch", "*", _v("remote", "pushremote"), None, None, "remote_name_or_url", X,
        "branch upstream remote: a configured remote name, '.', or a URL to a known host"),
    Row(R, "branch", "*", _v("merge"), None, None, "prefix:refs/", U, "branch upstream ref"),
    Row(R, "branch", "*", _v("rebase", "description", "gh-merge-base", "vscode-merge-base"),
        None, None, "any", U, "branch metadata"),
    Row(R, "remote", "*", _v("fetch"), None, None, "fetch_refspec", U,
        "fetch refspec into this remote's own refs/remotes namespace"),
    Row(R, "remote", "*", _v("gh-resolved"), None, None, "gh_resolved", U,
        "gh CLI's default-repo marker"),
    Row(R, "remote", "*", _v("tagopt", "prune", "prunetags"), None, None, "any", U,
        "remote fetch options"),
    Row(R, "submodule", "*", _v("active", "branch", "ignore", "fetchrecursesubmodules", "shallow"),
        None, None, "any", U, "submodule options"),
    Row(R, "lfs", None, _v("repositoryformatversion"), None, None, "in:0", U,
        "git-lfs repository format version"),
    Row(R, "worktrunk", None, _v("default-branch", "history"), None, None, "refname", U,
        "worktrunk branch bookkeeping"),
    Row(R, "maintenance", None, _v("auto"), None, None, "bool", U, "maintenance.auto"),
    Row(R, "index", None, _v("sparse"), None, None, "bool", U, "index.sparse"),
    Row(R, "pager", "*", ANY, None, "bool", "bool", D,
        "pager.<cmd> as a bool turns paging on or off; any other value is a pager command"),
    # -- REDIRECT: point git at another repo, path or proxy. ------------------------------------
    Row(X, "remote", "*", _v("url", "pushurl"), None, None, "url", X, "remote URL"),
    Row(X, "submodule", "*", _v("url"), None, None, "url", X, "submodule URL"),
    Row(X, "lfs", "*", _v("url", "pushurl"), None, None, "url", X, "git-lfs endpoint"),
    Row(X, "core", None, _v("hookspath"), None, None, "hooks_path", X,
        "core.hooksPath: hooks dir, must be a tracked dir inside the worktree"),
    Row(X, "core", None, _v("worktree"), None, None, "worktree_path", X,
        "core.worktree: must stay inside the anchor"),
    Row(X, "include", None, _v("path"), None, None, "include_path", X,
        "include.path: must stay inside a git dir"),
    Row(X, "includeif", "*", _v("path"), None, None, "include_path", X,
        "includeIf.<cond>.path: must stay inside a git dir"),
    Row(X, "url", "*", _v("insteadof", "pushinsteadof"), None, None, "never", X,
        "URL rewriting"),
    Row(X, "init", None, _v("templatedir"), None, None, "never", X,
        "init.templateDir: templates (hooks included) copied into new repos"),
    Row(X, "core", None, _v("attributesfile", "excludesfile"), None, None, "never", X,
        "out-of-repo attributes/excludes file (attributes can name filter drivers)"),
    Row(X, "http", "*", _v("proxy"), None, None, "never", X, "HTTP proxy"),
    # Added in the `git help --config` review (tests/fixtures/reviewed_unknown.txt):
    Row(X, "remote", None, _v("pushdefault"), None, None, "remote_name_or_url", X,
        "remote.pushDefault: default push remote, a name or a URL"),
    Row(X, "remote", "*", _v("proxy"), None, None, "never", X, "per-remote proxy"),
    Row(X, "remotes", None, ANY, None, None, "never", X,
        "remotes.<group>: remotes fetched by `git remote update`; members may be URLs"),
    Row(X, "submodule", "*", _v("gitdir"), None, None, "never", X,
        "submodule.<name>.gitdir: where the submodule's git dir lives"),
    Row(X, "bundle", "*", _v("uri"), None, None, "never", X,
        "bundle.<id>.uri: a bundle git downloads objects from"),
    Row(X, "fetch", None, _v("bundleuri"), None, None, "never", X,
        "fetch.bundleURI: a bundle list git downloads before fetching"),
    Row(X, "promisor", None, _v("acceptfromserver"), None, None, "never", X,
        "promisor.acceptFromServer: lets the server add promisor remotes"),
    Row(X, "attr", None, _v("tree"), None, None, "never", X,
        "attr.tree: attributes (which name filter drivers) read from another tree"),
    Row(X, "http", "*", _v("curloptresolve", "sslcainfo", "sslcapath", "proxysslcainfo"), None,
        None, "never", X, "DNS pinning and TLS trust roots"),
    Row(X, "gpg", "*", _v("allowedsignersfile", "revocationfile"), None, None, "never", X,
        "ssh signature trust files: who counts as a valid signer"),
    Row(X, "sendemail", "*", _v("smtpsslcertpath"), None, None, "never", X,
        "send-email TLS trust root"),
    Row(X, "imap", None, _v("host"), None, None, "never", X, "imap-send destination"),
    # -- EXEC: git runs the value, or something it names. ---------------------------------------
    Row(D, "hook", "*", ANY, None, None, "template", D,
        "config-defined hooks (hook.<name>.command/event): only installer templates pass"),
    Row(D, "filter", "*", ANY, None, None, "template", D,
        "filter drivers (clean/smudge/process): only installer templates pass"),
    Row(D, "pager", "*", ANY, None, None, "never", D, "pager.<cmd> command"),
    Row(D, "alias", "*", ANY, None, "prefix:!", "never", D, "shell alias"),
    Row(D, "submodule", "*", _v("update"), None, "prefix:!", "never", D,
        "submodule.<name>.update=!command"),
    Row(D, "difftool", "*", _v("path"), None, None, "never", D, "difftool binary"),
    Row(D, "mergetool", "*", _v("path"), None, None, "never", D, "mergetool binary"),
    Row(D, "man", "*", _v("path"), None, None, "never", D, "man viewer binary"),
    Row(D, "browser", "*", _v("path"), None, None, "never", D, "browser binary"),
    Row(D, "gpg", "*", _v("path"), None, None, "never", D, "gpg binary"),
    Row(D, "lfs", "customtransfer.*", ANY, None, None, "never", D,
        "git-lfs custom transfer agent (path, args)"),
    Row(D, "*", "*", EXEC_VARIABLES, None, None, "never", D,
        "variable that names a program or a command line"),
    # Added in the `git help --config` review (tests/fixtures/reviewed_unknown.txt):
    Row(D, "sendemail", "*", _v("smtpserver", "smtpserveroption"), None, None, "never", D,
        "sendemail.smtpServer: an absolute path is run as sendmail; smtpServerOption is its argv"),
    Row(D, "imap", None, _v("tunnel"), None, None, "never", D, "imap.tunnel: a command line"),
    Row(D, "instaweb", None, _v("httpd", "modulepath"), None, None, "never", D,
        "instaweb.httpd: a command line; instaweb.modulePath: modules the httpd loads"),
    Row(D, "branch", "*", _v("mergeoptions"), None, None, "never", D,
        "branch.<name>.mergeOptions: `-s <strategy>` runs git-merge-<strategy>"),
    Row(D, "pull", None, _v("twohead", "octopus"), None, None, "never", D,
        "pull.twohead/octopus: a merge strategy, run as git-merge-<strategy>"),
    Row(D, "*", "*", frozenset(), r"(cmd|command)$", None, "never", D,
        "variable ending in cmd/command (sendemail.ccCmd, sendemail.toCmd, ...)"),
    Row(D, "*", "*", frozenset(), r"^(?!ignoredhook$).*hook$", None, "never", D,
        "variable ending in 'hook' (uploadpack.packObjectsHook, gc.recentObjectsHook, ...); "
        "advice.ignoredHook is excluded, and core.fsmonitorHookVersion does not end in 'hook'"),
)

_PASS_FOR = {Kind.ROUTINE: Pass.LITERAL, Kind.REDIRECT: Pass.VALUE_OK, Kind.EXEC: Pass.TEMPLATE}


# -- Name matching ------------------------------------------------------------------------------


def _subsection_matches(pattern: Optional[str], sub: Optional[str]) -> bool:
    if pattern is None:
        return sub is None
    if pattern == "*":
        return True
    if sub is None:
        return False
    if pattern.endswith("*"):
        return sub.lower().startswith(pattern[:-1].lower())
    return sub == pattern


def _names(row: Row, key: ConfigKey) -> bool:
    if row.section != "*" and row.section != key.section:
        return False
    if not _subsection_matches(row.subsection, key.subsection):
        return False
    if row.var_regex is not None:
        return re.search(row.var_regex, key.variable) is not None
    return "*" in row.variables or key.variable in row.variables


def rows_for_key(key: ConfigKey) -> tuple[Row, ...]:
    """Every row whose name pattern matches `key`, ignoring `when`."""
    return tuple(row for row in ROWS if _names(row, key))


def _first(rows: Sequence[Row], key: ConfigKey, value: str) -> Optional[Row]:
    for row in rows:
        if _names(row, key) and (row.when is None or predicate(row.when)(value, None)):
            return row
    return None


def match_row(key: ConfigKey, value: str) -> Optional[Row]:
    """The first row of `ROWS` that names `key` and whose `when` gate admits `value`."""
    return _first(ROWS, key, value)


# -- Paths --------------------------------------------------------------------------------------


def _norm(path: PurePosixPath) -> PurePosixPath:
    return PurePosixPath(posixpath.normpath(str(path)))


def _inside(path: PurePosixPath, root: PurePosixPath) -> bool:
    return path == root or root in path.parents


def _dotdot_after_segment(value: str) -> bool:
    """True when a `..` follows a real segment (`sym/..`). Pure normpath would cancel the pair, but
    git follows `sym` first if it is a symlink. Leading runs of `..` (`../../sub`) are fine."""
    seen_real = False
    for seg in value.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if seen_real:
                return True
        else:
            seen_real = True
    return False


def _expand(value: str, home: PurePosixPath) -> Optional[PurePosixPath]:
    """git's pathname expansion, as far as we can follow it purely. `~user/` and `%(prefix)/`
    are unresolvable here, so the caller treats them as failing."""
    if value == "~":
        return home
    if value.startswith("~/"):
        return home / value[2:]
    if value.startswith("~") or value.startswith("%("):
        return None
    return PurePosixPath(value)


def _hooks_targets(
    value: str, surface: Surface
) -> Optional[list[tuple[PurePosixPath, tuple[PurePosixPath, ...]]]]:
    """(resolved target, toplevels it must stay inside) per resolution, or None if unresolvable.
    An absolute (or `~/`) path resolves once and may sit in any toplevel; a relative one resolves
    once per toplevel and must stay inside that toplevel."""
    path = _expand(value, surface.home)
    if path is None:
        return None
    if path.is_absolute():
        return [(_norm(path), surface.toplevels)]
    return [(_norm(top / path), (top,)) for top in surface.toplevels]


def _worktree_target(entry: ConfigEntry, surface: Surface) -> Optional[PurePosixPath]:
    path = _expand(entry.value, surface.home)
    return None if path is None else _norm(entry.member.git_dir / path)


def _include_target(entry: ConfigEntry, surface: Surface) -> Optional[PurePosixPath]:
    path = _expand(entry.value, surface.home)
    return None if path is None else _norm(entry.file.parent / path)


_HOOKSPATH = ConfigKey("core", None, "hookspath")


def resolve_redirect(entry: ConfigEntry, ctx: ClassifyCtx) -> tuple[PurePosixPath, ...]:
    """Resolved targets of a path-valued redirect (core.hooksPath, core.worktree, include paths).
    Empty for any other key, or when the value cannot be resolved purely."""
    key = entry.key
    if key == _HOOKSPATH:
        pairs = _hooks_targets(entry.value, ctx.surface)
        return () if pairs is None else tuple(target for target, _ in pairs)
    if key == ConfigKey("core", None, "worktree"):
        one = _worktree_target(entry, ctx.surface)
    elif key.variable == "path" and (
        (key.section == "include" and key.subsection is None) or key.section == "includeif"
    ):
        one = _include_target(entry, ctx.surface)
    else:
        return ()
    return () if one is None else (one,)


# -- URLs ---------------------------------------------------------------------------------------

_HOST = r"(?P<host>[A-Za-z0-9][A-Za-z0-9.-]*)"
_SCP_URL = re.compile(r"[A-Za-z0-9._~+][A-Za-z0-9._~+-]*@" + _HOST + r":\S+")
_SCHEME_URL = re.compile(
    r"(?:https|ssh|git)://(?:[A-Za-z0-9._~%+][A-Za-z0-9._~%+:-]*@)?" + _HOST
    + r"(?::[0-9]+)?/\S*",
    re.IGNORECASE,
)


def url_host(value: str) -> Optional[str]:
    """The lowercase host of an accepted URL shape, or None. Accepted: scp-like `user@host:path`
    and `https|ssh|git://[user@]host[:port]/...`. Transport helpers (`::`), `file:`, option
    injection (leading `-`), whitespace and bare paths are never accepted."""
    if value.startswith("-") or "::" in value or value.lower().startswith("file:"):
        return None
    match = _SCP_URL.fullmatch(value) or _SCHEME_URL.fullmatch(value)
    return match["host"].lower() if match else None


def _is_url_key(key: ConfigKey) -> bool:
    if key.subsection is None:
        return False
    if key.section == "remote":
        return key.variable in ("url", "pushurl")
    return key.section == "submodule" and key.variable == "url"


# -- Value predicates ---------------------------------------------------------------------------

_BOOL_WORDS = frozenset({"true", "false", "yes", "no", "on", "off", "0", "1", ""})
_FALSE_WORDS = frozenset({"false", "no", "off"})
# git_parse_maybe_bool falls back to git_parse_int (strtoimax base 0, unit suffix), so "00",
# "0x0" and "0k" are all false too.
_ZERO = re.compile(r"\s*[+-]?(?:0x0+|0+)[kmg]?\s*", re.IGNORECASE)
_REFNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/@+-]*")
_OWNER_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def _env(env: Optional[CheckEnv]) -> CheckEnv:
    if env is None:
        raise ValueError("this predicate needs an entry and a context; it cannot be a `when` gate")
    return env


def _is_false(value: str, _: Optional[CheckEnv]) -> bool:
    """git_parse_maybe_bool: an explicit empty value is false, and so is any integer zero
    (strtoimax skips leading whitespace; trailing whitespace is accepted too, to be safe)."""
    return value == "" or value.lower() in _FALSE_WORDS or _ZERO.fullmatch(value) is not None


def _bool(value: str, _: Optional[CheckEnv]) -> bool:
    return value.lower() in _BOOL_WORDS


def _url(value: str, env: Optional[CheckEnv]) -> bool:
    host = url_host(value)
    return host is not None and host in _env(env).ctx.hosts


def _remote_name_or_url(value: str, env: Optional[CheckEnv]) -> bool:
    return value == "." or value in _env(env).ctx.remotes or _url(value, env)


def _fetch_refspec(value: str, env: Optional[CheckEnv]) -> bool:
    remote = _env(env).entry.key.subsection
    if remote is None:
        return False
    return re.match(r"\+?refs/[^:]+:refs/remotes/" + re.escape(remote) + "/", value) is not None


def _hooks_path(value: str, env: Optional[CheckEnv]) -> bool:
    e = _env(env)
    if _dotdot_after_segment(value):
        return False
    surface = e.ctx.surface
    pairs = _hooks_targets(value, surface)
    if not pairs:
        return False
    tracked = {_norm(d) for d in surface.tracked_dirs}
    inside = all(any(_inside(t, top) for top in tops) for t, tops in pairs)
    if inside and any(t in tracked for t, _ in pairs):
        return True
    return _same_targets_as_lkg(e.entry, frozenset(t for t, _ in pairs), e.ctx)


def _same_targets_as_lkg(
    entry: ConfigEntry, targets: frozenset[PurePosixPath], ctx: ClassifyCtx
) -> bool:
    """A respelled hooksPath (relative <-> absolute) whose targets match the LKG value from the
    same file passes."""
    if ctx.lkg is None:
        return False
    for atom in ctx.lkg.atoms.values():
        if isinstance(atom, ConfigEntry) and atom.key == _HOOKSPATH and atom.file == entry.file:
            old = _hooks_targets(atom.value, ctx.surface)
            if old and frozenset(t for t, _ in old) == targets:
                return True
    return False


def _worktree_path(value: str, env: Optional[CheckEnv]) -> bool:
    e = _env(env)
    if _dotdot_after_segment(value):
        return False
    surface = e.ctx.surface
    target = _worktree_target(e.entry, surface)
    if target is None or not _inside(target, surface.anchor.path):
        return False
    # A worktree at (or inside) a git dir would check files out over git's own control files.
    git_dirs = [m.git_dir for m in surface.members] + [surface.common_dir]
    return not any(_inside(target, g) for g in git_dirs)


def _include_path(value: str, env: Optional[CheckEnv]) -> bool:
    e = _env(env)
    if _dotdot_after_segment(value):
        return False
    target = _include_target(e.entry, e.ctx.surface)
    return target is not None and any(_inside(target, m.git_dir) for m in e.ctx.surface.members)


def _template(value: str, env: Optional[CheckEnv]) -> bool:
    _env(env)
    # Task `templates` replaces this with templates.config_template_match(entry, ctx, rules.templates).
    return False


_STATIC: Mapping[str, Predicate] = {
    "any": lambda value, env: True,
    "never": lambda value, env: False,
    "bool": _bool,
    "is_false": _is_false,
    "refname": lambda value, env: _REFNAME.fullmatch(value) is not None,
    "gh_resolved": lambda value, env: value == "base" or _OWNER_REPO.fullmatch(value) is not None,
    "url": _url,
    "remote_name_or_url": _remote_name_or_url,
    "fetch_refspec": _fetch_refspec,
    "hooks_path": _hooks_path,
    "worktree_path": _worktree_path,
    "include_path": _include_path,
    "template": _template,
}
_NEEDS_ENV = frozenset(
    {"url", "remote_name_or_url", "fetch_refspec", "hooks_path", "worktree_path",
     "include_path", "template"}
)


def _compile(name: str) -> Predicate:
    """A predicate by name. Parameterized forms: `in:a,b` (case-insensitive), `eq:x`, `prefix:x`,
    `bool_or:a,b` (a bool, or one of the listed words, case-insensitive)."""
    if name in _STATIC:
        return _STATIC[name]
    op, sep, arg = name.partition(":")
    if not sep:
        raise ValueError(f"unknown predicate {name!r}")
    if op == "in":
        words = frozenset(w.lower() for w in arg.split(","))
        return lambda value, env: value.lower() in words
    if op == "eq":
        return lambda value, env: value == arg
    if op == "prefix":
        return lambda value, env: value.startswith(arg)
    if op == "bool_or":
        extra = frozenset(w.lower() for w in arg.split(","))
        return lambda value, env: _bool(value, env) or value.lower() in extra
    raise ValueError(f"unknown predicate {name!r}")


def _names_used(rows: Sequence[Row]) -> set[str]:
    return {n for row in rows for n in (row.when, row.value_check) if n is not None}


PREDICATES: Mapping[str, Predicate] = {name: _compile(name) for name in _names_used(ROWS)}


def predicate(name: str) -> Predicate:
    found = PREDICATES.get(name)
    return found if found is not None else _compile(name)


def _validate(rows: Sequence[Row]) -> None:
    for row in rows:
        if row.when in _NEEDS_ENV:
            raise ValueError(f"`when` must be value-only: {row.doc}")
        if row.kind is Kind.WEAKEN and row.value_check != "never":
            raise ValueError(f"WEAKEN rows never pass: {row.doc}")


_validate(ROWS)


# -- Classification -----------------------------------------------------------------------------


def make_ctx(cur: Surface, lkg: Optional[Lkg], rules: RuleSet) -> ClassifyCtx:
    # Only remotes with a url count as names: git uses a URL-less remote's name as its URL, so
    # `remote.../evil.prune=true` must not make `branch.main.remote=../evil` a remote name.
    remotes = frozenset(
        e.key.subsection
        for e in cur.entries
        if e.key.section == "remote" and e.key.subsection is not None and e.key.variable == "url"
    )
    source = (
        [a for a in lkg.atoms.values() if isinstance(a, ConfigEntry)]
        if lkg is not None
        else cur.entries
    )
    hosts = {url_host(e.value) for e in source if _is_url_key(e.key)}
    trusted = {h.lower() for h in rules.trusted_hosts}
    return ClassifyCtx(cur, lkg, remotes, frozenset(h for h in hosts if h) | trusted)


def classify_entry(entry: ConfigEntry, ctx: ClassifyCtx, rules: RuleSet) -> tuple[Kind, Pass]:
    row = _first(rules.rows, entry.key, entry.value)
    if row is None:
        return Kind.UNKNOWN, Pass.NONE
    if predicate(row.value_check)(entry.value, CheckEnv(entry, ctx, rules)):
        return row.kind, _PASS_FOR[row.kind]
    return row.on_fail, Pass.NONE


def default_rules() -> RuleSet:
    # Task `templates` supplies the real Templates; until then the `template` check ignores them.
    no_templates: Optional[Templates] = None
    return RuleSet(
        rows=ROWS,
        templates=no_templates,  # type: ignore[arg-type]
        trusted_hosts=frozenset({"github.com"}),
    )

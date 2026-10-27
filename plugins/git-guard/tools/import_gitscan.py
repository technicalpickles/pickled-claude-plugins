#!/usr/bin/env python3
"""Turn a raw gitscan dump into the scrubbed corpus committed under tests/fixtures.

    import_gitscan.py <all_keys.tsv> <tracked_hooks_dir>... [--out DIR]

Input rows are `<owner>/<repo>/.git/<rel>\\t<key>\\t<value>` (the research
scan of real local repos). Output, written to tests/fixtures by default:

  corpus.tsv               `/home/u/src/repo-NN/.git/<rel>\\t<key>\\t<value>`
  corpus_tracked_dirs.txt  one scrubbed absolute tracked hooks dir per line

Scrubbing is deterministic. Repos, owners, branches, worktrees and (non-public)
submodules are numbered in first-seen order, one counter each, and the same
token is rewritten the same way wherever it appears: path, key subsection,
`refs/heads/...`, `worktrunk.*` values, URLs, `gh-resolved` and absolute paths.
Hosts and the URL scheme shape (scp-like vs https) are kept. Keys are kept as
git normalized them (section and variable lowercased, subsection verbatim).

A key or value whose shape is not recognised is never copied raw: its value
becomes `scrubbed` and a warning is printed, so a new shape is visible instead
of leaking. A last pass refuses to write if any original name survives.

Pure text transformation: stdlib only, never touches git or the repos.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KEPT_BRANCHES = {"main", "master"}
GENERIC_REMOTES = {"origin", "upstream", "fork"}
# Submodule names that are public upstream project paths (ruling: may stay as-is).
PUBLIC_SUBMODULES = {"vendor/sbp", "vendor/vim-plug"}
# Keys whose values carry no names; copied verbatim.
LITERAL_KEYS = re.compile(
    r"^(core\.(repositoryformatversion|filemode|bare|logallrefupdates|ignorecase"
    r"|precomposeunicode|longpaths|fsmonitor|symlinks)"
    r"|extensions\.[a-z]+|lfs\.repositoryformatversion"
    r"|submodule\..+\.active|hook\..+\.(event|command))$"
)
HOME_ROOT = f"{Path.home()}/github.com"  # where the scanned checkouts live; set by $HOME
SCRUBBED_ROOT = "/home/u/src"

SCP_URL = re.compile(r"^(?P<pre>[^@:/\s]+@[^:/\s]+:)(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?P<ext>\.git)?$")
PROTO_URL = re.compile(r"^(?P<pre>[a-z][a-z0-9+.-]*://[^/\s]+/)(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?P<ext>\.git)?$")


class Mapper:
    """First-seen-order numbering, one counter per kind."""

    def __init__(self) -> None:
        self.maps: dict[str, dict[str, str]] = {
            "repo": {}, "owner": {}, "branch": {}, "worktree": {}, "submodule": {}
        }
        self.prefix = {
            "repo": "repo", "owner": "owner", "branch": "b",
            "worktree": "wt", "submodule": "sub",
        }
        self.warnings: list[str] = []

    def tok(self, kind: str, name: str) -> str:
        m = self.maps[kind]
        if name not in m:
            m[name] = f"{self.prefix[kind]}-{len(m) + 1:02d}"
        return m[name]

    def branch(self, name: str) -> str:
        return name if name in KEPT_BRANCHES else self.tok("branch", name)

    def submodule(self, name: str) -> str:
        return name if name in PUBLIC_SUBMODULES else self.tok("submodule", name)

    def warn(self, msg: str) -> None:
        if msg not in self.warnings:
            self.warnings.append(msg)

    def originals(self) -> list[tuple[str, str]]:
        return [
            (kind, name)
            for kind, m in self.maps.items()
            for name in m
            if kind != "branch" or name not in KEPT_BRANCHES
        ]


def split_key(key: str) -> tuple[str, str | None, str]:
    first, last = key.find("."), key.rfind(".")
    if first == last:
        return key[:first], None, key[first + 1 :]
    return key[:first], key[first + 1 : last], key[last + 1 :]


def scrub_path_value(mp: Mapper, value: str) -> str | None:
    """Absolute path under the real checkout root -> scrubbed root; else None."""
    prefix = HOME_ROOT + "/"
    if not value.startswith(prefix):
        return None
    parts = value[len(prefix):].split("/", 2)
    if len(parts) < 2:
        return None
    _owner, repo = parts[0], parts[1]
    rest = "/" + parts[2] if len(parts) > 2 else ""
    if rest and not re.fullmatch(r"(/\.[A-Za-z0-9_-]+)+", rest):
        return None  # unknown tail shape: caller falls back to `scrubbed`
    return f"{SCRUBBED_ROOT}/{mp.tok('repo', repo)}{rest}"


def scrub_url(mp: Mapper, value: str) -> str | None:
    for rx in (SCP_URL, PROTO_URL):
        m = rx.match(value)
        if m:
            return (
                f"{m['pre']}{mp.tok('owner', m['owner'])}/"
                f"{mp.tok('repo', m['repo'])}{m['ext'] or ''}"
            )
    return None


def scrub_refspec(mp: Mapper, value: str) -> str | None:
    def heads(m: re.Match) -> str:
        b = m.group(1)
        return "refs/heads/" + (b if b == "*" else mp.branch(b))

    def remotes(m: re.Match) -> str:
        r, b = m.group(1), m.group(2)
        if r not in GENERIC_REMOTES:
            raise ValueError(f"remote {r}")
        return f"refs/remotes/{r}/" + (b if b == "*" else mp.branch(b))

    try:
        out = re.sub(r"refs/heads/([^\s:]+)", heads, value)
        out = re.sub(r"refs/remotes/([^/\s:]+)/([^\s:]+)", remotes, out)
    except ValueError:
        return None
    return out


def scrub_rel(mp: Mapper, rel: str) -> str:
    """`config`, `config.worktree`, `worktrees/<n>/config.worktree`, `modules/<sub>/config[.worktree]`."""
    if rel in ("config", "config.worktree"):
        return rel
    m = re.fullmatch(r"worktrees/([^/]+)/config\.worktree", rel)
    if m:
        return f"worktrees/{mp.tok('worktree', m.group(1))}/config.worktree"
    m = re.fullmatch(r"modules/(.+)/(config(?:\.worktree)?)", rel)
    if m:
        return f"modules/{mp.submodule(m.group(1))}/{m.group(2)}"
    raise SystemExit(f"unknown config path shape: {rel!r}")


def scrub_row(mp: Mapper, rawpath: str, key: str, value: str) -> tuple[str, str, str]:
    owner_repo, sep, rel = rawpath.partition("/.git/")
    if not sep or owner_repo.count("/") != 1:
        raise SystemExit(f"unknown path shape: {rawpath!r}")
    owner, repo = owner_repo.split("/")
    # Number the repo and owner at the point they are first seen, path first.
    mp.tok("owner", owner)
    path = f"{SCRUBBED_ROOT}/{mp.tok('repo', repo)}/.git/{scrub_rel(mp, rel)}"

    section, sub, var = split_key(key)
    new_key, new_value = key, None

    if section == "branch" and sub is not None:
        new_key = f"branch.{mp.branch(sub)}.{var}"
        if var == "merge":
            new_value = scrub_refspec(mp, value) if value.startswith("refs/") else None
        elif var in ("remote", "pushremote"):
            if value in GENERIC_REMOTES:
                new_value = value
            else:
                new_value = scrub_url(mp, value)
    elif section == "remote" and sub is not None:
        if sub not in GENERIC_REMOTES:
            mp.warn(f"remote name {sub!r} not in generic set (key {key})")
            return path, "remote.scrubbed." + var, "scrubbed"
        if var in ("url", "pushurl"):
            new_value = scrub_url(mp, value)
        elif var == "fetch" or var == "push":
            new_value = scrub_refspec(mp, value)
        elif var == "gh-resolved":
            if value == "base":
                new_value = value
            elif value.count("/") == 1:
                o, r = value.split("/")
                new_value = f"{mp.tok('owner', o)}/{mp.tok('repo', r)}"
    elif section == "submodule" and sub is not None:
        new_key = f"submodule.{mp.submodule(sub)}.{var}"
        if var == "url":
            new_value = scrub_url(mp, value)
        elif LITERAL_KEYS.match(f"submodule.x.{var}"):
            new_value = value
    elif key == "core.hookspath":
        new_value = value if value == ".githooks" else scrub_path_value(mp, value)
    elif key == "core.worktree":
        stripped = value
        while stripped.startswith("../"):
            stripped = stripped[3:]
        head = value[: len(value) - len(stripped)]
        if head and stripped and not stripped.startswith("/"):
            new_value = head + mp.submodule(stripped)
    elif key in ("worktrunk.default-branch", "worktrunk.history"):
        new_value = mp.branch(value)
    elif LITERAL_KEYS.match(key):
        new_value = value

    if new_value is None:
        mp.warn(f"unrecognised shape, value scrubbed: {key} = {value!r}")
        new_value = "scrubbed"
    return path, new_key, new_value


def scrub_tracked_dir(mp: Mapper, d: str) -> str:
    out = scrub_path_value(mp, d.rstrip("/"))
    if out is None:
        raise SystemExit(f"tracked dir not under {HOME_ROOT}/<owner>/<repo>/.<dir>: {d!r}")
    return out


def check_no_leaks(mp: Mapper, text: str) -> None:
    """Refuse to write if any original name survives in the output."""
    low = text.lower()
    leaks = []
    # Public submodule names are kept on purpose, so their last segment may appear.
    public = {s.rsplit("/", 1)[-1] for s in PUBLIC_SUBMODULES} | set(PUBLIC_SUBMODULES)
    for kind, name in mp.originals():
        if kind in ("submodule",):
            continue
        # Whole-token match so short repo names ("sb") don't trip on substrings.
        # Branch names are checked by the full name and, if multi-segment, each segment.
        needles = {name}
        if kind == "branch":
            needles |= {s for s in re.split(r"[/]", name) if len(s) > 3}
        for n in needles - public:
            if re.search(r"(?<![A-Za-z0-9_.-])" + re.escape(n.lower()) + r"(?![A-Za-z0-9_-])", low):
                leaks.append((kind, name))
    for needle in (str(Path.home()).lower(), "/users/"):
        if needle in low:
            leaks.append(("literal", needle))
    if leaks:
        raise SystemExit(f"refusing to write, original names survive: {leaks}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("all_keys", type=Path)
    ap.add_argument("tracked_dirs", nargs="+")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "tests" / "fixtures")
    args = ap.parse_args(argv)

    mp = Mapper()
    rows = []
    for line in args.all_keys.read_text().splitlines():
        if not line.strip():
            continue
        rawpath, key, value = line.split("\t", 2)
        rows.append("\t".join(scrub_row(mp, rawpath, key, value)))
    tracked = [scrub_tracked_dir(mp, d) for d in args.tracked_dirs]

    corpus = "\n".join(rows) + "\n"
    dirs = "\n".join(tracked) + "\n"
    check_no_leaks(mp, corpus + dirs)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "corpus.tsv").write_text(corpus)
    (args.out / "corpus_tracked_dirs.txt").write_text(dirs)
    for w in mp.warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(
        f"wrote {len(rows)} rows, {len(mp.maps['repo'])} repos, "
        f"{len(mp.maps['owner'])} owners, {len(mp.maps['branch'])} branches, "
        f"{len(mp.maps['worktree'])} worktrees, {len(mp.warnings)} warnings",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

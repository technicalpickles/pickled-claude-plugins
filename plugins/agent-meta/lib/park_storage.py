"""Repo-keyed park storage. Pure stdlib; no external deps.

Park files live at ``~/.claude/parks/<repo-root-slug>/`` so every worktree of
a repo resolves to the same directory. Each park is a Markdown file with a
strict-subset YAML frontmatter block.

This module is intentionally minimal:
  * ``repo_key()`` — slug for the current working directory's repo
  * ``park_dir(key)`` / ``ensure_park_dirs(key)`` — path helpers
  * ``list_active(key)`` — active parks in a repo
  * ``Park.load(path)`` / ``Park.save(path)`` — read/write park files
  * ``record_unpark(key, session, slug)`` / ``read_last_unpark(key, session)``
    — per-session parent-chain breadcrumb

See ``docs/plans/2026-04-19-repo-keyed-park-store.md`` for the larger design.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Optional

_DEFAULT_PARKS_ROOT = Path.home() / ".claude" / "parks"
PARKS_ROOT: Path = Path(os.environ["CLAUDE_PARKS_ROOT"]) if "CLAUDE_PARKS_ROOT" in os.environ else _DEFAULT_PARKS_ROOT

# Frontmatter fields that are fundamentally string-or-None. Anything here
# gets written as `null` when the attribute is None, otherwise as a bare
# (or quoted, if necessary) value. The dataclass field order IS the on-disk
# order — downstream tools rely on this.
_FRONTMATTER_FIELDS = (
    "slug",
    "status",
    "parked_at",
    "branch",
    "worktree",
    "unparked_at",
    "parent",
    "plan",
    "task",
    "origin_session_id",
    "last_kept_at",
    "name",
    "type",
)


def _slugify(path: str) -> str:
    """Replace non-alphanumerics with ``-``, matching the ``~/.claude/projects/``
    naming convention.

    Leading dash is KEPT (absolute paths always start with ``/`` which becomes
    ``-``). Trailing dashes are stripped so ``/tmp/foo/`` and ``/tmp/foo``
    produce the same slug.
    """
    slug = re.sub(r"[^A-Za-z0-9]", "-", path)
    return slug.rstrip("-")


def repo_key() -> str:
    """Return the park-store key for the current working directory.

    Inside a git repo: slug of the shared repo root, derived from
    ``git rev-parse --git-common-dir``. We deliberately avoid
    ``--show-toplevel`` because it returns the *worktree* path, so every
    worktree would get its own park directory — defeating the whole point
    of making parks survive across worktrees.

    ``--git-common-dir`` returns the path to the shared ``.git`` directory
    (the one that lives in the main checkout). Its parent is the main repo
    root, which is identical across every worktree of that repo. From the
    main checkout the returned path is relative (``.git``); from a worktree
    it's absolute. We ``.resolve()`` before taking the parent so both cases
    produce the same absolute repo-root path and thus the same slug.

    Outside any git repo: slug of the resolved cwd.
    """
    cwd = os.getcwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        common_dir = result.stdout.strip()
        if common_dir:
            # Resolve FIRST, then take parent. From the main checkout,
            # common_dir is `.git` (relative) so Path(".git").parent is `.`
            # — wrong. Resolving against cwd produces the absolute .git
            # path; its parent is the repo root.
            common_path = Path(common_dir)
            if not common_path.is_absolute():
                common_path = Path(cwd) / common_path
            repo_root = common_path.resolve().parent
            return _slugify(str(repo_root))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return _slugify(str(Path(cwd).resolve()))


def park_dir(key: str, root: Path = PARKS_ROOT) -> Path:
    """Return the active park directory for ``key``.

    Does not create anything — use ``ensure_park_dirs`` for that.
    """
    return root / key


def ensure_park_dirs(key: str, root: Path = PARKS_ROOT) -> Path:
    """Create ``<root>/<key>/`` plus ``done/``, ``stale/``, ``.state/``.

    Returns the active dir. Idempotent.
    """
    active = park_dir(key, root=root)
    active.mkdir(parents=True, exist_ok=True)
    for sub in ("done", "stale", ".state"):
        (active / sub).mkdir(exist_ok=True)
    return active


@dataclass
class Park:
    slug: str
    status: str                         # "parked" | "unparked"
    parked_at: str                      # ISO-ish timestamp
    branch: str
    worktree: Optional[str] = None
    unparked_at: Optional[str] = None
    parent: Optional[str] = None        # parent park slug (e.g. "park-foo")
    plan: Optional[str] = None          # optional plan doc path
    task: Optional[str] = None          # optional taskwarrior UUID
    origin_session_id: Optional[str] = None
    last_kept_at: Optional[str] = None  # set by keep action; overrides parked_at for age
    name: Optional[str] = None          # frontmatter name, e.g. "park-<slug>"
    type: str = "park"
    body: str = ""                      # everything after the frontmatter

    @classmethod
    def load(cls, path: Path) -> "Park":
        """Parse a park file: ``---`` frontmatter then body."""
        text = Path(path).read_text()
        meta, body = _split_frontmatter(text)
        known = {f.name for f in fields(cls)} - {"body"}
        kwargs = {k: v for k, v in meta.items() if k in known}
        return cls(body=body, **kwargs)

    def save(self, path: Path) -> None:
        """Write frontmatter + body to ``path``.

        Frontmatter field order matches ``_FRONTMATTER_FIELDS`` (= dataclass
        order sans ``body``). Optional fields with ``None`` values are written
        as ``null`` so the schema on disk is stable.
        """
        lines = ["---"]
        for key in _FRONTMATTER_FIELDS:
            value = getattr(self, key)
            lines.append(f"{key}: {_format_value(value)}")
        lines.append("---")
        lines.append(self.body)
        # Body already tends to end with its own newline; if not, the join +
        # rstrip keeps the file from growing an extra blank line on every save.
        text = "\n".join(lines[:-1]) + "\n" + lines[-1]
        if not text.endswith("\n"):
            text += "\n"
        Path(path).write_text(text)


def list_active(key: str, root: Path = PARKS_ROOT) -> list[Park]:
    """Return active parks for ``key`` (top-level ``.md`` files).

    Skips ``done/``, ``stale/``, ``.state/`` and any non-.md files. Returns an
    empty list if the directory does not exist.
    """
    active = park_dir(key, root=root)
    if not active.is_dir():
        return []
    parks: list[Park] = []
    for entry in sorted(active.iterdir()):
        if entry.is_dir():
            continue
        if entry.suffix != ".md":
            continue
        parks.append(Park.load(entry))
    return parks


def age_days(timestamp: str) -> int:
    """Days elapsed since an ISO timestamp string."""
    try:
        parked = datetime.fromisoformat(timestamp)
        return (datetime.now() - parked).days
    except (ValueError, TypeError):
        return 0


# --- Per-session state (parent-chain breadcrumb) ----------------------------


def _state_path(key: str, session_id: str, root: Path = PARKS_ROOT) -> Path:
    return park_dir(key, root=root) / ".state" / f"{session_id}.json"


def record_unpark(
    key: str,
    session_id: str,
    slug: str,
    root: Path = PARKS_ROOT,
) -> None:
    """Write breadcrumb that this session just unparked ``slug``.

    Overwrites any prior record for the same session — only the most
    recent unpark is tracked (state cell, not log). The ``.state/``
    directory is created if missing so callers don't need to have
    pre-run ``ensure_park_dirs``.
    """
    path = _state_path(key, session_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_unpark": slug,
        "at": datetime.now().isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(payload))


def read_last_unpark(
    key: str,
    session_id: str,
    root: Path = PARKS_ROOT,
) -> Optional[str]:
    """Return the slug the given session most recently unparked, or ``None``.

    Missing file → ``None`` (checked race-free via FileNotFoundError).
    Malformed JSON → raises ``json.JSONDecodeError``: a corrupt state
    file is a real bug worth surfacing, not something to paper over.
    """
    path = _state_path(key, session_id, root=root)
    try:
        raw = path.read_text()
    except FileNotFoundError:
        return None
    return json.loads(raw).get("last_unpark")


# --- Frontmatter helpers ----------------------------------------------------


def _split_frontmatter(text: str) -> tuple[dict[str, Optional[str]], str]:
    """Split ``---\\n...---\\n`` frontmatter from body.

    Returns ``(meta, body)``. If no frontmatter is present, ``meta`` is empty
    and ``body`` is the whole text.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm = text[4:end]
    body = text[end + len("\n---\n"):]
    return _parse_frontmatter(fm), body


def _parse_frontmatter(block: str) -> dict[str, Optional[str]]:
    """Parse ``key: value`` pairs, one per line.

    Strict subset of YAML: no lists, no nested maps, no multi-line values.
    ``null`` (bare) becomes ``None``. Single/double quoted string values have
    their surrounding quotes stripped. Unknown keys are preserved so callers
    can decide what to drop.
    """
    meta: dict[str, Optional[str]] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = _parse_value(value.strip())
    return meta


def _parse_value(raw: str) -> Optional[str]:
    if raw == "" or raw == "null":
        return None
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        return raw[1:-1]
    return raw


def _format_value(value: Optional[str]) -> str:
    if value is None:
        return "null"
    # Quote strings that would otherwise confuse a naive re-parser. We keep
    # this narrow: anything containing a leading/trailing space or looking
    # like a YAML literal we emit (``null``) gets double-quoted. Colons,
    # dashes, slashes are fine bare because our parser splits on the FIRST
    # `:` only.
    if value == "null" or value != value.strip() or value == "":
        return f'"{value}"'
    return value

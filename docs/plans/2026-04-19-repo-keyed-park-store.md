# Repo-Keyed Park Store Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current memory-backed park/unpark workflow with a repo-keyed external store, a SessionStart hook for surfacing, chain/anchor metadata, and a lifecycle audit command.

**Architecture:** Parks live at `~/.claude/parks/<repo-root-slug>/` instead of Claude Code's per-project memory dir. This lets all worktrees of a repo share park history. A SessionStart hook surfaces active parks in context (replacing the auto-memory mechanism). An audit skill handles lifecycle (done/stale/keep/delete), keyed off branch existence and age. A one-time migration skill moves existing `park-*.md` memory entries and in-repo `.parkinglot/` files into the new store.

**Tech Stack:** Python 3 (stdlib only) for the storage library, hooks, and audit logic. Markdown + YAML frontmatter for park files. Existing agent-meta hook pattern (`inject-session-context.py`) as the template.

---

## Design summary

### Storage layout
```
~/.claude/parks/<repo-root-slug>/
  <date>-<slug>.md                  # active (parked or unparked)
  done/<date>-<slug>.md             # work completed
  stale/<date>-<slug>.md            # abandoned, no follow-up
```

Repo slug derivation matches Claude Code's convention: slashified path of `git rev-parse --show-toplevel`. Non-git-repo fallback: slugified cwd. All worktrees of a repo resolve to the same slug.

### Park file frontmatter
```yaml
---
name: park-<slug>
type: park
status: parked | unparked
slug: <slug>
parked_at: 2026-04-19T10:23:00
unparked_at: null
branch: feat/jwt-auth
worktree: /abs/path/to/worktree      # null if main repo
parent: park-<prev-slug>             # auto-filled from last unpark this session
plan: docs/plans/ccrpi-v2.md         # optional, offered if session touched a plan doc
task: <taskwarrior-uuid>             # optional, offered if session used taskwarrior
origin_session_id: <session-id>
---
```

### Parent chain mechanic
Unpark writes the unparked slug to a per-session state file at `~/.claude/parks/.state/<session-id>.json`. Park reads that file when deciding `parent:`. Stop hook (future) or manual TTL cleans old state files. No transcript scraping.

### SessionStart surfacing
New hook at `plugins/agent-meta/hooks/SessionStart.py` reads the repo-keyed park dir and emits active parks as additional context. Threshold: if >8 active parks, collapse to one-line summary with `/memory-audit` pointer.

### Audit lifecycle
New skill `plugins/agent-meta/skills/audit/SKILL.md` backed by `plugins/agent-meta/scripts/audit-parks.py`. Rules-based preview:
- Park age >30d, status=parked, no unpark → flag as orphaned
- Park status=unparked, unparked >7d ago, no re-park → flag as maybe-done
- Branch doesn't exist locally or on remote → flag as probably-done

Per-item interactive prompt: `[d]one  [s]tale  [k]eep  [x]delete  [?]show`. Actions move files between subdirs; delete actually removes.

### Migration
One-time skill `plugins/agent-meta/skills/migrate/SKILL.md` backed by `plugins/agent-meta/scripts/migrate-parks.py`. Discovers old park state from:
- `~/.claude/projects/*/memory/park-*.md` (memory entries + MEMORY.md index lines)
- `<repo>/.parkinglot/*.md` (in-tree files)

Per-item interactive choice: move to new store (active/done/stale) or purge. Removes migrated memory entries from `MEMORY.md` index.

---

## Task sequence

Tasks use kebab-case slugs, not ordinals — per repo convention (plan step numbers drift).

### Task: `storage-module`

Shared Python library for resolving the park store path and loading/saving park files.

**Files:**
- Create: `plugins/agent-meta/lib/__init__.py` (empty)
- Create: `plugins/agent-meta/lib/park_storage.py`
- Create: `plugins/agent-meta/tests/__init__.py` (empty)
- Create: `plugins/agent-meta/tests/test_park_storage.py`

**Step 1: Write failing tests**

Write tests covering:
- `repo_key()`: returns slashified path of git toplevel when in a repo
- `repo_key()`: returns slashified cwd when NOT in a git repo
- `park_dir(key)`: returns `~/.claude/parks/<key>/` as a `Path`
- `ensure_park_dirs(key)`: creates active, done/, stale/, .state/ if missing
- `list_active(key)`: returns list of Park objects at active dir, skipping subdirs
- `Park.load(path)`: parses YAML frontmatter + body; handles missing optional fields
- `Park.save(path)`: round-trips frontmatter + body preserving field order

```python
# plugins/agent-meta/tests/test_park_storage.py
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from plugins.agent_meta.lib import park_storage as ps


class RepoKeyTests(unittest.TestCase):
    def test_inside_git_repo_uses_toplevel(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "my-repo"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            with patch("os.getcwd", return_value=str(repo)):
                self.assertEqual(ps.repo_key(), ps._slugify(str(repo.resolve())))

    def test_outside_git_repo_uses_cwd(self):
        with TemporaryDirectory() as tmp:
            with patch("os.getcwd", return_value=tmp):
                self.assertEqual(ps.repo_key(), ps._slugify(str(Path(tmp).resolve())))


# ... more tests for park_dir, ensure_park_dirs, list_active, Park.load/save
```

**Step 2: Run tests to verify they fail**

```
cd plugins/agent-meta
python3 -m unittest discover tests -v
```

Expected: ImportError or AttributeError for missing module/functions.

**Step 3: Implement `park_storage.py`**

```python
"""Repo-keyed park storage. Pure stdlib; no external deps."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

PARKS_ROOT = Path.home() / ".claude" / "parks"


def _slugify(path: str) -> str:
    """Mirror Claude Code's project-slug convention: replace / with -, strip leading."""
    return re.sub(r"[^A-Za-z0-9]", "-", path).strip("-")


def repo_key() -> str:
    """Return the repo slug for the current working directory.
    In a git repo: slug of `git rev-parse --show-toplevel`.
    Otherwise: slug of cwd.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        toplevel = result.stdout.strip()
        if toplevel:
            return _slugify(toplevel)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return _slugify(str(Path(os.getcwd()).resolve()))


def park_dir(key: str) -> Path:
    return PARKS_ROOT / key


def ensure_park_dirs(key: str) -> Path:
    base = park_dir(key)
    for sub in ("", "done", "stale", ".state"):
        (base / sub).mkdir(parents=True, exist_ok=True)
    return base


# ... Park dataclass with load/save, list_active helper
```

Implementation should parse frontmatter as dict (simple key: value, preserve strings, booleans, nulls). Don't pull in PyYAML — hand-written parser is ~20 lines and plenty for this schema.

**Step 4: Run tests to verify they pass**

```
cd plugins/agent-meta
python3 -m unittest discover tests -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add plugins/agent-meta/lib plugins/agent-meta/tests
git commit -m "feat(agent-meta): add park_storage module for repo-keyed park files"
```

---

### Task: `parent-chain-state`

Per-session state file for parent auto-fill. Unpark writes here, park reads.

**Files:**
- Modify: `plugins/agent-meta/lib/park_storage.py` (add state helpers)
- Modify: `plugins/agent-meta/tests/test_park_storage.py`

**Step 1: Write failing tests**

```python
def test_write_last_unpark_then_read(self):
    key = ps.repo_key()
    ps.ensure_park_dirs(key)
    ps.record_unpark(key, session_id="sess-1", slug="jwt-auth")
    self.assertEqual(ps.read_last_unpark(key, "sess-1"), "jwt-auth")

def test_read_last_unpark_returns_none_if_missing(self):
    key = ps.repo_key()
    ps.ensure_park_dirs(key)
    self.assertIsNone(ps.read_last_unpark(key, "no-such-session"))
```

**Step 2: Run to verify fail**

**Step 3: Implement**

State file at `<park_dir>/.state/<session-id>.json` with shape `{"last_unpark": "<slug>", "at": "<iso-ts>"}`. Small JSON, stdlib only.

**Step 4: Run tests to verify pass**

**Step 5: Commit**

```bash
git commit -m "feat(agent-meta): add parent-chain state file to park_storage"
```

---

### Task: `park-skill-rewrite`

Rewrite park SKILL.md to use the new storage location and frontmatter schema.

**Files:**
- Modify: `plugins/agent-meta/skills/park/SKILL.md`
- Delete: `plugins/agent-meta/skills/park/scripts/get-session-id.sh` (session ID comes from hook; fallback no longer needed in this skill)

**Step 1: Draft new SKILL.md**

New workflow:
1. Read injected context for session ID + transcript path.
2. Invoke `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/park-resolve.py` which returns repo key, current branch, worktree path (JSON).
3. Look up parent by calling `park_storage.read_last_unpark(key, session_id)`.
4. If a plan doc path appears in session context, prompt: "Link this park to `docs/plans/foo.md`? (y/n)".
5. If a taskwarrior UUID appears in session context, prompt similarly.
6. Write park file via `park_storage.Park.save()`.

The skill stays instruction-based — Claude drives the flow, but the heavy lifting (path resolution, file I/O) is in the Python helpers so Claude isn't doing path arithmetic.

**Step 2: Add helper script**

- Create: `plugins/agent-meta/scripts/park-resolve.py`

Prints a JSON blob with `{ repo_key, branch, worktree, is_worktree }` so the skill has a single command to get all the git context.

**Step 3: Write integration smoke test**

- Create: `plugins/agent-meta/tests/test_park_resolve.py`

Use `TemporaryDirectory`, `git init`, call the script as a subprocess, assert the JSON shape.

**Step 4: Run tests to verify pass**

**Step 5: Manual verification**

Open a fresh Claude Code session in a test repo, invoke park skill, verify:
- File lands at `~/.claude/parks/<expected-slug>/<date>-<slug>.md`
- Frontmatter has correct branch, session ID, parked_at
- No file written to old locations

**Step 6: Commit**

```bash
git commit -m "feat(agent-meta): write parks to repo-keyed store"
```

---

### Task: `unpark-skill-rewrite`

Update unpark to read from the new store and record last-unpark for chain.

**Files:**
- Modify: `plugins/agent-meta/skills/unpark/SKILL.md`
- Create: `plugins/agent-meta/scripts/unpark-list.py`

**Step 1: Write tests for the list helper**

- `plugins/agent-meta/tests/test_unpark_list.py`

Create a temp park dir with a few active parks, run `unpark-list.py`, assert JSON output sorted by recency.

**Step 2: Implement `unpark-list.py`**

Prints active parks in the current repo's store as JSON: `[{ slug, parked_at, status, branch, summary }, ...]`.

**Step 3: Rewrite SKILL.md**

New workflow:
1. Invoke `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/unpark-list.py` → get candidate parks.
2. If argument provided (path or slug): resolve to park; if ambiguous, show options.
3. If no argument: list all active parks, ask which.
4. Read park file, present summary (same shape as current skill).
5. Validate (branch exists, worktree exists, files exist).
6. On confirm: update park status to `unparked`, stamp `unparked_at`, record last-unpark in state file for chain.

**Step 4: Run tests**

**Step 5: Manual verification**

Park from one session, unpark from a different worktree of the same repo. Verify:
- Unpark finds the park (cross-worktree shared store working)
- Park file status flips to `unparked`
- State file gets the slug

**Step 6: Commit**

```bash
git commit -m "feat(agent-meta): read parks from repo-keyed store and record unpark chain"
```

---

### Task: `session-start-hook`

Surface active parks at session start.

**Files:**
- Create: `plugins/agent-meta/hooks/SessionStart.py`
- Modify: `plugins/agent-meta/hooks/hooks.json`

**Step 1: Write tests**

- Create: `plugins/agent-meta/tests/test_session_start_hook.py`

Mock stdin with a SessionStart payload (json with `session_id`, `cwd`). Mock `park_storage.list_active`. Assert hook emits correct `hookSpecificOutput.additionalContext` for:
- 0 parks: no output (exit 0, empty stdout)
- 1-8 parks: full list with branch column
- >8 parks: collapsed summary

**Step 2: Implement hook**

```python
#!/usr/bin/env python3
"""SessionStart hook: surface active parks for the current repo."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import park_storage as ps

THRESHOLD = 8

def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    key = ps.repo_key()
    parks = ps.list_active(key)
    if not parks:
        sys.exit(0)

    if len(parks) > THRESHOLD:
        msg = f"{len(parks)} active parks in this repo. Run /audit to review."
    else:
        lines = [f"Active parks ({len(parks)}):"]
        for p in parks:
            age = ps.age_days(p.parked_at)
            lines.append(
                f"  {p.slug:<30} branch: {p.branch:<25} {p.status} {age}d ago"
            )
        msg = "\n".join(lines)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }))

if __name__ == "__main__":
    main()
```

**Step 3: Register in hooks.json**

Add SessionStart entry alongside the existing PostToolUse:

```json
"SessionStart": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/SessionStart.py"
      }
    ]
  }
]
```

**Step 4: Run tests**

**Step 5: Manual verification**

Park 3 items in a test repo, open a new session in that repo, verify context shows them. Park 10 items, verify collapsed form.

**Step 6: Commit**

```bash
git commit -m "feat(agent-meta): surface active parks via SessionStart hook"
```

---

### Task: `audit-skill`

New skill for the `/audit` lifecycle workflow.

**Files:**
- Create: `plugins/agent-meta/skills/audit/SKILL.md`
- Create: `plugins/agent-meta/scripts/audit-parks.py`
- Create: `plugins/agent-meta/tests/test_audit_parks.py`

**Step 1: Write tests for the rules engine**

Rules to test in isolation:
- `classify_park(park, now)` returns one of `orphan`, `maybe_done`, `branch_gone`, `healthy`
- Age-based: parked >30d → `orphan`
- Unparked >7d → `maybe_done`
- Branch check: calls `git branch --list` + `git ls-remote` — mock subprocess

```python
def test_classifies_parked_30d_as_orphan(self):
    park = make_park(status="parked", parked_at=days_ago(31))
    self.assertEqual(classify_park(park, now=NOW), "orphan")

def test_classifies_unparked_7d_as_maybe_done(self):
    park = make_park(status="unparked", unparked_at=days_ago(8))
    self.assertEqual(classify_park(park, now=NOW), "maybe_done")

def test_branch_gone_when_neither_local_nor_remote(self):
    with patch_branch_existence(local=False, remote=False):
        self.assertEqual(classify_park(park, now=NOW), "branch_gone")
```

**Step 2: Implement rules engine**

`audit-parks.py` has a `--list` mode (machine-readable JSON of classification) and an `--action <slug> <d|s|k|x>` mode for file moves.

**Step 3: Implement file-move actions**

- `d` (done): `mv active/<file> done/<file>`
- `s` (stale): `mv active/<file> stale/<file>`
- `k` (keep): touch park's `parked_at` (reset aging clock)? Or add `last_kept_at` field. **Decide during implementation.**
- `x` (delete): `rm active/<file>`

Test file-move actions with temp park dirs.

**Step 4: Write audit SKILL.md**

Workflow:
1. Invoke `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit-parks.py --list` → get classified parks.
2. Show grouped preview (orphans, maybe-done, branch-gone, healthy-count-only).
3. For each flagged park, interactive prompt.
4. Per decision: invoke `audit-parks.py --action <slug> <d|s|k|x>`.
5. Show summary at end: "Moved 3 to done/, 2 to stale/, kept 1, deleted 0."

**Step 5: Run tests**

**Step 6: Manual verification**

Create a few synthetic parks with varied ages and branches, run audit, walk through decisions, verify file movements.

**Step 7: Commit**

```bash
git commit -m "feat(agent-meta): add audit skill for park lifecycle management"
```

---

### Task: `migration-skill`

One-time migration of existing park state from memory entries + `.parkinglot/` files.

**Files:**
- Create: `plugins/agent-meta/skills/migrate/SKILL.md`
- Create: `plugins/agent-meta/scripts/migrate-parks.py`
- Create: `plugins/agent-meta/tests/test_migrate_parks.py`

**Step 1: Write discovery tests**

- `discover_memory_parks()` finds all `park-*.md` in `~/.claude/projects/*/memory/`
- `discover_parkinglot_files()` finds all `.parkinglot/*.md` under a given repo root
- Returns structured records with `{ source, path, repo_hint, slug, age }`

**Step 2: Implement discovery**

**Step 3: Write conversion tests**

- `convert_memory_to_park(record)` reads old format, produces new Park object
- Handles missing fields gracefully (older parks won't have branch metadata)
- Memory entries without `file:` pointer get the BODY as their .parkinglot equivalent

**Step 4: Implement conversion**

**Step 5: Implement MEMORY.md cleanup**

After successful migration, remove the `- [Park: ...](park-*.md)` line from the relevant `MEMORY.md`. Don't delete the whole file — the index has non-park entries too.

**Step 6: Write migrate SKILL.md**

Workflow:
1. Invoke `migrate-parks.py --discover` → preview total count + categorization.
2. Offer: "Migrate N parks? (y) interactive per-item / (r) rules-based (DONE→done/, >30d→stale/, else active/) / (n) cancel"
3. If interactive: per-park prompt (active/done/stale/skip).
4. If rules-based: show preview of what each park would become, confirm, execute.
5. Cleanup: remove migrated entries from MEMORY.md indexes.

**Step 7: Run tests**

**Step 8: Manual verification on a dry-run flag**

```bash
python3 scripts/migrate-parks.py --discover --dry-run
```

Verify it correctly identifies parks in your actual `~/.claude/projects/` without modifying anything.

**Step 9: Commit**

```bash
git commit -m "feat(agent-meta): add migration skill for existing park state"
```

---

### Task: `plugin-docs`

Update README and plugin.json references.

**Files:**
- Modify: `plugins/agent-meta/README.md`
- Modify: `plugins/agent-meta/.claude-plugin/plugin.json` (if new skills need listing)

**Step 1: Document the new model**

README updates:
- New section: "Park storage" — where files live, why (worktree sharing).
- Update skill table: add `audit`, add `migrate`.
- Migration note: point existing users to `migrate` skill.

**Step 2: Update skill list in plugin.json if needed**

Check current contents — if skills are auto-discovered from `skills/` subdirs, nothing to do. Otherwise add the new ones.

**Step 3: Manual review**

Re-read README end-to-end from the perspective of a new user installing agent-meta. Is the park/unpark/audit cycle clear? Is migration discoverable?

**Step 4: Commit**

```bash
git commit -m "docs(agent-meta): document repo-keyed park store and audit workflow"
```

---

### Task: `end-to-end-verification`

Prove the new system works across the real failure cases.

**No files to create** — this is a manual verification task.

**Cases to cover:**

1. **Fresh repo:** `mkdir /tmp/test-repo && cd $_ && git init`, open Claude, park, verify file at `~/.claude/parks/private-tmp-test-repo/`.

2. **Worktree sharing:** `cd pickled-finances && git worktree add .worktrees/test-park`, open Claude in the worktree, verify park written from worktree lands in the main-repo-keyed store. Unpark from main repo's cwd, verify it finds the worktree-written park.

3. **Chain:** Park A, unpark A, park B in the same session. Inspect B's frontmatter — `parent:` should be `park-A`.

4. **SessionStart surfacing:** Park something, open a new session in the same repo, verify the injected context mentions it.

5. **Audit done-detection:** Park on a branch, delete the branch, run `/audit`, verify the park is flagged `branch_gone`.

6. **Migration:** Run `migrate --discover --dry-run` against real `~/.claude/projects/` state. Inspect output against known park counts (37 oak-grove-strong, 19 picklehome, 17 tracy4dekalbschools, 1 dotfiles = 74 total).

Create a short verification log and commit as:

**Files:**
- Create: `plugins/agent-meta/docs/repo-keyed-parks-verification.md`

**Commit:**

```bash
git commit -m "docs(agent-meta): capture repo-keyed park store verification results"
```

---

## Out of scope (followups)

Captured in taskwarrior, **not** included in this plan:

- **Cross-machine park sync.** Repo-slug is machine-specific paths; syncing parks across machines needs a separate design. User deferred.
- **Stop hook for auto-audit prompts.** Hook warning when many orphans exist at park-time is desirable but not required for v1.
- **Memory-system insight tool (cq subcommand or separate plugin)** — taskwarrior task 88.
- **Auto-detection of "done" from session content** (e.g. "we shipped it" → offer close). Too magical for v1.
- **Plan-doc-as-trunk hierarchy.** An alternative chain model where the plan doc is the root and parks are branches. Deferred — linear `parent:` is enough for now.

## Open decisions to settle during implementation

1. **`[k]eep` action semantics in audit.** Does keeping reset the aging clock (touch `parked_at`) or add a `last_kept_at` field? The second preserves original parked date (useful for "how long has this been kicking around overall") but the first is simpler. **Leaning:** add `last_kept_at`, use it for age-for-flagging purposes, preserve `parked_at`.

2. **Threshold value for SessionStart collapse.** Spec'd at 8; revisit after dogfooding.

3. **Migration target for post-hoc DONE memories.** The existing oak-grove-strong memories often have "DONE: shipped commits X, Y, Z" as their body. On migration they'd become `done/` entries — but then they're out of MEMORY.md, so any value they had as quick-reference is lost. **Leaning:** that's fine. If a DONE record is worth keeping as memory, promote it to a proper `project` type manually. Don't preserve the accidental "park-as-shipped-log" pattern.

4. **Non-git-repo fallback slug stability.** Slugifying cwd works, but if the dir moves, the key changes. Fine for the one reported use case (`brineworks-workspace` is git-backed anyway). Flag if it bites.

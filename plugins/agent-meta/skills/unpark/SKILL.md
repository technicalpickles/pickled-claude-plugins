---
name: unpark
description: Resume work from a parked handoff
allowed-tools: Bash(python3:*), Bash(git:*), Bash(test:*), Read
---

# Unpark

Resume work from a park previously saved by the `park` skill. Parks live
in a repo-keyed store at `~/.claude/parks/<repo-slug>/`, shared across
every worktree of the same repo — so unparking works from any checkout.

Invocation forms:

```
unpark                  # list active parks, ask which
unpark <slug>           # resume the matching park
unpark <date>-<slug>    # disambiguate when the same slug was parked twice
unpark /absolute/path   # unpark a specific file
```

## Workflow

### 1. Read injected session context

When this skill is invoked, the agent-meta PostToolUse hook injects:

```
Session ID: <uuid>
Transcript: /path/to/transcript.jsonl
```

Read them. If no `Session ID:` line appears (older install, hook
disabled), treat the session ID as absent. Without it the parent-chain
breadcrumb for the next `park` in this session won't be written — that's
a degraded but non-fatal case; continue.

### 2. List active parks

Invoke `unpark-list.py` to get candidate parks in one Bash call:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/unpark-list.py"
```

Output is a JSON array, most-recent-first:

```json
[
  {
    "slug": "jwt-auth",
    "parked_at": "2026-04-17T10:23:00",
    "unparked_at": null,
    "status": "parked",
    "branch": "feat/auth",
    "summary": "Halfway through the JWT refactor, stuck on token refresh.",
    "path": "/Users/.../.claude/parks/<key>/2026-04-17-jwt-auth.md"
  }
]
```

If the array is empty, tell the user "No active parks in this repo's
store" and stop. Don't guess, don't fall back to legacy locations.

### 3. Pick the target park

**If the user passed no argument:** present a numbered list and ask
which to unpark.

```
Active parks:
1. jwt-auth         parked 2026-04-17  branch: feat/auth
   Halfway through the JWT refactor, stuck on token refresh.
2. fix-login-bug    parked 2026-04-15  branch: fix/login
   Repro works, patch drafted but untested.
```

**If the user passed an argument:** resolve it in this order:

1. **Absolute path** ending in `.md`: match entries by `path`.
2. **`YYYY-MM-DD-<slug>`** form: extract slug from the arg (last
   segment) and match the date (first 10 chars of `parked_at`).
3. **Bare slug:** match entries whose `slug` equals the arg.

If exactly one match, use it. If more than one (re-parks of the same
slug on different days), list them and ask. If zero, say so, show the
active list, and ask.

### 4. Load and summarize the park

Read the park file via Python and surface the relevant fields.

```bash
python3 - <<'PYEOF'
import sys
from pathlib import Path

PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
sys.path.insert(0, str(Path(PLUGIN_ROOT) / "lib"))
from park_storage import Park

path = "<absolute path from step 3>"
p = Park.load(Path(path))

print(f"slug: {p.slug}")
print(f"status: {p.status}")
print(f"branch: {p.branch}")
print(f"worktree: {p.worktree}")
print(f"parked_at: {p.parked_at}")
print(f"parent: {p.parent}")
print(f"plan: {p.plan}")
print(f"task: {p.task}")
print("---")
print(p.body)
PYEOF
```

Present to the user as a summary:

```
Resuming: <slug>

Parked:   <parked_at>
Branch:   <branch>
Worktree: <worktree or "(none, main checkout)">
Parent:   <parent or "(none)">
Plan:     <plan or "(none)">
Task:     <task or "(none)">

<body>
```

### 5. Validate

Best-effort, not blocking. Report findings as a checklist; let the user
decide whether to proceed.

- **Branch exists?** `git show-ref --verify --quiet refs/heads/<branch>`
  — non-zero means it's not local. Also try
  `git ls-remote --exit-code --heads origin <branch>` if a remote
  exists. Warn if neither finds it, but allow continuing.
- **Worktree path exists?** If `worktree` is non-null, check
  `test -d <worktree>`. If it's missing, warn and offer to unpark in
  the current cwd instead.
- **Key files referenced in the body?** Skim the body for paths
  (`path/to/file.py`-style tokens). Best-effort only — a fuzzy visual
  check like "two of the three files in the list still exist" is
  enough. Don't block on this.

Surface the results:

```
Validation:
  [x] Branch feat/auth exists locally
  [ ] Worktree /Users/.../wt/foo not found -- will unpark in current cwd
  [x] Referenced files all present
```

### 6. Confirm, then update

Ask:

```
Proceed with unpark?
  (y) yes, mark as unparked and start resuming
  (n) no, show the body again
  (p) show the park file path
```

On yes:

1. Flip `status` to `unparked` and stamp `unparked_at` with the current
   ISO timestamp.
2. Save back to the SAME path via `Park.save()`.
3. Call `park_storage.record_unpark(key, session_id, slug)` so the next
   `park` in this session auto-fills `parent:`. Skip this call if no
   session ID was injected.

```bash
python3 - <<'PYEOF'
import sys
from datetime import datetime
from pathlib import Path

PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
sys.path.insert(0, str(Path(PLUGIN_ROOT) / "lib"))
from park_storage import Park, record_unpark, repo_key

path = "<absolute path>"
session_id = "<from injected context, or empty>"

p = Park.load(Path(path))
p.status = "unparked"
p.unparked_at = datetime.now().isoformat(timespec="seconds")
p.save(Path(path))

if session_id:
    record_unpark(repo_key(), session_id, p.slug)

print(f"Unparked {p.slug}")
PYEOF
```

### 7. Report and hand off

Print the body's "Next Steps" section (or the whole body if the park
doesn't use that heading), then offer a concrete first move:

```
Unparked: jwt-auth

Next steps from the park:
1. Fix refresh flow.
2. Write tests for expiry edge case.

Continuing from step 1. Want me to start there?
```

Keep the handoff copy-pasteable: the user (or a human reader) should
see exactly what's queued up next.

## Summary heuristic

`unpark-list.py` derives a one-line `summary` from the park body: the
first non-empty line that doesn't start with `#`, trimmed to 100 chars.
Empty body or body-of-only-headings → empty summary. This is
documented in the script itself; see
[scripts/unpark-list.py](../../scripts/unpark-list.py).

## Edge Cases

- **No active parks.** Tell the user plainly and stop. No legacy
  location fallback.
- **Slug collision across dates.** The same topic can be parked and
  re-parked; disambiguate by date and ask.
- **Missing worktree.** Warn and offer to continue in cwd. Don't
  recreate the worktree silently.
- **Outside a git repo.** `unpark-list.py` emits `[]` — same code path
  as "no parks." The skill tells the user nothing is unparkable here.
- **Corrupt park file.** `Park.load()` will raise. Surface the error,
  name the file, and ask the user whether to skip or inspect it
  manually.

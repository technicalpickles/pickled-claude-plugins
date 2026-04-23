---
name: audit
description: Review and clean up active parks via lifecycle management
allowed-tools: Bash(python3:*)
---

# Audit Parks

Review active parks for the current repo and take lifecycle actions. Parks are
classified by rules and grouped for review; you handle each flagged park
interactively.

## Step 1: Classify

Run the audit script to get classified parks:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit-parks.py" --list
```

Parse the JSON array. Each entry has:
- `slug` - park identifier
- `classification` - one of: `orphan`, `maybe_done`, `branch_gone`, `healthy`
- `status`, `branch`, `parked_at`, `unparked_at`

## Step 2: Show Grouped Preview

Present a summary grouped by classification:

```
Audit results for <repo>:

branch_gone (N):  branch deleted — likely done
  - <slug>  (<branch>)  parked Xd ago

orphan (N):  parked >30d with no activity
  - <slug>  (<branch>)  parked Xd ago

maybe_done (N):  unparked >7d ago, no re-park
  - <slug>  (<branch>)  unparked Xd ago

healthy (N): no action needed (skipping)
```

If there are no flagged parks (all healthy), say so and stop.

## Step 3: Interactive Per-Item Decisions

For each flagged park (branch_gone first, then orphan, then maybe_done):

Show:
```
[<slug>]  branch: <branch>  status: <status>  age: Xd
  <first line of park body if present>

  [d] done    [s] stale    [k] keep    [x] delete    [?] show full
```

Wait for user input. On `?`, read and display the full park file, then
re-show the prompt. On any other choice, apply immediately:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit-parks.py" --action <slug> <choice>
```

Actions:
- `d` - move to `done/` (work completed)
- `s` - move to `stale/` (abandoned, no follow-up)
- `k` - keep; resets the aging clock (`last_kept_at` updated)
- `x` - delete permanently

## Step 4: Summary

After all flagged parks are handled:

```
Audit complete:
  Moved to done/: N
  Moved to stale/: N
  Kept (clock reset): N
  Deleted: N
  Skipped: N
```

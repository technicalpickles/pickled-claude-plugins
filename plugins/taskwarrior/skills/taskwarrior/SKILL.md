---
name: taskwarrior
description: Use when querying or modifying tasks via the taskwarrior CLI - dense recipes for listing, single-field lookups, multi-task batched lookups, full-text search, and the soft description-length convention. Activates on `task list`, `task add`, `task info`, `task done`, "what's on the backlog", "find a task", or any taskwarrior interaction.
---

# Taskwarrior Token-Dense Recipes

Use these recipes whenever you invoke `task` on the user's behalf. They cut output size 4-10× compared to default formats.

**Companion config:** This skill assumes `~/.taskrc` has the named `dense` report defined and `verbose=` configured to suppress override-echo noise. If `task` (with no args) doesn't run a dense report, see the design doc at `docs/superpowers/specs/2026-05-08-taskwarrior-token-density-design.md`.

## Listing tasks

**Default — use the named report:**

```bash
task <filter> dense
```

Examples:

```bash
task project:pickled-claude-plugins dense
task +followup dense
task dense  # bare = all pending, urgency-sorted
```

**Custom shape — when you need different columns or truncation:**

```bash
task <filter> export | jq -r '.[] | "\(.uuid[0:8]) [\(.project // "-")] \(.tags // [] | join(",")) \(.due // "-")  \(.description[0:80])"'
```

This produces ~120 chars/task. The `dense` report produces ~150 chars/task with column alignment. The jq form is for when you need a specific shape (e.g., longer description, different fields).

**Never:** raw `task list` with no filter. The 320+ pending tasks at default formatting is the largest single cost in your taskwarrior I/O.

## Single-field lookup

When you need ONE field of a known task, use `_get`:

```bash
task <uuid> _get description
task <uuid> _get project
task <uuid> _get tags
task <uuid> _get due
task <uuid> _get urgency
```

`_get` returns the raw field value, no metadata, no formatting. Roughly 10× denser than `task <uuid> info`.

**Never:** `task <uuid> info` when you only need one field. `info` dumps full metadata (entry/modified/uuid/status/etc.) — useful when triaging, wasteful for field lookup.

## Multi-task lookup

When inspecting several tasks at once, batch them through `export`:

```bash
task uuid:UUID1,UUID2,UUID3 export | jq -r '.[] | "\(.uuid[0:8])  [\(.project // "-")]  \(.description[0:120])"'
```

Or for richer output:

```bash
task uuid:UUID1,UUID2,UUID3 export | jq -r '.[] | "uuid: \(.uuid[0:8])  tags: \(.tags // [] | join(","))  due: \(.due // "-")  desc: \(.description[0:80])"'
```

**Never:** `task A info && echo --- && task B info && echo --- && task C info && ...`. This pattern has been observed at 25,000+ chars per call (vs ~600 chars for the batched export equivalent).

## Full-text search

`task list | grep` is unreliable because descriptions wrap across lines. Use export + jq:

```bash
# Search descriptions
task export | jq -r '.[] | select(.description | test("PATTERN"; "i")) | "\(.uuid[0:8])  \(.description[0:120])"'

# Search annotations
task export | jq -r '.[] | select(.annotations[]?.description | test("PATTERN"; "i")) | "\(.uuid[0:8])  \(.description[0:120])"'

# Search both
task export | jq -r '.[] | select((.description // "") + " " + ((.annotations // []) | map(.description) | join(" ")) | test("PATTERN"; "i")) | "\(.uuid[0:8])  \(.description[0:120])"'
```

The `"i"` flag makes the test case-insensitive. Drop it for case-sensitive matches.

## Description-length convention

When creating tasks (`task add ...`), aim for descriptions ≤ 100 chars. Long context goes in annotations:

```bash
# Good — short title, then annotate context
task add project:foo +bug "OAuth token refresh fails with 401 after 24h"
# `Created task <N>.` prints; grab the int ID, or look up by the most-recent-entry filter:
task entry.after:now-1m +bug uuid.short
# Then attach the longer context as an annotation:
task <uuid> annotate "Repro: lifecycle.test.ts:124 - happens only with refresh-token rotation enabled. Suspect cache key collision between user_id and session_id; see retro 2026-04-19."
```

```bash
# Bad — paragraph as description
task add project:foo +bug "OAuth token refresh fails with 401 after 24h. Repro: lifecycle.test.ts:124 — happens only with refresh-token rotation enabled. Suspect cache key collision between user_id and session_id; see retro 2026-04-19. Affects all users on the canary deployment, blocks GA. Fix: split cache namespace by token_type."
```

Soft target. Existing bloated descriptions decay naturally as tasks are completed or edited; no retroactive cleanup is required.

## Other dense idioms

- **Counts:** `task <filter> count` — single integer, ~3 chars.
- **Project summary:** `task summary` — project-by-project rollup, very dense.
- **Project list:** `task projects` — list of all project names with counts.
- **Tag list:** `task tags` — all tags with counts.

## Decision tree: what should I run?

| Need | Run |
|---|---|
| "What's pending in project X?" | `task project:X dense` |
| "How many open in project X?" | `task project:X count` |
| "What's on the backlog overall?" | `task summary` (then drill into a project with `dense`) |
| "What does task `<uuid>` look like?" | `task <uuid> info` (full metadata is fine for one task) |
| "What's the description of `<uuid>`?" | `task <uuid> _get description` |
| "What about these 5 tasks?" | `task uuid:A,B,C,D,E export \| jq -r '...'` |
| "Find tasks mentioning 'oauth'" | `task export \| jq -r '.[] \| select(.description \| test("oauth"; "i")) \| ...'` |
| "Add a task" | `task add project:X +tag "short title ≤100c"` then optionally `task <uuid> annotate "context"` |
| "Mark done" | `task <uuid> done` |

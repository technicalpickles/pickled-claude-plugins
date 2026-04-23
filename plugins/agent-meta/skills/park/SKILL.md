---
name: park
description: Save current work context for later resumption
allowed-tools: Bash(python3:*), Bash(mkdir:*), Bash(test:*)
---

# Park

Save the current work session so you (or another session) can resume it
later. Parks are written to a repo-keyed store at
`~/.claude/parks/<repo-slug>/`, shared across every worktree of a given
repo.

## Output Location

`~/.claude/parks/<repo-slug>/<YYYY-MM-DD>-<slug>.md`

- `<repo-slug>` is derived from the repo's main root (same slug across
  all worktrees) — returned by `park-resolve.py` as `repo_key`.
- `<slug>` is a short kebab-case topic slug: `jwt-auth`, `fix-login`,
  `park-resolve-rewrite`.
- If two parks get the same name on the same day, overwriting is
  intentional — the latest state wins.

You do NOT need to resolve locations from `CLAUDE.md` anymore. The store
is canonical.

## Workflow

### 1. Read injected session context

When this skill is invoked, the agent-meta plugin's PostToolUse hook
injects lines like:

```
Session ID: <uuid>
Transcript: /path/to/transcript.jsonl
```

into the tool result for the Skill call. Read them out. If no `Session
ID:` line appears (older install, hook disabled), treat the ID as
absent — do not fall back to a shell script (that legacy path is gone).
Without a session ID, `parent:` will stay null and `origin_session_id:`
will be written as `null`. Everything else still works.

### 2. Resolve git + parent context

Invoke `park-resolve.py`. It emits a single JSON blob with everything
the frontmatter needs:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/park-resolve.py" --session-id "<sid>"
```

Example output:

```json
{
  "repo_key": "-Users-tp-github-com-tp-pickled-claude-plugins",
  "branch": "feat/ccrpi-v2",
  "worktree": "/Users/tp/.../.worktrees/ccrpi",
  "is_worktree": true,
  "parent": "feature-jwt"
}
```

- `repo_key` → directory to write into.
- `branch` → frontmatter `branch:` field.
- `worktree` → frontmatter `worktree:` field. `null` outside a worktree.
- `parent` → if non-null, auto-fill `parent:` in the frontmatter. This
  is the slug of the park that was unparked in this session (the
  parent-chain breadcrumb); it links resumed work to its predecessor.

Drop `--session-id` if you don't have one — `parent` will come back
`null`.

### 3. Gather the park content

Ask yourself (and the user, where it's ambiguous):

1. **Topic slug.** Short kebab-case. This becomes the `slug:` field
   and part of the filename.
2. **What's done.** What the session actually finished.
3. **What's in progress.** Half-written code, partial refactors.
4. **Key decisions.** So they aren't re-litigated on resume. Short
   bullet with rationale.
5. **Relevant files.** Mark each `(new)`, `(modified)`, or `(read)`.
6. **Next steps.** Prioritized list. Someone resuming should know
   which step to start on.
7. **Resume prompt.** A copy-pasteable sentence the user (or another
   Claude) can paste into a fresh session to pick up cleanly.

### 4. Offer to link a plan or task

Judge from session context — no programmatic check required.

- **Plan:** If you've referenced a `docs/plans/*.md` file this session,
  ask the user: "Link this park to `docs/plans/<filename>`? (y/n)". If
  yes, populate `plan:` with the path.
- **Task:** If a taskwarrior UUID has come up (you ran `task <uuid>
  info`, or the user mentioned one), ask similarly and populate
  `task:`.

Both default to `null`. Don't guess if nothing obvious exists.

### 5. Write the park file

Use Python to drive `park_storage.Park.save()`. The frontmatter has a
stable order — `Park.save()` enforces it — so you don't need to worry
about the output shape as long as you populate the dataclass correctly.

Here's a complete, concrete example. Fill in the variables at the top
and run it as one Bash block:

```bash
python3 - <<'PYEOF'
import sys
from datetime import datetime
from pathlib import Path

PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
sys.path.insert(0, str(Path(PLUGIN_ROOT) / "lib"))
from park_storage import Park, ensure_park_dirs

# --- populated from park-resolve.py and the session ---
repo_key = "-Users-tp-github-com-tp-pickled-claude-plugins"
slug = "park-resolve-rewrite"
branch = "feat/agent-meta-repo-keyed-parks"
worktree = "/Users/tp/.../.worktrees/repo-keyed-parks"  # or None
parent = None            # or a slug like "jwt-auth"
plan = None              # or "docs/plans/2026-04-19-foo.md"
task = None              # or a taskwarrior UUID
origin_session_id = "abc123-session-uuid"  # or None

body = """## Current State

What's done, what's in progress, blockers.

## Key Decisions

- Decision with rationale.

## Relevant Files

- path/to/file.py (new)
- path/to/other.py (modified)

## Next Steps

1. Step one.
2. Step two.

## Resume Prompt

> Continue work on park-resolve-rewrite. See the park file for state.
"""

parked_at = datetime.now().isoformat(timespec="seconds")
active = ensure_park_dirs(repo_key)
filename = f"{parked_at[:10]}-{slug}.md"
path = active / filename

Park(
    slug=slug,
    status="parked",
    parked_at=parked_at,
    branch=branch,
    worktree=worktree,
    parent=parent,
    plan=plan,
    task=task,
    origin_session_id=origin_session_id,
    name=f"park-{slug}",
    body=body,
).save(path)

print(path)
PYEOF
```

The final `print(path)` gives you the absolute location to cite in the
resume message.

### 6. Report

After writing, tell the user:

```
Parked to `<absolute path>`.

To resume in a new session:
> unpark <slug>
```

Keep the `unpark <slug>` line copy-pasteable — it's the whole point.

## Body Format

The body (everything after the frontmatter `---`) is markdown. Use these
section headings so `unpark` can parse them consistently:

```markdown
## Current State
[What's done, what's in progress, blockers]

## Key Decisions
- [Decision 1 with rationale]

## Relevant Files
- path/to/file.ts (new)
- path/to/other.ts (modified)

## Next Steps
1. [Step]

## Resume Prompt
> [Copy-pasteable prompt to resume]
```

## Frontmatter Schema

`park_storage.Park.save()` writes these fields in this order. You only
need to populate them — the helper handles the on-disk format:

| Field               | Required | Value                                                  |
| ------------------- | -------- | ------------------------------------------------------ |
| `slug`              | yes      | kebab-case topic slug                                  |
| `status`            | yes      | `parked` (unpark flips to `unparked`)                  |
| `parked_at`         | yes      | ISO timestamp, seconds precision                       |
| `branch`            | yes      | current branch                                         |
| `worktree`          | no       | absolute worktree path or `null`                       |
| `unparked_at`       | no       | set by unpark, `null` on park                          |
| `parent`            | no       | slug of predecessor park, auto-filled from breadcrumb  |
| `plan`              | no       | `docs/plans/*.md` path if linked                       |
| `task`              | no       | taskwarrior UUID if linked                             |
| `origin_session_id` | no       | session that parked this                               |
| `name`              | no       | `park-<slug>` by convention                            |
| `type`              | yes      | `park` (default)                                       |

## Edge Cases

- **No session ID injected.** Write the park with
  `origin_session_id=None` and `parent=None`. Don't block.
- **Outside a git repo.** `park-resolve.py` still gives you a `repo_key`
  (the cwd slug). `branch` and `worktree` come back `null` — use them
  as-is.
- **Slug collision on the same day.** The second save overwrites the
  first; that's treated as a re-park of the same topic. If you really
  want distinct parks, pick a different slug.

---
name: devlog
description: Use when finishing a feature, fixing a notable bug, wrapping up a work session, or discovering something non-obvious (a gotcha, undocumented behavior, a workaround that took several tries, a constraint you only noticed after hitting it). Write the entry immediately, in the same turn - don't ask permission, don't offer, just do it. Do NOT use for routing, connecting, or moving notes (that's process-inbox), and do NOT use for one-off external-source capture (that's second-brain:capture).
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(npx @techpickles/sb:*)
  - Bash(${CLAUDE_PLUGIN_ROOT}/scripts/diagnose-sb.sh)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/check-sb-before-call.py"
---

# Devlog

## Overview

Devlog is continuous, point-in-time work commentary: what happened, why,
and anything surprising, captured as it happens instead of reconstructed
from memory at the end of a session. One narrative session note
accumulates every entry from the current session — no separate
"learnings" system, no til/cursed split, everything worth remembering goes
in the same place.

Processing (routing, connecting, daily-linking) happens later via
`/second-brain:process-inbox`. This skill only ever appends to the inbox.

**Write the entry now, in the same turn as whatever triggered it.** Don't
ask "should I log this?" and don't offer to — just write it. Asking is
exactly the failure mode that made the old `distill-conversation` flow get
skipped: by the time a session ends, you're mentally done, and a skip-able
step gets skipped.

## When to write

- Finished a feature or fixed a notable bug
- Wrapping up a work session
- Discovered something non-obvious: a gotcha, undocumented behavior, a
  workaround that took several tries, a constraint you only noticed after
  hitting it

## When not to write

- Routing, connecting, or moving existing notes — that's
  `/second-brain:process-inbox`
- Reading an external source and writing it up — that's
  `second-brain:capture`
- Trivially obvious or one-off details you'd never reach for again
- Project-specific context (a config value, a repo convention) — that
  belongs in Claude Code's own memory system, not the vault

## Step 1: Load Configuration

Don't preflight-check sb availability — just run it:

```bash
npx @techpickles/sb config default && npx @techpickles/sb config vaults
```

If this fails, run `${CLAUDE_PLUGIN_ROOT}/scripts/diagnose-sb.sh` and follow
its guidance rather than re-deriving the checks by hand.

If no default vault is configured:
```
Second brain not configured. Run /second-brain:setup first.
```

## Step 2: Find or create this session's devlog note

Every entry from the current session lands in ONE note. Never create a
second devlog note for a session that already has one.

1. Collect session context:
   - Current repo and branch, if in a worktree
   - Current bean ID, if applicable
   - Short session id (first 8 characters of the session UUID)
   - Source string format: `claude-code session {short-id} ({repo}, branch {branch}, bean {id})`
     (omit fields that don't apply, matching the format the retired
     `distill-conversation` command used)

2. **Check your own memory first.** If you already created or appended to
   this session's devlog note earlier in this same conversation, you
   already have its path in context — go straight to Step 2a and append.
   No CLI search needed: this is the same mechanism
   `second-brain:insight` uses for its own accumulating session note
   ("if the session file already exists, was created in an earlier call
   in this same conversation, append").

3. **If this is the first devlog entry this session,** go to Step 2b to
   create the note, and keep its path in mind for the rest of the
   session.

4. **Fallback, only if you've genuinely lost track of the note's path**
   (e.g. a context compaction wiped your memory of this session) —
   resolve a real path instead of guessing:
   - `npx @techpickles/sb vault obsidian` — parse the JSON for the
     top-level `inbox` field (the inbox subfolder name, e.g. `📫 Inbox`).
     This is the precomputed field `sb note create` itself resolves the
     inbox folder from — don't parse `app.newFileFolderPath` directly,
     since that skips the Zettelkasten Prefixer plugin's folder override
     (`inbox` is `zkPrefixer?.folder ?? app?.newFileFolderPath`) and can
     point at the wrong folder.
   - `npx @techpickles/sb inbox list --detail` — parse the JSON, look for
     the entry with `type: session-notes` whose `source` field contains
     the current short session id, and take its `filename`
   - Combine: `~/.claude/vaults/{vault-name}/{inbox}/{filename}` is the
     real, readable/editable path. `inbox list --detail` only ever
     returns a bare filename, never a resolvable path on its own.
   - With the resolved path in hand, go to Step 2a and append. If the
     `inbox list --detail` search finds no entry matching the current
     session id (genuinely nothing to recover), fall through to Step 2b
     and create the note instead.

### Step 2a: Append to the existing note

Read the note, append one new bullet to the end of its body (format
below) using the Edit tool. Don't touch its frontmatter.

### Step 2b: Create the note

Staged and written in one unsandboxed Bash call:

```bash
STAGE=$(mktemp)
cat > "$STAGE" <<'EOF'
- {HH:MM} {entry}
EOF
npx @techpickles/sb note create \
  --title "Session: {topic}" \
  --source "claude-code session {short-id} ({repo}, branch {branch}, bean {id})" \
  --content "$(cat "$STAGE")"
rm -f "$STAGE"
```

Run this with the Bash tool's `dangerouslyDisableSandbox: true` set from
the start, not as a retry. Two reasons, same as the retired
distill-conversation flow documented: vault paths symlink outside the
sandbox's writable allowlist (a sandboxed attempt always EPERMs), and
`$TMPDIR` resolves to a *different path* under
`dangerouslyDisableSandbox: true` than under the normal sandbox — staging
and reading have to happen in the same call under the same mode or the
read can miss the file. The staged file must be a fresh `mktemp` path,
not a fixed filename: `$TMPDIR` is shared across every Claude Code
session on the machine, and a fixed-name file can be overwritten or read
by a stale write from a different session.

`sb note create` prints JSON with a `path` field. If stdout has anything
before the `{` (e.g. a stray `npm warn ...` line from the caller's own
`.npmrc`), extract the JSON substring starting at the first `{` rather
than parsing the whole stdout blob.

`sb note create` only ever writes `captured`, `source`, `repo`, `branch`,
`commit` to frontmatter — it has no `--type`/`--status` flag, and `repo`/
`branch` come out as the literal `none`/`none` (devlog's `--source` format
doesn't match `sb`'s own `conversation:repo=...,branch=...` parsing
convention). Read the file back at the path just parsed to preserve the
exact frontmatter sb wrote, then Edit it:
- add `status: raw`
- add `type: session-notes`
- replace the `repo: none` line sb wrote with `repo: {repo-name}` (from
  git context if available) — don't add a second `repo:` line
- replace the `branch: none` line sb wrote with `branch: {branch-name}`
  (from git context if available) — don't add a second `branch:` line
- add `bean: {bean-id}` (from git context if available)
- keep `source` as sb wrote it — the `claude-code session ...` string
  already covers provenance for devlog's format
- keep `captured` as sb wrote it

Without this fixup, the note is invisible both to this skill's own
"check memory / find existing note" logic (Step 2, above) and to
`process-inbox`'s stage 3a filter, which requires exactly `status: raw` +
`type: session-notes` to ever pick the note up.

## Entry format

One bullet per entry, each with a wall-clock timestamp:

```markdown
- {HH:MM} {what happened, why, anything surprising — one to three
  sentences, standalone enough to make sense without the surrounding
  conversation}
```

Prose, not a title. Write it like a short journal line, not a commit
message.

## Constraints

- One note per session — append, never create a second one for the same
  session.
- Never ask before writing, never present a summary and wait for a
  selection.
- Don't route, connect, move the note, or touch the daily note. That's
  entirely `process-inbox`'s job, later.
- Frontmatter stays `status: raw`, `type: session-notes` for the life of
  the session. `process-inbox` owns every status transition after that.

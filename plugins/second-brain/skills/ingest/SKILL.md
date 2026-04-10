---
name: ingest
description: Split a raw session notes file into individual insight notes in the inbox. Stage 1 of the processing pipeline.
allowed-tools:
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(npx @techpickles/sb:*)
---

# Ingest Stage

Split a raw session notes file (type: `session-notes`) into individual insight notes.

See `references/pipeline.md` for stage definitions and status flow.

## Input

A session notes file in the inbox with `status: raw` and `type: session-notes`.

## Process

1. Read the session notes file
2. Extract each bullet point as a separate insight
3. For each insight, create a new note via `sb note create --source auto --title "{insight title}"` with:
   - `status: ingested`
   - `type: insight`
   - `source-session: {original session filename}`
   - Inherited metadata: `repo`, `branch`, `bean` from the parent session file
4. Write the note body (the bullet text, cleaned up into a sentence or short paragraph) using the Write tool
5. Update the original session file's status to `ingested` using the Edit tool (change `status: raw` to `status: ingested` in frontmatter)

## Output

- N new insight notes in the inbox, each with `status: ingested`
- Original session file updated to `status: ingested`

## Constraints

- Preserve all provenance metadata from the parent session file
- Each extracted note gets its own zettelkasten timestamp (via sb)
- The `source-session` field links back to the original session file
- Don't merge or combine bullets. One bullet, one note.
- Skip empty or trivial bullets (single words, fragments)

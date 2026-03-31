---
name: link-daily
description: Link a processed note to today's daily note. Stage 5 of the processing pipeline.
allowed-tools:
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(npx @techpickles/sb:*)
---

# Link Daily Stage

Add an entry for the processed note to today's daily note.

See `references/pipeline.md` for stage definitions and status flow.
See `references/daily-linking.md` for linking mechanics.

## Input

A note with `status: connected`. (The connect skill sets this even when qmd is unavailable and connections are skipped.)

## Process

1. Link to daily note:
   ```bash
   npx @techpickles/sb daily append \
     --section "Links" \
     --content "- [[{filename without .md}]] - {brief description}"
   ```

2. Update status to `complete`

If daily note linking fails (sb returns error), log the error but don't fail. The note is already processed. Set status to `complete` anyway.

## Output

- Entry added to today's daily note
- `status: complete`

## Constraints

- Don't fail the pipeline if daily linking fails
- Use the note's title for the brief description
- sb handles daily note creation if it doesn't exist

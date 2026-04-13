---
name: connect
description: Find related notes via semantic search and weave links. Stage 4 of the processing pipeline.
allowed-tools:
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(which:qmd)
  - Bash(qmd:query *)
  - Bash(qmd:collection list)
  - Bash(qmd:get *)
  - Bash(qmd:status)
---

# Connect Stage

Find related notes via semantic search (qmd) and weave forward/backward links.

See `references/pipeline.md` for stage definitions and status flow.
See `references/connecting.md` for the connection discovery algorithm.

## Input

A routed note with `status: routed`.

## Process

1. Check qmd availability:
   ```bash
   which qmd
   ```
   If not available, log "Skipped connections: qmd not available", set `status: connected`, and return.

2. Extract query terms from the note's title and body

3. Run semantic search:
   ```bash
   qmd query "{terms}" -c {collection} -n 15 --json
   ```

4. Filter and rank per `references/connecting.md`:
   - Remove self
   - Remove already-linked notes
   - Remove daily notes
   - Remove low-relevance results (below 30%)

5. If candidates found, present to human (when called by orchestrator):
   - Show candidates with scores and snippets
   - Let user multi-select which to connect

6. For selected connections:
   - Add `## Related` section to the note with wiki-links
   - Offer backlink weaving for notes that have See Also/Related/TK sections

7. Update status to `connected`

## Output

- Note with `## Related` section added (if connections found)
- `status: connected`

## Constraints

- Graceful skip if qmd unavailable (always log that it was skipped)
- The note being processed won't be in qmd's index yet. Search FROM its content, not for it.
- Don't add connections the user didn't approve
- Backlink weaving is optional (offer, don't force)

---
name: route
description: Analyze an enriched note and route to the best vault destination. Stage 3 of the processing pipeline.
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/*.md)
  - Read(~/.claude/vaults/**/.routing-memory.md)
  - Write(~/.claude/vaults/**/.routing-memory.md)
  - Edit(~/.claude/vaults/**/.routing-memory.md)
  - Bash(npx @techpickles/sb:*)
---

# Route Stage

Analyze an enriched note against routing memory, vault rules, and generic signals. Move to destination or mark for review.

See `references/pipeline.md` for stage definitions and status flow.
See `references/routing.md` for the scoring algorithm.
See `references/routing-memory.md` for the correction and learning loop.

## Input

An enriched note in the inbox with `status: enriched`.

## Process

1. Load routing context:
   - Read `.routing-memory.md` from vault root (create with defaults if missing)
   - Read vault CLAUDE.md for disambiguation rules
   - Run `sb vault structure` for available destinations
   - Run `sb note context --note "{note-path}"` for keywords and signals

2. Score destinations (priority order):
   a. Check `.routing-memory.md` corrections for matching topics/keywords
   b. Check `.routing-memory.md` learned patterns
   c. Apply vault CLAUDE.md disambiguation rules
   d. Apply generic signal scoring (per `references/routing.md`)

3. Apply threshold:
   - Score >= `auto-route-threshold`: auto-route, move file, set `status: routed`
   - Score < threshold: set `status: pending-review`, return without moving

4. If auto-routing, move the file:
   ```bash
   npx @techpickles/sb note move --from "{note-path}" --to "{destination}/"
   ```
   Update frontmatter: `status: routed`

5. If pending-review, present suggestions to human (when called by orchestrator):
   - Show top 2-3 destinations with scores and reasoning
   - Include "Leave in inbox" option
   - If user overrides suggestion, capture correction to `.routing-memory.md`

## Capturing Corrections

When the user picks a destination different from the top suggestion:

1. Ask: "Quick note on why {chosen} over {suggested}?"
2. Append to `## Corrections` in `.routing-memory.md`:
   ```
   - {YYYY-MM-DD}: "{note title}" routed to "{suggested}", corrected to "{chosen}"
     Reason: {user's reason}
   ```

## Output

- Note moved to destination with `status: routed`, OR
- Note marked `status: pending-review` for human input

## Constraints

- Only suggest destinations from `sb vault structure` output
- Always include "Leave in inbox" for pending-review notes
- Show reasoning for all suggestions
- Capture corrections on every override (this is how routing improves)

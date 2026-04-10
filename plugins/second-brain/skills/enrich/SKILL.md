---
name: enrich
description: Turn an ingested insight into a proper zettelkasten note with clean prose. Stage 2 of the processing pipeline.
allowed-tools:
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
---

# Enrich Stage

Turn an ingested insight note into a proper zettelkasten note with a clean title, well-written prose, and complete frontmatter.

See `references/pipeline.md` for stage definitions and status flow.
See `references/note-patterns.md` for the Insight Note template.
See `references/zettelkasten.md` for naming conventions.

## Input

An insight note in the inbox with `status: ingested` and `type: insight`.

## Process

1. Read the ingested note
2. Rewrite the body as clean prose (1-3 paragraphs) using the Insight Note pattern from `references/note-patterns.md`
3. Improve the title if needed (should be descriptive and specific)
4. Add a `## Context` section with brief description of what session produced this
5. Update status to `enriched` in frontmatter
6. Write the updated note using the Write tool (read first, then rewrite)

## Output

The same file, now with:
- Clean, well-written prose body
- Descriptive title
- Context section
- `status: enriched`

## Constraints

- Don't create a new file. Enrich in place.
- Preserve all existing frontmatter fields (provenance, source-session, etc.)
- The note should be useful months later to someone with no context
- Keep it concise. 1-3 paragraphs, not an essay.

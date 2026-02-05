# Daily Note Linking Reference

When capturing notes via `/insight` or `/distill-conversation`, link them back to today's daily note so there's a record of "what was captured today."

## When to Link

Link to daily note when:
- A new note is captured via `/insight` or `/distill-conversation`
- The daily note exists and has a `## Links` section (or can have one added)

Do NOT link when:
- Processing daily notes (`/process-daily`) - that's a different workflow
- The note was already extracted from the daily note (would be circular)

---

## Step 1: Find Today's Daily Note

Get daily note configuration from vault's `.obsidian/daily-notes.json`:

```bash
# Read daily notes folder from config
cat "{vault}/.obsidian/daily-notes.json" 2>/dev/null
```

Parse the `folder` field. If config doesn't exist, check `~/.claude/second-brain.md` for `Daily notes:` setting.

Construct today's path:
```bash
date +"%Y-%m-%d"
# Result: {vault}/{folder}/{YYYY-MM-DD}.md
```

If the daily note doesn't exist, skip linking (don't create it).

---

## Step 2: Check for Links Section

Read the daily note and look for `## Links` section.

**If `## Links` exists:** Append to it.

**If `## Links` doesn't exist but daily note does:** Add the section in the appropriate location (after `## Action Items` if present, otherwise near the top).

---

## Step 3: Format the Link Entry

Use Obsidian wiki-link syntax with description:

```markdown
- [[{filename}]] - {brief description}
```

Where:
- `{filename}` is the Zettelkasten filename without `.md` extension
- `{brief description}` is a 3-8 word summary of what the note captures

### Examples

```markdown
- [[202602051430 redis-session-caching]] - Redis vs Memcached for session storage
- [[202602051445 golf-green-prompting-metaphor]] - Prompting as miniature golf geography
- [[202602051500 pr-review-blast-radius]] - Review large PRs by blast radius, not lines
```

### Description Guidelines

Good descriptions:
- State the insight topic, not just keywords
- Help future-you understand what this is about
- Are scannable in a list

| Good | Bad |
|------|-----|
| "Redis vs Memcached for session storage" | "Redis" |
| "Prompting as miniature golf geography" | "prompting metaphor" |
| "Review large PRs by blast radius" | "PR review thoughts" |

---

## Step 4: Append to Daily Note

Insert the new link at the end of the `## Links` section:

```bash
# Pseudo-approach using Edit tool:
# 1. Find the line with "## Links"
# 2. Find the next ## header or EOF
# 3. Insert new link line before that boundary
```

**Implementation:**

If `## Links` section exists with content:
```markdown
## Links

- [[202602051400 existing-note]] - existing description
- [[202602051430 new-note]] - new description  ← append here
```

If `## Links` section exists but empty:
```markdown
## Links

- [[202602051430 new-note]] - new description  ← add first entry
```

If adding `## Links` section (after `## Action Items`):
```markdown
## Action Items

- [ ] Some task

## Links

- [[202602051430 new-note]] - new description  ← new section

## Notes
```

---

## Step 5: Confirm Linking

After appending, confirm:

```
✓ Linked to daily note: Fleeting/{date}.md
```

If daily note doesn't exist or linking fails:
```
(Daily note not found - skipping link)
```

Don't fail the capture workflow if linking fails - the note is already saved.

---

## Implementation Pattern

When integrating into a command:

```markdown
## After Capture: Link to Daily Note

Follow `references/daily-linking.md` algorithm:

1. Find today's daily note path from config
2. If daily note exists, read it
3. Locate or create `## Links` section
4. Append wiki-link with description
5. Confirm or note skipped

This step is best-effort - don't fail capture if linking fails.
```

---

## Batch Linking

When capturing multiple notes (e.g., `/distill-conversation`), link them all in a single batch:

```markdown
## Links

- [[202602051430 insight-one]] - first insight description
- [[202602051432 insight-two]] - second insight description
- [[202602051434 insight-three]] - third insight description
```

This avoids multiple edits to the daily note.

---

## Constraints

- **Best-effort** - Don't fail capture if linking fails
- **No duplicates** - Check if link already exists before adding
- **Wiki-link format** - Use `[[filename]]` not `[text](path)`
- **Descriptive text** - Always include meaningful description
- **Preserve order** - Append to end of Links section (chronological)

---
description: Connect a note to related notes in your vault using semantic search
argument-hint: [path/to/note.md]
allowed-tools:
  - Read(~/.claude/second-brain.md)
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/.obsidian/*.json)
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(which:qmd)
  - Bash(qmd:query *)
  - Bash(qmd:collection list)
  - Bash(qmd:get *)
  - Bash(qmd:status)
  - Bash(ls:*)
  - Bash(date:*)
  - Bash(find:*)
  - Bash(stat:*)
---

# Connect Notes

Connect a note to related notes in your vault, or discover connection opportunities across the vault.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault name and path.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to access the vault (e.g., `~/.claude/vaults/primary`).

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/connecting.md` for connection discovery algorithm

## Step 2: Check Prerequisites

Follow `references/connecting.md` prerequisites:

```bash
which qmd
```

If qmd is not available:
```
qmd is not installed. Connection discovery requires qmd for semantic search.
Install via: bun add -g qmd
Then configure: qmd collection add ~/path/to/vault --name second-brain
```

Verify collection exists:
```bash
qmd collection list
```

Load collection name from `~/.claude/second-brain.md` (`qmd_collection` setting). Default: `second-brain`.

## Step 3: Determine Mode

**If argument provided (note path):** Go to Step 4 (Connect Specific Note)
**If no argument:** Go to Step 7 (Connection Gardening)

---

## Connect Specific Note

### Step 4: Load Target Note

Resolve the path. Accept:
- Vault-relative path: `Areas/gusto/202501121430 kafka-consumer-groups.md`
- Absolute path: `~/Vaults/pickled-knowledge/.../file.md`
- Just the filename: `202501121430 kafka-consumer-groups.md` (search for it)

If just a filename, find it:
```bash
find "{vault}" -name "{filename}" -type f 2>/dev/null
```

Read the note content.

If note not found:
```
Note not found: {path}
Check the path and try again.
```

### Step 5: Run Connection Discovery

Follow the full `references/connecting.md` algorithm:

1. Extract query terms from the note's title and body
2. Run `qmd query "{terms}" -c {collection} -n 15 --json`
3. Filter noise (self, already-linked, low-relevance, daily notes)
4. Enrich candidates (check for See Also, Related, TK sections)
5. Rank by connection value
6. Present candidates for multi-select

### Step 6: Apply Connections

Based on user selection:

1. Add forward links (## Related section) to the target note
2. Offer backlink weaving for selected notes
3. Confirm what was connected

Done. Skip to Step 10.

---

## Connection Gardening (No-Arg Mode)

### Step 7: Find Connection Opportunities

Scan the vault for notes that might benefit from connections:

**Priority 1: Recent inbox notes without connections**
```bash
# Notes in inbox without ## Related section
find "{vault}"/📫\ Inbox/ -name "*.md" -type f -mtime -30 2>/dev/null
```

For each, check if it has a `## Related` section. Notes without one are candidates.

**Priority 2: Notes with TK placeholders**
Search for notes containing `TK` in See Also or Related sections:
```bash
qmd query "TK see also related" -c {collection} -n 10 --json
```

Or use grep if qmd doesn't help here:
```bash
find "{vault}" -name "*.md" -exec grep -l "TK" {} \; 2>/dev/null | head -20
```

**Priority 3: Recently captured notes with no outgoing wiki-links**
```bash
# Recently modified notes
find "{vault}" -name "*.md" -type f -mtime -7 2>/dev/null | head -20
```

For each, check if it has any `[[wiki-links]]` in the body.

### Step 8: Present Opportunities

```
Connection gardening: found {N} notes that could use connections:

Inbox notes without connections:
1. **{title}** - captured {date}, no Related section
2. **{title}** - captured {date}, no Related section

Notes waiting for connections (TK):
3. **{title}** - has TK in See Also section
4. **{title}** - has TK placeholder

Recent notes with no outgoing links:
5. **{title}** - modified {date}, no wiki-links
```

Use AskUserQuestion:
**Question:** "Which note would you like to connect?"
**Options:** Top 3-4 candidates, plus "None, I'm done gardening"

### Step 9: Connect Selected Note

When user picks a note, run the same flow as Steps 4-6 (Connect Specific Note):
1. Read the selected note
2. Run connection discovery
3. Present candidates
4. Apply connections

After connecting, offer to continue gardening:
```
Want to connect another note?
(A) Yes, show me more opportunities
(B) Done for now
```

If (A), loop back to Step 7 with already-connected notes excluded.

---

## Step 10: Summary

After all connections are done:

```
Connection session complete:
- {N} notes connected
- {M} forward links added
- {K} backlinks woven

Run /second-brain:connect again anytime to tend the garden.
```

## Constraints

- **User always chooses** - Present candidates, never auto-connect
- **Best-effort** - Skip gracefully if qmd fails or returns nothing
- **Wiki-link format** - Use `[[filename]]` not `[text](path)`
- **Descriptive links** - Always include relationship description
- **Respect structure** - Append to existing sections, don't reorganize
- **Gardening is optional** - If no opportunities found, say so and exit

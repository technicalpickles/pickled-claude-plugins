---
description: Extract and capture multiple insights from this conversation
allowed-tools:
  - Read(~/.claude/second-brain.md)
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/.obsidian/*.json)
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Bash(ls:*)
  - Bash(date:*)
  - Bash(git rev-parse:*)
  - Bash(git branch:*)
  - Bash(mv:*)
---

# Distill Conversation

Review the current conversation and extract insights worth capturing.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault name and path.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to access the vault (e.g., `~/.claude/vaults/primary`).

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/zettelkasten.md` for naming
- `references/note-patterns.md` for Insight Note template
- `references/routing.md` for destination matching

## Step 2: Review the Conversation

Scan through the conversation looking for:

1. **Architecture decisions** - Choices about design, technology, structure
2. **Debugging patterns** - Root causes found, diagnostic approaches
3. **Domain knowledge** - Business logic, system behavior
4. **Process improvements** - Better ways of doing things
5. **Key learnings** - Surprising findings, corrected misunderstandings

## Step 3: Present Findings

Show what you found:

```
Reviewing this conversation...

Found {N} potential insights worth capturing:

1. **{Category}**: {Brief description}
   → {Why this might be worth keeping}

2. **{Category}**: {Brief description}
   → {Why this might be worth keeping}

3. **{Category}**: {Brief description}
   → {Why this might be worth keeping}
```

If nothing worth capturing:
```
Reviewed this conversation - no notable insights to capture.
The conversation was mostly {operational/routine/exploratory without conclusions}.
```

## Step 4: Let User Select

Use AskUserQuestion with multi-select enabled:

**Question:** "Which insights should I capture?"

**Options:** List each insight (up to 4, mention others)

Include "None - skip capture" option.

## Step 5: Capture Selected

For each selected insight, follow `/second-brain:insight` flow:
1. Gather provenance
2. Generate Zettelkasten filename
3. Write to inbox with Insight Note pattern
4. Show confirmation

```
Capturing {N} insights...

✓ {filename1}
✓ {filename2}
✓ {filename3}

All captured to inbox.
```

## Step 6: Batch Routing

Load `references/routing.md` and analyze all captured notes together.

**1. Discover vault structure once:**
```bash
ls -d "{vault}"/*Areas*/*/     2>/dev/null
ls -d "{vault}"/*Resources*/*/ 2>/dev/null
ls -d "{vault}"/*Projects*/*/  2>/dev/null
```

**2. Load disambiguation rules from vault CLAUDE.md:**
- Find `### Disambiguation:` sections
- Extract key questions, category tables, edge case mappings
- These override generic matching for semantically similar areas

**3. Score each captured note:**

*Apply disambiguation rules first (if loaded):*
- Check edge case mappings (explicit rules)
- Apply key question matches (+25% boost)
- Apply category table matches (+15% boost)
- Apply disambiguation mismatch penalty (-20%)

*Then apply generic signals:*
- Keyword match, related notes, PARA fit, recency

**4. Present batch summary table:**
```
Analyzing captured notes for routing...

| Note | Suggested Destination | Confidence | Rule Applied |
|------|----------------------|------------|--------------|
| "insight about caching" | Areas/AI/agentic development/ | High (82%) | - |
| "tmux-comma-parsing" | Areas/tool sharpening/ | High (95%) | edge case |
| "debugging approach" | (leave in inbox) | None | - |

Routing explanations:
- "insight about caching" → keyword "claude" matches, related notes exist
- "tmux-comma-parsing" → vault rule: tmux config → tool sharpening
- "debugging approach" → no strong destination match
```

**5. Use AskUserQuestion:**

**Question:** "How should I route these?"

**Options:**
1. Route all as suggested (Recommended)
2. Route individually (I'll ask about each)
3. Leave all in inbox for now

**6. Execute based on selection:**
- "Route all": Move files with confidence > 20% to suggested destinations
- "Route individually": Use AskUserQuestion for each note separately
- "Leave all": Skip routing, notes stay in inbox

```bash
# For each routed note:
mv "{inbox}/{filename}" "{vault}/{destination}/"
```

**Important:** Only suggest destinations that exist (from `ls` output). Never suggest paths that weren't discovered.

## Constraints

- **Be selective** - Only genuinely valuable insights
- **Categorize clearly** - Help user understand knowledge type
- **Batch efficiently** - Don't make user go through many dialogs
- **Clean prose** - Each insight standalone, useful months later
- **Zettelkasten naming** - Must use `YYYYMMDDHHMM title.md`

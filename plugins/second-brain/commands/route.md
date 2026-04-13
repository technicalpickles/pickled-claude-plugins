---
description: Route notes from inbox to appropriate vault destinations
argument-hint: [filename | "all"]
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/.routing-memory.md)
  - Edit(~/.claude/vaults/**/.routing-memory.md)
  - Bash(npx @techpickles/sb:*)
---

# Route Notes

Route notes from inbox to appropriate destinations in your vault.

## Step 1: Load Configuration

Verify sb CLI availability:

```bash
npx @techpickles/sb --version
```

If this fails:
```
sb CLI is required but not available. Install Node.js and npm, then try again.
Or install globally for faster execution: npm i -g @techpickles/sb
```

Load configuration:

```bash
npx @techpickles/sb config default
npx @techpickles/sb config vaults
```

If no vault configured:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to Read vault files (e.g., `~/.claude/vaults/primary/CLAUDE.md`).

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/routing.md` for routing algorithm
- `references/sb-cli.md` for sb command reference
- `references/routing-memory.md` for routing correction format

## Step 2: Identify Notes to Route

**If argument is a filename:**
Look for that file in inbox. If not found, search vault.

**If argument is "all":**
List all files in inbox for batch routing.

**If no argument:**
List inbox contents and let user select:

```bash
npx @techpickles/sb inbox list
```

Example output:
```json
{
  "notes": [
    {
      "filename": "202601251430 redis-session-caching.md",
      "timestamp": "202601251430",
      "title": "redis-session-caching"
    },
    {
      "filename": "202601251445 claude-code-hooks.md",
      "timestamp": "202601251445",
      "title": "claude-code-hooks"
    }
  ]
}
```

Present to user:
```
Notes in inbox:
1. 202601251430 redis-session-caching.md
2. 202601251445 claude-code-hooks.md
3. 202601251500 debugging-approach.md

Which note(s) would you like to route?
```

Use AskUserQuestion with multi-select to let user choose.

## Step 3: Discover Vault Structure

```bash
npx @techpickles/sb vault structure
```

Example output:
```json
{
  "areas": [
    "Areas/AI/agentic development",
    "Areas/tool sharpening"
  ],
  "resources": [
    "Resources/software engineering",
    "Resources/mental models"
  ],
  "projects": [
    "Projects/pickletown",
    "Projects/claude-plugins"
  ]
}
```

Build destination map from returned paths only.

## Step 4: Load Disambiguation Rules

Read the vault's `CLAUDE.md` via symlink (e.g., `~/.claude/vaults/primary/CLAUDE.md`) and look for `### Disambiguation:` sections.

If found, extract:
- **Key questions** - Decision heuristics for each area
- **Category tables** - Lists of tools/topics that belong in each area
- **Edge case mappings** - Explicit routing rules for ambiguous cases

These rules override generic matching for semantically similar areas.

## Step 4b: Load Routing Memory

Read `.routing-memory.md` from vault root (via symlink path, e.g. `~/.claude/vaults/primary/.routing-memory.md`). If it doesn't exist, skip this step (no corrections yet).

If the file exists, parse:
- `auto-route-threshold` from frontmatter
- `## Corrections` entries with:
  - Date, original suggestion, user's correction, and reason
  - Extract patterns: what topics have been corrected before
- `## Patterns Learned` entries:
  - Stable routing rules distilled from corrections
  - Pattern → destination mappings

Store this context for Step 5 scoring.

## Step 5: Analyze and Score

For each selected note, follow `references/routing.md` algorithm:

1. **Extract signals** using sb:

```bash
npx @techpickles/sb note context --note "inbox/202601251430 redis-session-caching.md"
```

Example output:
```json
{
  "keywords": ["redis", "session", "caching"],
  "category": "architecture",
  "relatedNotes": [
    {
      "path": "Areas/AI/agentic development/Redis patterns.md",
      "similarity": 0.85
    }
  ],
  "sourceContext": {
    "origin": "slack",
    "thread": "https://..."
  }
}
```

2. **Apply routing memory** (if loaded in Step 4b):
   - Check if any correction matches this note's topic/keywords (exact or close match). If so, strongly favor the corrected destination (+40% to that destination).
   - Check if any learned pattern matches the note's topic/keywords. If so, boost that destination (+20%).
   - These take precedence over generic signals but come after exact topic matches from corrections.

3. **Apply disambiguation rules** (if loaded):
   - Check edge case mappings first (explicit rules)
   - Apply key question matches (+25% boost)
   - Apply category table matches (+15% boost)
   - Apply disambiguation mismatch penalty (-20%)

4. **Score with generic signals:**
   - Keyword match in folder name (40%)
   - Related notes exist in folder (30%)
   - PARA category fit (20%)
   - Recency of folder activity (10%)

5. **Calculate confidence:**
   - High (80-100%): Strong match, often with disambiguation support
   - Medium (50-79%): Partial match
   - Low (20-49%): Weak signals
   - None (<20%): Leave in inbox

## Step 6: Present Recommendations

**For single note:**
```
Routing suggestions for "202601251430 redis-session-caching.md":

1. **Areas/AI/agentic development/** (85% - High)
   → Matches keywords: "caching", "session"
   → Related note exists: "Redis patterns.md"

2. **Resources/software engineering/** (48% - Low)
   → Generic architecture fit

3. **Leave in Inbox** (Safe default)
```

When disambiguation rules influenced the result:
```
1. **Areas/tool sharpening/** (95% - High)
   → Vault rule: "tmux config syntax" → tool sharpening
   → Key question: "Is this about MY machine?" → YES
```

Use AskUserQuestion with options from discovered paths.

**For multiple notes:**
```
| Note | Suggested Destination | Confidence | Rule Applied |
|------|----------------------|------------|--------------|
| "redis-session-caching" | Areas/AI/agentic development/ | High (85%) | - |
| "tmux-comma-parsing" | Areas/tool sharpening/ | High (95%) | edge case |
| "debugging-approach" | (leave in inbox) | None | - |
```

Use AskUserQuestion:
1. Route all as suggested (Recommended)
2. Route individually
3. Leave all in inbox

## Step 7: Execute Moves

For each note being routed:

```bash
npx @techpickles/sb note move --from "inbox/202601251430 redis-session-caching.md" --to "Areas/AI/agentic development/"
```

sb handles the filesystem operation and returns confirmation.

## Step 8: Report Success

```
✓ Moved "redis-session-caching.md" → Areas/AI/agentic development/
✓ Moved "claude-code-hooks.md" → Areas/AI/agentic development/
○ Left "debugging-approach.md" in inbox (no clear destination)

3 notes processed: 2 routed, 1 remaining in inbox
```

## Step 8b: Capture Corrections

For each note where the user chose a destination different from the top suggestion:

1. Read `.routing-memory.md` from vault root. If it doesn't exist, create it with defaults:
   ```markdown
   ---
   auto-route-threshold: 70
   ---

   ## Corrections

   ## Patterns Learned
   ```

2. Ask: "Quick note on why {chosen} over {suggested}?" (keep it to one sentence)

3. Append the correction to `## Corrections`:
   ```
   - {YYYY-MM-DD}: "{note title}" routed to "{suggested}", corrected to "{chosen}"
     Reason: {user's reason}
   ```

4. Write/Edit the updated file using the Edit tool

Example correction entry:
```markdown
- 2026-03-31: "tmux conditional parsing" routed to "Resources/software engineering/", corrected to "Areas/tool sharpening/"
  Reason: tmux is a personal tool config, not a programming pattern
```

This correction becomes available in Step 4b of future routing operations, feeding the learning loop.

## Examples

```bash
# Route a specific note
/second-brain:route redis-session-caching

# Route all inbox notes
/second-brain:route all

# Interactive: list inbox and select
/second-brain:route
```

## Constraints

- **Never suggest non-existent paths** - Only use `vault structure` output
- **Always include inbox option** - Safe default for uncertain cases
- **Show reasoning** - Users should understand why
- **Preserve filenames** - Don't rename when moving
- **Two-level depth max** - Don't suggest deeply nested paths
- **Respect emoji prefixes** - Use exact folder names from filesystem

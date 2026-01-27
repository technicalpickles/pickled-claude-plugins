---
description: Route notes from inbox to appropriate vault destinations
argument-hint: [filename | "all"]
allowed-tools:
  - Read(~/.claude/second-brain.md)
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/*.md)
  - Bash(ls:*)
  - Bash(mv:*)
---

# Route Notes

Route notes from inbox to appropriate destinations in your vault.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault name and path.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to access the vault (e.g., `~/.claude/vaults/primary`).

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/routing.md` for routing algorithm

## Step 2: Identify Notes to Route

**If argument is a filename:**
Look for that file in inbox. If not found, search vault.

**If argument is "all":**
List all files in inbox for batch routing.

**If no argument:**
List inbox contents and let user select:

```bash
ls "{vault}/{inbox}/"
```

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
ls -d "{vault}"/*Areas*/*/     2>/dev/null
ls -d "{vault}"/*Resources*/*/ 2>/dev/null
ls -d "{vault}"/*Projects*/*/  2>/dev/null
```

Build destination map from actual paths only.

## Step 4: Analyze and Score

For each selected note, follow `references/routing.md` algorithm:

1. **Extract signals** from note content:
   - Keywords from title (after Zettelkasten prefix)
   - Key terms from body
   - Category (architecture, debugging, tool, etc.)
   - Source context from frontmatter

2. **Score each destination:**
   - Keyword match in folder name (40%)
   - Related notes exist in folder (30%)
   - PARA category fit (20%)
   - Recency of folder activity (10%)

3. **Calculate confidence:**
   - High (80-100%): Strong match
   - Medium (50-79%): Partial match
   - Low (20-49%): Weak signals
   - None (<20%): Leave in inbox

## Step 5: Present Recommendations

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

Use AskUserQuestion with options from discovered paths.

**For multiple notes:**
```
| Note | Suggested Destination | Confidence |
|------|----------------------|------------|
| "redis-session-caching" | Areas/AI/agentic development/ | High (85%) |
| "claude-code-hooks" | Areas/AI/agentic development/ | High (92%) |
| "debugging-approach" | (leave in inbox) | None |
```

Use AskUserQuestion:
1. Route all as suggested (Recommended)
2. Route individually
3. Leave all in inbox

## Step 6: Execute Moves

For each note being routed:

```bash
mv "{inbox}/{filename}" "{vault}/{destination}/"
```

## Step 7: Report Success

```
✓ Moved "redis-session-caching.md" → Areas/AI/agentic development/
✓ Moved "claude-code-hooks.md" → Areas/AI/agentic development/
○ Left "debugging-approach.md" in inbox (no clear destination)

3 notes processed: 2 routed, 1 remaining in inbox
```

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

- **Never suggest non-existent paths** - Only use `ls` output
- **Always include inbox option** - Safe default for uncertain cases
- **Show reasoning** - Users should understand why
- **Preserve filenames** - Don't rename when moving
- **Two-level depth max** - Don't suggest deeply nested paths
- **Respect emoji prefixes** - Use exact folder names from filesystem

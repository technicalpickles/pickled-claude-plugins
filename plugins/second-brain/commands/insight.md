---
description: Capture an insight from conversation to your second brain
argument-hint: [insight to capture]
---

# Capture Insight

Capture an insight from the current conversation to your Obsidian vault.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault path.

If missing, inform user:
```
Second brain not configured. Run /second-brain:setup first.
```

Read vault's `CLAUDE.md` for structure and routing rules.

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/zettelkasten.md` for naming
- `references/note-patterns.md` for Insight Note template

## Step 2: Identify the Insight

**If argument provided:**
Use the argument as the insight to capture.

**If no argument:**
Ask: "What insight would you like to capture?"

Also review recent conversation context to suggest what might be worth capturing.

## Step 3: Gather Provenance

Collect context about where this insight came from:

```bash
# Get repo info (if in a repo)
git rev-parse --show-toplevel 2>/dev/null || echo "none"
git branch --show-current 2>/dev/null || echo "none"
git rev-parse --short HEAD 2>/dev/null || echo "none"

# Get timestamp
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

## Step 4: Generate Filename

Use Zettelkasten format: `YYYYMMDDHHMM short-title.md`

```bash
date +"%Y%m%d%H%M"
```

Create short, descriptive title (3-5 words, lowercase, hyphenated).

Example: `202601211430 redis-over-memcached-sessions.md`

## Step 5: Write to Inbox

Get inbox path from vault's `CLAUDE.md` or `.obsidian/app.json`.

Use **Insight Note** pattern from `references/note-patterns.md`:

```markdown
---
captured: {ISO timestamp}
source: claude-conversation
repo: {repo name or "none"}
branch: {branch name or "none"}
commit: {short commit hash or "none"}
---

# {Insight Title}

{The insight, cleaned up and clearly written. 1-3 paragraphs.}

## Context

Captured while {brief description of what you were working on/discussing}.

---
*Captured via /second-brain:insight*
```

## Step 6: Confirm and Analyze

After writing:
```
✓ Captured to inbox: {filename}

Analyzing for routing...
```

Search vault for related notes:
- Grep for similar keywords
- Check Projects, Areas, Resources folders
- Look for existing notes on same topic

## Step 7: Suggest Routing

Show findings:
```
Found related notes:
- {path/to/related-note.md}
- {path/to/another-related.md}

This looks like: {category - e.g., "architecture decision", "debugging pattern"}
```

Use AskUserQuestion with options:
1. {Best matching location} (Recommended)
2. {Second best location}
3. Leave in inbox for now

If user selects destination, move the file there.

## Constraints

- **Always write to inbox first** - Never skip this step
- **Use skill references** - Get paths from skill, not hardcoded
- **Zettelkasten naming** - Must use `YYYYMMDDHHMM title.md` format
- **Show analysis before asking** - Don't just ask, show reasoning
- **Clean prose** - Well-written insight, not raw conversation paste

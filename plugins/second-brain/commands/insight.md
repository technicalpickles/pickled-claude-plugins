---
description: Capture an insight from conversation to your second brain
argument-hint: [insight to capture]
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

# Capture Insight

Capture an insight from the current conversation to your Obsidian vault.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault name and path.

If missing, inform user:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to access the vault (e.g., `~/.claude/vaults/primary`).

Read vault's `CLAUDE.md` for structure and routing rules.

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/zettelkasten.md` for naming
- `references/note-patterns.md` for Insight Note template
- `references/routing.md` for destination matching

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

## Step 6: Confirm and Analyze for Routing

After writing, confirm capture:
```
✓ Captured to inbox: {filename}

Analyzing for routing...
```

Load `references/routing.md` and follow the algorithm:

**1. Discover vault structure:**
```bash
ls -d "{vault}"/*Areas*/*/     2>/dev/null
ls -d "{vault}"/*Resources*/*/ 2>/dev/null
ls -d "{vault}"/*Projects*/*/  2>/dev/null
```

**2. Extract signals from captured note:**
- Keywords from title and body
- Content category (architecture, debugging, tool config, etc.)
- Source context from provenance (repo, branch)

**3. Load disambiguation rules from vault CLAUDE.md:**
- Find `### Disambiguation:` sections
- Extract key questions, category tables, edge case mappings
- These override generic matching for semantically similar areas

**4. Score each discovered destination:**

*If disambiguation rules apply:*
- Check edge case mappings first (explicit rules)
- Apply key question matches (+25% boost)
- Apply category table matches (+15% boost)
- Apply disambiguation mismatch penalty (-20%)

*Then apply generic signals:*
- Keyword match in folder name (40%)
- Related notes exist in folder (30%)
- PARA category fit (20%)
- Recency of folder activity (10%)

**5. Calculate confidence levels:**
- High (80-100%): Strong match, often with disambiguation support
- Medium (50-79%): Partial match
- Low (20-49%): Weak signals
- None (<20%): Leave in inbox

## Step 7: Suggest Routing

Present findings with explanations:
```
Routing suggestions for "{filename}":

1. **{Areas/path/}** (85% - High)
   → Matches keywords: "keyword1", "keyword2"
   → Related note exists: "{related-note.md}"
   → [If disambiguation applied] Vault rule: "{edge case or key question}"

2. **{Resources/path/}** (48% - Low)
   → Generic category fit

3. **Leave in Inbox** (Safe default)
   → Route later when destination is clearer
```

When disambiguation rules influenced the result, explain which rule applied.

Use AskUserQuestion with discovered options:
- Only include destinations that actually exist (from `ls` output)
- Show confidence and explanation for each
- Always include "Leave in inbox for now" option

If user selects a destination, move the file:
```bash
mv "{inbox}/{filename}" "{vault}/{selected-destination}/"
```

If all destinations score <20%, recommend inbox without asking.

## Constraints

- **Always write to inbox first** - Never skip this step
- **Use skill references** - Get paths from skill, not hardcoded
- **Zettelkasten naming** - Must use `YYYYMMDDHHMM title.md` format
- **Show analysis before asking** - Don't just ask, show reasoning
- **Clean prose** - Well-written insight, not raw conversation paste

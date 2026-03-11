---
description: Capture an insight from conversation to your second brain
argument-hint: [insight to capture]
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/.obsidian/*.json)
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(npx @techpickles/sb:*)
  - Bash(which:qmd)
  - Bash(qmd:query *)
  - Bash(qmd:collection list)
  - Bash(qmd:get *)
  - Bash(qmd:status)
---

# Capture Insight

Capture an insight from the current conversation to your Obsidian vault.

## Step 1: Load Configuration

Load configuration using sb CLI:

```bash
npx @techpickles/sb config default    # Get default vault name
npx @techpickles/sb config vaults     # List all configured vaults
```

If sb is not available, inform user:
```
sb CLI is required but not available. Install Node.js and npm, then try again.
Or install globally for faster execution: npm i -g @techpickles/sb
```

If no vaults are configured, inform user:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to access the vault for reading CLAUDE.md (e.g., `~/.claude/vaults/primary`).

Read vault's `CLAUDE.md` for structure and routing rules.

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/sb-cli.md` for sb invocation details
- `references/zettelkasten.md` for naming
- `references/note-patterns.md` for Insight Note template
- `references/routing.md` for destination matching
- `references/connecting.md` for connection discovery
- `references/daily-linking.md` for linking to daily note

## Step 2: Identify the Insight

**If argument provided:**
Use the argument as the insight to capture.

**If no argument:**
Ask: "What insight would you like to capture?"

Also review recent conversation context to suggest what might be worth capturing.

## Step 3: Create Note Scaffold

Create the note scaffold using sb CLI (without --content):

```bash
npx @techpickles/sb note create \
  --source auto \
  --title "short descriptive title"
```

sb creates the file with frontmatter and title heading only. Returns JSON with the created path:
```json
{
  "path": "/path/to/vault/Inbox/202603111430 short-descriptive-title.md",
  "filename": "202603111430 short-descriptive-title.md"
}
```

The `--source auto` flag tells sb to:
- Use `source: claude-conversation` in frontmatter
- Collect git provenance (repo, branch, commit) if in a repo
- Add `captured: {ISO timestamp}` to frontmatter
- Generate Zettelkasten filename with current timestamp

Then write the note body using Claude's **Write tool** at the returned path. Read the created file first (to get the exact frontmatter sb wrote), then rewrite with the full note content:

Use **Insight Note** pattern with cleaned up prose (1-3 paragraphs):

```
{frontmatter from sb, preserved exactly}

# {Insight Title}

{The insight, cleaned up and clearly written. 1-3 paragraphs.}

## Context

Captured while {brief description of what you were working on/discussing}.

---
*Captured via /second-brain:insight*
```

**Why two steps?** The sb call is a short, easy-to-approve Bash command. The Write tool has a clean approval UI for file content. Together they're much easier to review than a single Bash command with embedded multi-paragraph prose.

## Step 4: Confirm and Analyze for Routing

After creation, sb returns the created note's path as JSON. Parse and confirm:
```
✓ Captured to inbox: {filename}

Analyzing for routing...
```

Get routing context from sb:
```bash
npx @techpickles/sb note context --note "{note-path}"
```

This returns JSON with:
- Keywords extracted from title and body
- Content category (architecture, debugging, tool config, etc.)
- Related notes in the vault
- Source context from provenance

Also discover vault structure:
```bash
npx @techpickles/sb vault structure
```

This returns PARA folders (Areas, Resources, Projects) as structured JSON.

Load disambiguation rules from vault CLAUDE.md (read via Claude's Read tool):
- Find `### Disambiguation:` sections
- Extract key questions, category tables, edge case mappings
- These override generic matching for semantically similar areas

## Step 5: Score Destinations

For each discovered destination from vault structure:

**If disambiguation rules apply:**
- Check edge case mappings first (explicit rules)
- Apply key question matches (+25% boost)
- Apply category table matches (+15% boost)
- Apply disambiguation mismatch penalty (-20%)

**Then apply generic signals:**
- Keyword match in folder name (40%)
- Related notes exist in folder (30%)
- PARA category fit (20%)
- Recency of folder activity (10%)

**Calculate confidence levels:**
- High (80-100%): Strong match, often with disambiguation support
- Medium (50-79%): Partial match
- Low (20-49%): Weak signals
- None (<20%): Leave in inbox

## Step 6: Suggest Routing

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
- Only include destinations that actually exist (from vault structure)
- Show confidence and explanation for each
- Always include "Leave in inbox for now" option

If user selects a destination, move the file using sb:
```bash
npx @techpickles/sb note move \
  --from "{inbox-note-path}" \
  --to "{selected-destination}/"
```

If all destinations score <20%, recommend inbox without asking.

## Step 8: Discover Connections

Follow `references/connecting.md` algorithm to find related notes in the vault.

**1. Check prerequisites:**
```bash
which qmd
```

If qmd is not available, skip to Step 9 (don't fail the capture).

**2. Extract query terms** from the captured note's title and body.

**3. Run semantic search:**
```bash
qmd query "{terms}" -c {collection} -n 15 --json
```

**4. Filter and rank** per the connecting reference (remove self, already-linked, low-relevance, daily notes; enrich with TK/See Also signals; rank).

**5. If connections found (any candidates above 30%):**

Present candidates and let user multi-select which to connect.

**6. For selected connections:**
- Add `## Related` section to the captured note with wiki-links
- Offer backlink weaving for notes with See Also/Related/TK sections

**7. If no connections above threshold,** skip silently and continue.

Note: The captured note won't be in qmd's index yet. That's fine. We're searching FROM the note's content, not for it.

## Step 9: Link to Daily Note

Link the captured note to today's daily note using sb:

```bash
npx @techpickles/sb daily append \
  --section "Links" \
  --content "- [[{filename without .md}]] - {brief description of the insight}"
```

The sb CLI handles:
- Finding today's daily note path from .obsidian config
- Creating the daily note if it doesn't exist
- Finding or creating the `## Links` section
- Appending the link

Confirm linking:
```
✓ Linked to daily note: {date}.md
```

If daily note linking fails (sb returns error), skip silently. The note is already captured.

## Constraints

- **Always write to inbox first** - Never skip this step
- **Use skill references** - Get paths from skill, not hardcoded
- **Use sb CLI for data operations** - Note creation, moving, structure discovery
- **Use Claude's Read/Write/Edit for prose** - Reading CLAUDE.md, editing note content
- **Zettelkasten naming** - sb handles `YYYYMMDDHHMM title.md` format automatically
- **Show analysis before asking** - Don't just ask, show reasoning
- **Clean prose** - Well-written insight, not raw conversation paste

# Second Brain Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a reusable `second-brain` plugin for Obsidian vault integration and knowledge capture.

**Architecture:** Plugin provides skills (tool mechanics + methodology references) and commands (setup, insight, distill-conversation, process-daily, link-project). Configuration layered across global, vault, and repo levels.

**Tech Stack:** Claude Code plugin system, markdown skills/commands

**Source Design:** `working-with-pickles/docs/plans/2026-01-21-second-brain-plugin-design.md`

---

## Phase 1: Plugin Scaffolding

### Task 1: Create plugin directory structure

**Files:**
- Create: `plugins/second-brain/.claude-plugin/plugin.json`
- Create: `plugins/second-brain/skills/obsidian/references/.gitkeep`
- Create: `plugins/second-brain/commands/.gitkeep`
- Create: `plugins/second-brain/templates/.gitkeep`

**Step 1: Create plugin.json**

```json
{
  "name": "second-brain",
  "version": "1.0.0",
  "description": "Knowledge management for Obsidian vaults and structured markdown repositories",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT"
}
```

**Step 2: Create directory structure**

```bash
mkdir -p plugins/second-brain/.claude-plugin
mkdir -p plugins/second-brain/skills/obsidian/references
mkdir -p plugins/second-brain/commands
mkdir -p plugins/second-brain/templates
```

**Step 3: Verify structure**

```bash
tree plugins/second-brain/
```

Expected:
```
plugins/second-brain/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── skills/
│   └── obsidian/
│       └── references/
└── templates/
```

**Step 4: Commit**

```bash
git add plugins/second-brain/
git commit -m "feat(second-brain): scaffold plugin structure"
```

---

## Phase 2: Obsidian Skill (Tool Mechanics)

### Task 2: Create obsidian skill (tool-focused)

**Files:**
- Create: `plugins/second-brain/skills/obsidian/SKILL.md`
- Reference: `working-with-pickles/.claude/skills/obsidian/SKILL.md` (for content)

**Step 1: Create SKILL.md focused on tool mechanics**

The skill should cover Obsidian-specific behavior (wiki links, .obsidian/ folder, daily notes mechanics) but NOT methodology (PARA, Zettelkasten) - that goes in references.

```markdown
---
name: obsidian
description: Obsidian vault mechanics - wiki links, .obsidian/ config, daily notes, plugins. Use when working with Obsidian vaults or structured markdown.
---

# Obsidian Skill

Tool-specific mechanics for working with Obsidian vaults.

## Vault Detection

A directory is an Obsidian vault if it contains `.obsidian/` folder.

## Wiki Links

**Syntax:** `[[Note Title]]` or `[[path/Note Title]]`

- Obsidian resolves by title match
- Can include path for disambiguation
- Aliases: `[[Note Title|display text]]`

## .obsidian/ Configuration

Obsidian stores settings in `.obsidian/` at vault root:

| File | Purpose |
|------|---------|
| `daily-notes.json` | Daily note folder and template |
| `templates.json` | Templates folder location |
| `zk-prefixer.json` | Zettelkasten/inbox settings |
| `app.json` | General settings (new file location, attachments) |
| `plugins/` | Installed plugin data |

### Parsing Config

```json
// daily-notes.json
{
  "folder": "Fleeting",
  "template": "Templates/daily"
}

// templates.json
{"folder": "Templates"}

// zk-prefixer.json
{
  "folder": "📫 Inbox",
  "template": "Templates/frontmatter"
}

// app.json
{
  "newFileFolderPath": "📫 Inbox",
  "attachmentFolderPath": "🖇 Attachments"
}
```

## Daily Notes

**Finding today's note:**
1. Read `.obsidian/daily-notes.json` for folder
2. Use format `YYYY-MM-DD.md` (Obsidian default)
3. Path: `{folder}/{YYYY-MM-DD}.md`

**Template application:**
- Obsidian applies template on note creation
- Template path from `daily-notes.json`

## Glossary Integration

If `Glossary.md` exists at vault root:
- Contains known transcription corrections
- Maps common errors to correct terms
- Used by process-daily command

## Vault CLAUDE.md

Vaults should have a `CLAUDE.md` at root describing:
- Folder structure
- Routing rules
- Naming conventions
- References to methodology (PARA, Zettelkasten)

See `templates/vault-claude-md.md` for template.

## References

For methodology (tool-agnostic):
- `references/para.md` - PARA organizational system
- `references/zettelkasten.md` - Naming conventions
- `references/note-patterns.md` - Note templates
```

**Step 2: Verify skill is readable**

```bash
head -20 plugins/second-brain/skills/obsidian/SKILL.md
```

**Step 3: Commit**

```bash
git add plugins/second-brain/skills/obsidian/SKILL.md
git commit -m "feat(second-brain): add obsidian skill for tool mechanics"
```

---

### Task 3: Create PARA reference

**Files:**
- Create: `plugins/second-brain/skills/obsidian/references/para.md`
- Reference: `working-with-pickles/.claude/skills/obsidian/references/para.md` (copy and adapt)

**Step 1: Copy PARA reference from working-with-pickles**

Read the source file and copy to new location. Content should remain largely unchanged as it's already tool-agnostic.

**Step 2: Verify content**

```bash
wc -l plugins/second-brain/skills/obsidian/references/para.md
```

Expected: ~145 lines

**Step 3: Commit**

```bash
git add plugins/second-brain/skills/obsidian/references/para.md
git commit -m "feat(second-brain): add PARA methodology reference"
```

---

### Task 4: Create Zettelkasten reference

**Files:**
- Create: `plugins/second-brain/skills/obsidian/references/zettelkasten.md`

**Step 1: Create zettelkasten.md**

Extract naming conventions into dedicated reference:

```markdown
# Zettelkasten Naming Convention

Timestamp-prefixed filenames for unique, sortable note identifiers.

## Format

```
YYYYMMDDHHMM short-title.md
```

**Components:**
- `YYYYMMDDHHMM` - Timestamp (year, month, day, hour, minute)
- `short-title` - 3-5 words, lowercase, hyphenated
- `.md` - Markdown extension

**Examples:**
- `202601211430 redis-session-caching.md`
- `202601211445 debugging-kafka-lag.md`
- `202601211500 meeting-platform-review.md`

## Generating Timestamps

```bash
date +"%Y%m%d%H%M"
# Output: 202601211430
```

## Benefits

1. **Unique** - Timestamp ensures no collisions
2. **Sortable** - Files sort chronologically
3. **Linkable** - Stable identifier for wiki links
4. **Discoverable** - Title in filename aids search

## Exceptions

Some note types skip the Zettelkasten prefix:

| Type | Naming | Example |
|------|--------|---------|
| Person notes | Full name | `Jane Smith.md` |
| Daily notes | Date only | `2026-01-21.md` |
| Index/MOC | Topic name | `Kafka.md` |
| Project folders | Project name | `Projects/kafka-migration/` |

## When to Use

- New permanent notes (insights, ideas, concepts)
- Meeting notes
- Investigation notes
- Extracted content from daily notes

## When NOT to Use

- Daily notes (use `YYYY-MM-DD.md`)
- Person notes (use full name)
- Templates
- Index/overview notes
```

**Step 2: Commit**

```bash
git add plugins/second-brain/skills/obsidian/references/zettelkasten.md
git commit -m "feat(second-brain): add Zettelkasten naming reference"
```

---

### Task 5: Create note patterns reference

**Files:**
- Create: `plugins/second-brain/skills/obsidian/references/note-patterns.md`
- Reference: `working-with-pickles/.claude/skills/obsidian/references/note-patterns.md` (copy)

**Step 1: Copy note-patterns.md from working-with-pickles**

Read the source file and copy to new location. Content should remain unchanged.

**Step 2: Verify content**

```bash
wc -l plugins/second-brain/skills/obsidian/references/note-patterns.md
```

Expected: ~294 lines

**Step 3: Commit**

```bash
git add plugins/second-brain/skills/obsidian/references/note-patterns.md
git commit -m "feat(second-brain): add note patterns reference"
```

---

## Phase 3: Commands

### Task 6: Create setup command

**Files:**
- Create: `plugins/second-brain/commands/setup.md`

**Step 1: Create setup.md**

```markdown
---
description: Set up second-brain vault configuration
---

# Second Brain Setup

Configure vault paths and scaffold vault CLAUDE.md.

## Step 1: Check Existing Config

Read `~/.claude/second-brain.md` if it exists.

If exists, show current vaults and ask:
- Add another vault?
- Reconfigure existing vault?
- Cancel

## Step 2: Get Vault Path

Ask user for vault path. No assumed locations - just ask directly:

"Where is your Obsidian vault located? (full path)"

## Step 3: Validate Vault

Check the path:

```bash
# Path exists?
ls -d "{path}" 2>/dev/null

# Is it an Obsidian vault?
ls -d "{path}/.obsidian" 2>/dev/null
```

If `.obsidian/` missing:
- Might not be an Obsidian vault
- Offer to continue anyway (for plain markdown repos)
- Or user can open folder in Obsidian first to initialize

## Step 4: Parse .obsidian/ Config

If `.obsidian/` exists, read settings:

```bash
# Daily notes
cat "{path}/.obsidian/daily-notes.json" 2>/dev/null

# Templates
cat "{path}/.obsidian/templates.json" 2>/dev/null

# Zettelkasten/inbox
cat "{path}/.obsidian/zk-prefixer.json" 2>/dev/null

# General settings
cat "{path}/.obsidian/app.json" 2>/dev/null
```

Extract:
- Daily notes folder and template
- Templates folder
- Inbox/new notes folder
- Attachments folder

## Step 5: Confirm Settings

Show detected settings:

```
Detected from .obsidian/:
- Daily notes: Fleeting/ (template: Templates/daily)
- Templates: Templates/
- Inbox: 📫 Inbox/
- Attachments: 🖇 Attachments/

Does this look right? [Yes] [Adjust]
```

## Step 6: Name the Vault

Ask for short identifier:

"What should I call this vault? (e.g., primary, work, personal)"

Suggest "primary" if this is the first vault.

## Step 7: Write Global Config

Create or update `~/.claude/second-brain.md`:

```markdown
# Second Brain Configuration

## Vaults

- {name}: {path}

Default: {name}
```

If file exists, append new vault to list.

## Step 8: Scaffold Vault CLAUDE.md

Check if `{vault}/CLAUDE.md` exists.

If missing, offer to create from template:

"Your vault doesn't have a CLAUDE.md. Create one with detected settings? [Yes] [No]"

If yes, use `templates/vault-claude-md.md` as base, filling in detected values.

## Step 9: Confirm Complete

```
✓ Second brain configured!

Vault: {name} → {path}
Config: ~/.claude/second-brain.md

Next steps:
- Use /second-brain:insight to capture from any repo
- Use /second-brain:link-project to connect a repo to your vault
- Run Claude inside your vault for /second-brain:process-daily
```

## Adding Additional Vaults

If `~/.claude/second-brain.md` already exists:

1. Show current vaults
2. Ask for new vault path
3. Follow same validation/detection flow
4. Append to existing config
5. Ask if this should be the new default
```

**Step 2: Commit**

```bash
git add plugins/second-brain/commands/setup.md
git commit -m "feat(second-brain): add setup command"
```

---

### Task 7: Create insight command

**Files:**
- Create: `plugins/second-brain/commands/insight.md`
- Reference: `working-with-pickles/.claude/commands/brain-capture.md` (adapt)

**Step 1: Create insight.md**

Adapt brain-capture.md with new naming and skill references:

```markdown
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
```

**Step 2: Commit**

```bash
git add plugins/second-brain/commands/insight.md
git commit -m "feat(second-brain): add insight command"
```

---

### Task 8: Create distill-conversation command

**Files:**
- Create: `plugins/second-brain/commands/distill-conversation.md`
- Reference: `working-with-pickles/.claude/commands/brain-distill.md` (adapt)

**Step 1: Create distill-conversation.md**

Adapt brain-distill.md with new naming:

```markdown
---
description: Extract and capture multiple insights from this conversation
---

# Distill Conversation

Review the current conversation and extract insights worth capturing.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault path.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

Load skill references for note patterns and naming.

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

Analyze captured notes:

```
Analyzing captured notes for routing...

1. "{insight1}" → looks like it belongs in {suggested path}
2. "{insight2}" → looks like it belongs in {suggested path}
3. "{insight3}" → no clear match, recommend leaving in inbox
```

Use AskUserQuestion:

**Question:** "How should I route these?"

**Options:**
1. Route all as suggested
2. Route individually (I'll ask about each)
3. Leave all in inbox for now

## Constraints

- **Be selective** - Only genuinely valuable insights
- **Categorize clearly** - Help user understand knowledge type
- **Batch efficiently** - Don't make user go through many dialogs
- **Clean prose** - Each insight standalone, useful months later
- **Zettelkasten naming** - Must use `YYYYMMDDHHMM title.md`
```

**Step 2: Commit**

```bash
git add plugins/second-brain/commands/distill-conversation.md
git commit -m "feat(second-brain): add distill-conversation command"
```

---

### Task 9: Create process-daily command

**Files:**
- Create: `plugins/second-brain/commands/process-daily.md`
- Reference: `working-with-pickles/.claude/commands/brain-process-daily.md` (adapt)

**Step 1: Create process-daily.md**

Copy brain-process-daily.md and add vault-only check at the beginning:

```markdown
---
description: Process voice transcriptions in today's daily note
argument-hint: [date, e.g. 2026-01-21]
---

# Process Daily Note

Clean up voice transcriptions in a daily note. Works in phases with confirmation between each.

## Prerequisite: Vault Context Check

**This command only works inside a vault.**

Check if current directory is a vault:

```bash
ls -d .obsidian 2>/dev/null
```

If `.obsidian/` not found in current directory or parents:

```
⚠ /second-brain:process-daily only works inside a vault.

You're currently in: {cwd}

Options:
1. Open your vault: {path from ~/.claude/second-brain.md}
2. Use /second-brain:insight to capture from here
3. Use /second-brain:distill-conversation for end-of-session extraction
```

Stop execution - do not continue.

## Overview (when in vault)

1. Load context (daily note, glossary, vault conventions)
2. Identify & confirm transcription corrections (batched by category)
3. Clean prose (preview before applying)
4. Restructure to daily note template (preview before applying)
5. Suggest extractions (optional)

## Phase 1: Load Context

### Step 1.1: Read Vault CLAUDE.md

Read `CLAUDE.md` at vault root for:
- Daily note location
- Template reference
- Structure conventions

### Step 1.2: Find the Daily Note

**If argument provided:** Use as date (parse YYYY-MM-DD format)
**If no argument:** Use today's date

```bash
date +"%Y-%m-%d"
```

Construct path from vault's daily note location (e.g., `Fleeting/{date}.md`).

If file doesn't exist, inform user and stop.

### Step 1.3: Load Glossary

Read `Glossary.md` if it exists at vault root.

Parse correction mappings by category.

### Step 1.4: Assess Content

Read daily note. Report:
```
Loaded: Fleeting/2026-01-21.md
Glossary: Found ({N} known corrections)
Content: ~{N} words, {structured|unstructured}

Ready to process. Continue? [Yes] [Cancel]
```

## Phase 2: Identify & Confirm Corrections

Present corrections in batches by category:

```
### Tools & Software (Batch 1 of 4)

| # | Found | → Correction | Context |
|---|-------|--------------|---------|
| 1 | me's | mise | "started using me's" |
| 2 | Claude MT | CLAUDE.md | "added Claude MT" |

✓ Accept all | Enter numbers to reject | ? for more context
```

Categories:
1. Known corrections (from Glossary) - batch accept
2. Tool/product names
3. People names
4. Technical terms
5. Uncertain - need user input

After all batches, offer glossary update for new corrections.

## Phase 3: Clean Prose

Remove filler words, false starts, run-on sentences.

Preserve: conversational tone, first-person voice, meaning.

Show before/after preview for representative sections.

## Phase 4: Restructure (if needed)

If note lacks structure, propose restructuring to match daily template:

```
## Action Items    ← Top: high visibility
## Extracted Notes ← Links to permanent notes
## Log             ← Structured events
## Quick Notes     ← Bottom: append zone
```

## Phase 5: Suggest Extractions

Identify content substantial enough for permanent notes.

Criteria: substantial, reusable, standalone, reference-worthy.

Offer extraction with routing.

## Constraints

- **Vault-only** - Must be run from inside vault
- **Interactive** - Always preview before applying
- **Batch confirmations** - Group similar items
- **Preserve meaning** - Never change what was said
- **Follow skill references** - Use vault conventions
- **Phases skippable** - User can skip any phase
```

**Step 2: Commit**

```bash
git add plugins/second-brain/commands/process-daily.md
git commit -m "feat(second-brain): add process-daily command (vault-only)"
```

---

### Task 10: Create link-project command

**Files:**
- Create: `plugins/second-brain/commands/link-project.md`

**Step 1: Create link-project.md**

```markdown
---
description: Set up symlink from repo to vault folder
---

# Link Project to Vault

Create a symlink from current repo to a folder in your vault.

## Step 1: Check Configuration

Read `~/.claude/second-brain.md` for vault paths.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

## Step 2: Select Vault

If multiple vaults configured, ask which one:

Use AskUserQuestion:
**Question:** "Which vault should this project connect to?"
**Options:** List configured vaults

If only one vault, use it automatically.

## Step 3: Browse Vault Structure

Show top-level folders in vault:

```bash
ls -d {vault}/*/ | head -10
```

Ask user to select or specify path:

"Which folder in your vault? (or type a path)"

Options:
1. Areas/
2. Projects/
3. Resources/
4. (type custom path)

May need to drill down into subfolders.

## Step 4: Determine Local Path

Suggest default based on vault folder name:

```
Vault folder: Areas/gusto/ASYNC/
Suggested local path: docs/ASYNC/

Use this path? [Yes] [Custom path]
```

## Step 5: Create Symlink

```bash
# Create parent directory if needed
mkdir -p {local_parent}

# Create symlink
ln -s "{vault_path}" "{local_path}"

# Verify
ls -la "{local_path}"
```

## Step 6: Write Local Config

Create `.claude/second-brain.local.md`:

```markdown
# Second Brain Connection

Vault: {vault_name}

Symlinks:
- {local_path}/ → {vault_relative_path}/
```

If file exists, append new symlink to list.

## Step 7: Check Gitignore

```bash
git check-ignore .claude/second-brain.local.md
```

If not ignored (exit code 1):

```
⚠ .claude/second-brain.local.md is not gitignored.

This file contains host-specific paths and shouldn't be committed.

Options:
1. Add to .git/info/exclude (this repo only)
2. Add to global gitignore (~/.config/git/ignore)
3. Skip (I'll handle it)
```

If option 1:
```bash
echo ".claude/second-brain.local.md" >> .git/info/exclude
```

If option 2:
```bash
mkdir -p ~/.config/git
echo ".claude/second-brain.local.md" >> ~/.config/git/ignore
```

## Step 8: Confirm

```
✓ Project linked to vault!

Symlink: {local_path}/ → {vault_path}/
Config: .claude/second-brain.local.md

Files in {local_path}/ are now synced with your vault.
```

## Listing Existing Links

If `.claude/second-brain.local.md` exists, show current links first:

```
Current links:
- docs/jira/ASYNC/ → Areas/gusto/ASYNC/
- docs/interviews/ → Areas/gusto/interviews/

Add another link? [Yes] [No]
```
```

**Step 2: Commit**

```bash
git add plugins/second-brain/commands/link-project.md
git commit -m "feat(second-brain): add link-project command"
```

---

## Phase 4: Templates

### Task 11: Create vault CLAUDE.md template

**Files:**
- Create: `plugins/second-brain/templates/vault-claude-md.md`

**Step 1: Create template**

```markdown
# {Vault Name}

> See `second-brain:obsidian` skill for tool conventions.

## Structure

- {inbox_folder}/ - New captures before routing
- {daily_folder}/ - Daily notes, quick captures
- Projects/ - Active work with deadlines
- Areas/ - Ongoing responsibilities
- Resources/ - Reference material
- Archive/ - Inactive items
- {templates_folder}/ - Note templates
- {attachments_folder}/ - Media files

## Daily Notes

Location: {daily_folder}/
Format: YYYY-MM-DD.md
Template: {daily_template}

## Naming Convention

Zettelkasten: YYYYMMDDHHMM short-title.md

See `second-brain:obsidian/references/zettelkasten.md` for details.

## Routing Rules

1. Quick capture? → {inbox_folder}/
2. Today's log? → {daily_folder}/{date}.md
3. Has deadline/deliverable? → Projects/
4. Ongoing responsibility? → Areas/
5. Reference material? → Resources/
6. Done/inactive? → Archive/

See `second-brain:obsidian/references/para.md` for PARA methodology.

## Note Patterns

See `second-brain:obsidian/references/note-patterns.md` for templates:
- Insight notes
- Meeting notes
- Person notes
- Investigation notes
- Project notes

## Glossary

See Glossary.md for transcription corrections (if using /second-brain:process-daily).

---
*Generated by /second-brain:setup from .obsidian/ config*
```

**Step 2: Commit**

```bash
git add plugins/second-brain/templates/vault-claude-md.md
git commit -m "feat(second-brain): add vault CLAUDE.md template"
```

---

## Phase 5: Finalization

### Task 12: Verify plugin structure

**Step 1: Check complete structure**

```bash
tree plugins/second-brain/
```

Expected:
```
plugins/second-brain/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── distill-conversation.md
│   ├── insight.md
│   ├── link-project.md
│   ├── process-daily.md
│   └── setup.md
├── skills/
│   └── obsidian/
│       ├── SKILL.md
│       └── references/
│           ├── note-patterns.md
│           ├── para.md
│           └── zettelkasten.md
└── templates/
    └── vault-claude-md.md
```

**Step 2: Verify all files have content**

```bash
wc -l plugins/second-brain/**/*.md plugins/second-brain/**/**/*.md
```

All files should have substantial content (no empty files).

**Step 3: Test plugin loads**

Add plugin to a test session and verify commands appear:
- /second-brain:setup
- /second-brain:insight
- /second-brain:distill-conversation
- /second-brain:process-daily
- /second-brain:link-project

### Task 13: Update working-with-pickles (optional, separate PR)

**Files:**
- Remove: `working-with-pickles/.claude/skills/obsidian/` (entire folder)
- Remove: `working-with-pickles/.claude/commands/brain-capture.md`
- Remove: `working-with-pickles/.claude/commands/brain-distill.md`
- Remove: `working-with-pickles/.claude/commands/brain-process-daily.md`
- Modify: `working-with-pickles/CLAUDE.md` (update references)

**Step 1: Remove migrated files**

```bash
rm -rf .claude/skills/obsidian/
rm .claude/commands/brain-capture.md
rm .claude/commands/brain-distill.md
rm .claude/commands/brain-process-daily.md
```

**Step 2: Update CLAUDE.md**

Remove obsidian skill references, note that second-brain plugin provides this functionality.

**Step 3: Create ~/.claude/second-brain.md**

Move vault config from `~/.claude/CLAUDE.md` to new location.

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: migrate obsidian skills to second-brain plugin"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1 | Plugin scaffolding |
| 2 | 2-5 | Obsidian skill + references |
| 3 | 6-10 | Commands |
| 4 | 11 | Templates |
| 5 | 12-13 | Verification + migration |

Total: 13 tasks

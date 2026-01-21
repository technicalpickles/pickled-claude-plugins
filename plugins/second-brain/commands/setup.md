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

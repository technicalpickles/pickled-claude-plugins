---
description: Set up second-brain vault configuration
allowed-tools:
  - Read(~/.claude/second-brain.md)
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Write(~/.claude/vaults/**/CLAUDE.md)
  - Bash(npx @techpickles/sb:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
  - Bash(ln:*)
---

# Second Brain Setup

Configure vault paths and scaffold vault CLAUDE.md.

For sb CLI details, see [references/sb-cli.md](../skills/obsidian/references/sb-cli.md).

## Step 1: Check Prerequisites

Verify sb CLI is available:

```bash
npx @techpickles/sb --version
```

If this fails:
```
sb CLI is required but not available. Install Node.js and npm, then try again.
Or install globally for faster execution: npm i -g @techpickles/sb
```

## Step 2: Check Existing Config

Check if vaults are already configured:

```bash
npx @techpickles/sb config vaults
```

This returns JSON with configured vaults.

If vaults exist, show current and ask:
- Add another vault?
- Reconfigure existing vault?
- Cancel

## Step 3: Get Vault Path

Ask user for vault path. No assumed locations, just ask directly:

"Where is your Obsidian vault located? (full path)"

## Step 4: Validate Vault

Check the path exists:

```bash
ls -d "{path}" 2>/dev/null
```

Parse .obsidian config (if present):

```bash
npx @techpickles/sb vault obsidian --path "{path}"
```

This outputs JSON with:
- Daily notes folder and template
- Templates folder
- Inbox/new notes folder
- Attachments folder

If `.obsidian/` missing, sb will indicate this in the output:
- Might not be an Obsidian vault
- Offer to continue anyway (for plain markdown repos)
- Or user can open folder in Obsidian first to initialize

## Step 5: Confirm Settings

Show detected settings from the sb output:

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

## Step 7: Initialize Configuration

Create or update `~/.claude/second-brain.md`:

```bash
npx @techpickles/sb init --name "{name}" --path "{path}"
```

Add `--scaffold` flag if user wants to create vault CLAUDE.md:

```bash
npx @techpickles/sb init --name "{name}" --path "{path}" --scaffold
```

This command:
- Writes the vault configuration to `~/.claude/second-brain.md`
- Optionally creates `{vault}/CLAUDE.md` with detected settings

## Step 8: Create Vault Symlink

Create a symlink at `~/.claude/vaults/{name}` pointing to the actual vault:

```bash
# Create vaults directory if needed
mkdir -p ~/.claude/vaults

# Create symlink (use -n to not follow existing symlink, -f to force replace)
ln -sfn "{actual_vault_path}" ~/.claude/vaults/{name}

# Verify
ls -la ~/.claude/vaults/{name}
```

This symlink provides a well-known path for permissions and access.

## Step 9: Show Permissions

Generate permission entries for Claude Code settings:

```bash
npx @techpickles/sb permissions --vault "{name}"
```

This outputs the exact permission strings needed for:
- Read/Write on the vault path
- Read/Write on CLAUDE.md
- Read on .obsidian config

## Step 10: Confirm Complete

```
✓ Second brain configured!

Vault: {name} → {path}
Symlink: ~/.claude/vaults/{name}
Config: ~/.claude/second-brain.md

Add these permissions to your Claude Code settings:
{output from sb permissions}

Next steps:
- Use /second-brain:insight to capture from any repo
- Use /second-brain:link-project to connect a repo to your vault
- Run Claude inside your vault for /second-brain:process-daily
```

## Adding Additional Vaults

If vaults already exist (shown in Step 2):

1. Show current vaults from `npx @techpickles/sb config vaults`
2. Ask for new vault path
3. Follow same validation/detection flow (Steps 3-5)
4. Run `npx @techpickles/sb init --name "{name}" --path "{path}"` (appends to config)
5. Create symlink for new vault (Step 8)
6. Generate and show permissions (Step 9)
7. Ask if this should be the new default

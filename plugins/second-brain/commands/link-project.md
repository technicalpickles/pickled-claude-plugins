---
description: Set up symlink from repo to vault folder
allowed-tools:
  - Read(~/.claude/second-brain.md)
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(./.claude/second-brain.local.md)
  - Write(./.claude/second-brain.local.md)
  - Bash(ls:*)
  - Bash(mkdir:*)
  - Bash(ln:*)
  - Bash(git check-ignore:*)
  - Bash(echo:*)
---

# Link Project to Vault

Create a symlink from current repo to a folder in your vault.

## Step 1: Check Configuration

Read `~/.claude/second-brain.md` for vault names and paths.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to access vaults.

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

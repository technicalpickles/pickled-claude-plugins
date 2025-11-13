# Plugin Marketplace Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform claude-skills into pickled-claude-plugins marketplace with five domain-organized plugins

**Architecture:** Migrate flat skills/ directory to plugins/ structure where each plugin contains skills, commands, hooks, and metadata following Claude Code plugin specification

**Tech Stack:** Git, JSON, Markdown, Bash

---

## Task 1: Create Plugin Directory Structure

**Files:**
- Create: `plugins/working-in-monorepos/.claude-plugin/`
- Create: `plugins/working-in-monorepos/skills/`
- Create: `plugins/working-in-monorepos/commands/`
- Create: `plugins/working-in-monorepos/hooks/scripts/`
- Create: `plugins/git-workflows/.claude-plugin/`
- Create: `plugins/git-workflows/skills/`
- Create: `plugins/ci-cd-tools/.claude-plugin/`
- Create: `plugins/ci-cd-tools/skills/`
- Create: `plugins/debugging-tools/.claude-plugin/`
- Create: `plugins/debugging-tools/skills/`
- Create: `plugins/dev-tools/.claude-plugin/`
- Create: `plugins/dev-tools/skills/`

**Step 1: Create all plugin directories**

```bash
mkdir -p plugins/working-in-monorepos/{.claude-plugin,skills,commands,hooks/scripts}
mkdir -p plugins/git-workflows/{.claude-plugin,skills}
mkdir -p plugins/ci-cd-tools/{.claude-plugin,skills}
mkdir -p plugins/debugging-tools/{.claude-plugin,skills}
mkdir -p plugins/dev-tools/{.claude-plugin,skills}
```

**Step 2: Verify directory structure**

Run: `find plugins -type d | sort`

Expected output should show all created directories in tree structure.

**Step 3: Commit directory structure**

```bash
find plugins -type d -empty -exec touch {}/.gitkeep \;
git add plugins
git commit -m "chore: create plugin directory structure

Add directories for five plugins following Claude Code plugin layout."
```

---

## Task 2: Move Skills to Plugins

**Files:**
- Move: `skills/working-in-monorepos/` → `plugins/working-in-monorepos/skills/`
- Move: `skills/git-preferences-and-practices/` → `plugins/git-workflows/skills/`
- Move: `skills/gh-pr.md` → `plugins/git-workflows/skills/gh-pr/SKILL.md`
- Move: `skills/buildkite-status/` → `plugins/ci-cd-tools/skills/`
- Move: `skills/scope/` → `plugins/debugging-tools/skills/`
- Move: `skills/mcpproxy-debug/` → `plugins/debugging-tools/skills/`
- Move: `skills/working-in-scratch-areas/` → `plugins/dev-tools/skills/`

**Step 1: Move working-in-monorepos (preserves history)**

```bash
git mv skills/working-in-monorepos plugins/working-in-monorepos/skills/
```

**Step 2: Move git-workflows skills**

```bash
git mv skills/git-preferences-and-practices plugins/git-workflows/skills/
mkdir -p plugins/git-workflows/skills/gh-pr
git mv skills/gh-pr.md plugins/git-workflows/skills/gh-pr/SKILL.md
```

**Step 3: Move ci-cd-tools skills**

```bash
git mv skills/buildkite-status plugins/ci-cd-tools/skills/
```

**Step 4: Move debugging-tools skills**

```bash
git mv skills/scope plugins/debugging-tools/skills/
git mv skills/mcpproxy-debug plugins/debugging-tools/skills/
```

**Step 5: Move dev-tools skills**

```bash
git mv skills/working-in-scratch-areas plugins/dev-tools/skills/
```

**Step 6: Verify moves preserved structure**

Run: `find plugins/*/skills -name "SKILL.md" | sort`

Expected: Should list all 7 SKILL.md files in their new locations.

**Step 7: Commit skill migrations**

```bash
git add -A
git commit -m "refactor: move skills into plugin structure

Preserve git history by using git mv. Each skill now lives under
its plugin's skills/ directory."
```

---

## Task 3: Create working-in-monorepos Plugin Metadata

**Files:**
- Create: `plugins/working-in-monorepos/.claude-plugin/plugin.json`

**Step 1: Write plugin.json**

```json
{
  "name": "working-in-monorepos",
  "version": "1.0.0",
  "description": "Navigate and execute commands in monorepo subprojects with proper directory handling",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "homepage": "https://github.com/technicalpickles/pickled-claude-plugins",
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT",
  "keywords": ["monorepo", "workspace", "subproject", "directory"]
}
```

**Step 2: Verify JSON is valid**

Run: `cat plugins/working-in-monorepos/.claude-plugin/plugin.json | python3 -m json.tool`

Expected: Pretty-printed JSON with no errors.

**Step 3: Commit plugin metadata**

```bash
git add plugins/working-in-monorepos/.claude-plugin/plugin.json
git commit -m "feat: add working-in-monorepos plugin metadata"
```

---

## Task 4: Create working-in-monorepos SessionStart Hook

**Files:**
- Create: `plugins/working-in-monorepos/hooks/hooks.json`
- Create: `plugins/working-in-monorepos/hooks/scripts/detect-monorepo.sh`

**Step 1: Write hooks.json**

```json
{
  "hooks": [
    {
      "name": "detect-monorepo",
      "description": "Auto-detect monorepo structure on session start",
      "event": "SessionStart",
      "type": "command",
      "command": "bash",
      "args": ["{{hooksDir}}/scripts/detect-monorepo.sh"]
    }
  ]
}
```

**Step 2: Write detect-monorepo.sh script**

```bash
#!/usr/bin/env bash
# detect-monorepo.sh - Auto-detect monorepo and suggest activation

set -euo pipefail

# Check if .monorepo.json exists
if [ -f .monorepo.json ]; then
    echo "✓ Monorepo configuration found (.monorepo.json)"
    echo "The working-in-monorepos skill is available."
    exit 0
fi

# Look for monorepo indicators
has_multiple_package_json=false
has_multiple_cargo_toml=false
has_workspace_indicator=false

# Count package.json files (excluding node_modules)
package_count=$(find . -name package.json -not -path "*/node_modules/*" -type f 2>/dev/null | wc -l)
if [ "$package_count" -gt 1 ]; then
    has_multiple_package_json=true
fi

# Count Cargo.toml files
cargo_count=$(find . -name Cargo.toml -maxdepth 3 -type f 2>/dev/null | wc -l)
if [ "$cargo_count" -gt 1 ]; then
    has_multiple_cargo_toml=true
fi

# Check for workspace indicators
if [ -f package.json ] && grep -q '"workspaces"' package.json 2>/dev/null; then
    has_workspace_indicator=true
fi

if [ -f pnpm-workspace.yaml ] || [ -f lerna.json ]; then
    has_workspace_indicator=true
fi

# Report findings
if [ "$has_multiple_package_json" = true ] || [ "$has_multiple_cargo_toml" = true ] || [ "$has_workspace_indicator" = true ]; then
    echo "⚠ Monorepo detected but no .monorepo.json configuration found."
    echo ""
    echo "This appears to be a monorepo. Consider running:"
    echo "  /monorepo-init"
    echo ""
    echo "Or use the working-in-monorepos skill for guidance."
fi

exit 0
```

**Step 3: Make script executable**

```bash
chmod +x plugins/working-in-monorepos/hooks/scripts/detect-monorepo.sh
```

**Step 4: Test script runs without error**

Run: `bash plugins/working-in-monorepos/hooks/scripts/detect-monorepo.sh`

Expected: Script executes and prints output about monorepo detection.

**Step 5: Commit hooks**

```bash
git add plugins/working-in-monorepos/hooks/
git commit -m "feat: add SessionStart hook for monorepo detection

Automatically detects monorepo indicators and suggests initialization."
```

---

## Task 5: Create /monorepo-init Command

**Files:**
- Create: `plugins/working-in-monorepos/commands/monorepo-init.md`

**Step 1: Write command markdown**

```markdown
---
name: monorepo-init
description: Initialize monorepo configuration and activate working-in-monorepos skill
---

# Initialize Monorepo Configuration

This command runs the monorepo initialization script to detect subprojects and generate `.monorepo.json` configuration.

## Usage

First, preview what will be detected:

```bash
~/.claude/plugins/working-in-monorepos/skills/working-in-monorepos/scripts/monorepo-init --dry-run
```

Then, if the detection looks correct, write the configuration:

```bash
~/.claude/plugins/working-in-monorepos/skills/working-in-monorepos/scripts/monorepo-init --write
```

## What This Does

1. Detects repository root using `git rev-parse --show-toplevel`
2. Scans for subprojects by finding:
   - Directories with `package.json` (Node.js)
   - Directories with `Cargo.toml` (Rust)
   - Directories with `go.mod` (Go)
   - Directories with `pyproject.toml` or `setup.py` (Python)
3. Generates `.monorepo.json` with absolute paths and subproject metadata

## After Initialization

Once `.monorepo.json` is created, the working-in-monorepos skill provides guidance for:
- Executing commands in the correct subproject directory
- Using absolute paths to avoid directory confusion
- Defining command execution rules per subproject
```

**Step 2: Verify markdown formatting**

Run: `head -20 plugins/working-in-monorepos/commands/monorepo-init.md`

Expected: Valid frontmatter and readable markdown.

**Step 3: Commit command**

```bash
git add plugins/working-in-monorepos/commands/monorepo-init.md
git commit -m "feat: add /monorepo-init slash command"
```

---

## Task 6: Create git-workflows Plugin Metadata

**Files:**
- Create: `plugins/git-workflows/.claude-plugin/plugin.json`

**Step 1: Write plugin.json**

```json
{
  "name": "git-workflows",
  "version": "1.0.0",
  "description": "Git and GitHub workflow helpers including preferences, PR management, and best practices",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "homepage": "https://github.com/technicalpickles/pickled-claude-plugins",
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT",
  "keywords": ["git", "github", "workflow", "pull-request"]
}
```

**Step 2: Verify and commit**

```bash
cat plugins/git-workflows/.claude-plugin/plugin.json | python3 -m json.tool
git add plugins/git-workflows/.claude-plugin/plugin.json
git commit -m "feat: add git-workflows plugin metadata"
```

---

## Task 7: Create ci-cd-tools Plugin Metadata

**Files:**
- Create: `plugins/ci-cd-tools/.claude-plugin/plugin.json`

**Step 1: Write plugin.json**

```json
{
  "name": "ci-cd-tools",
  "version": "1.0.0",
  "description": "CI/CD workflow helpers for Buildkite and other continuous integration tools",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "homepage": "https://github.com/technicalpickles/pickled-claude-plugins",
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT",
  "keywords": ["ci-cd", "buildkite", "continuous-integration"]
}
```

**Step 2: Verify and commit**

```bash
cat plugins/ci-cd-tools/.claude-plugin/plugin.json | python3 -m json.tool
git add plugins/ci-cd-tools/.claude-plugin/plugin.json
git commit -m "feat: add ci-cd-tools plugin metadata"
```

---

## Task 8: Create debugging-tools Plugin Metadata

**Files:**
- Create: `plugins/debugging-tools/.claude-plugin/plugin.json`

**Step 1: Write plugin.json**

```json
{
  "name": "debugging-tools",
  "version": "1.0.0",
  "description": "Debugging helpers for Scope, MCPProxy, and other development tools",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "homepage": "https://github.com/technicalpickles/pickled-claude-plugins",
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT",
  "keywords": ["debugging", "scope", "mcpproxy", "development"]
}
```

**Step 2: Verify and commit**

```bash
cat plugins/debugging-tools/.claude-plugin/plugin.json | python3 -m json.tool
git add plugins/debugging-tools/.claude-plugin/plugin.json
git commit -m "feat: add debugging-tools plugin metadata"
```

---

## Task 9: Create dev-tools Plugin Metadata

**Files:**
- Create: `plugins/dev-tools/.claude-plugin/plugin.json`

**Step 1: Write plugin.json**

```json
{
  "name": "dev-tools",
  "version": "1.0.0",
  "description": "General development tools including scratch area management and productivity helpers",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "homepage": "https://github.com/technicalpickles/pickled-claude-plugins",
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT",
  "keywords": ["development", "productivity", "scratch", "tools"]
}
```

**Step 2: Verify and commit**

```bash
cat plugins/dev-tools/.claude-plugin/plugin.json | python3 -m json.tool
git add plugins/dev-tools/.claude-plugin/plugin.json
git commit -m "feat: add dev-tools plugin metadata"
```

---

## Task 10: Update Root Marketplace Configuration

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read current marketplace.json**

Run: `cat .claude-plugin/marketplace.json`

**Step 2: Replace with updated configuration**

```json
{
  "name": "technicalpickles-marketplace",
  "description": "Personal plugins marketplace for Josh Nichols",
  "owner": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "plugins": [
    {
      "name": "working-in-monorepos",
      "description": "Navigate and execute commands in monorepo subprojects",
      "version": "1.0.0",
      "source": "./plugins/working-in-monorepos",
      "author": {
        "name": "Josh Nichols",
        "email": "josh@technicalpickles.com"
      }
    },
    {
      "name": "git-workflows",
      "description": "Git and GitHub workflow helpers",
      "version": "1.0.0",
      "source": "./plugins/git-workflows",
      "author": {
        "name": "Josh Nichols",
        "email": "josh@technicalpickles.com"
      }
    },
    {
      "name": "ci-cd-tools",
      "description": "CI/CD workflow helpers for Buildkite",
      "version": "1.0.0",
      "source": "./plugins/ci-cd-tools",
      "author": {
        "name": "Josh Nichols",
        "email": "josh@technicalpickles.com"
      }
    },
    {
      "name": "debugging-tools",
      "description": "Debugging helpers for Scope and MCPProxy",
      "version": "1.0.0",
      "source": "./plugins/debugging-tools",
      "author": {
        "name": "Josh Nichols",
        "email": "josh@technicalpickles.com"
      }
    },
    {
      "name": "dev-tools",
      "description": "General development and productivity tools",
      "version": "1.0.0",
      "source": "./plugins/dev-tools",
      "author": {
        "name": "Josh Nichols",
        "email": "josh@technicalpickles.com"
      }
    }
  ]
}
```

**Step 3: Verify JSON is valid**

Run: `cat .claude-plugin/marketplace.json | python3 -m json.tool`

Expected: Pretty-printed JSON with all five plugins listed.

**Step 4: Commit marketplace update**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: update marketplace with five plugins

Configure marketplace to reference all plugins in plugins/ directory."
```

---

## Task 11: Update README for Plugin Marketplace

**Files:**
- Modify: `README.md`

**Step 1: Read current README**

Run: `cat README.md`

**Step 2: Replace with marketplace-focused README**

```markdown
# Pickled Claude Plugins

Personal plugin marketplace for Claude Code containing domain-organized development tools, workflows, and helpers.

## Installation

### Automatic (via technicalpickles/dotfiles)

If you use [technicalpickles/dotfiles](https://github.com/technicalpickles/dotfiles), the marketplace is installed automatically via `install.sh`.

### Manual Installation

```bash
git clone https://github.com/technicalpickles/pickled-claude-plugins ~/.claude/plugins/technicalpickles
```

## Plugins Included

### working-in-monorepos

Navigate and execute commands in monorepo subprojects with proper directory handling.

**Features:**
- Auto-detect monorepo structure on session start
- `/monorepo-init` command for configuration generation
- Skill guidance for absolute path usage
- Command execution rules per subproject

**Skills:** working-in-monorepos

### git-workflows

Git and GitHub workflow helpers including preferences, PR management, and best practices.

**Skills:** git-preferences-and-practices, gh-pr

### ci-cd-tools

CI/CD workflow helpers for Buildkite and other continuous integration tools.

**Skills:** buildkite-status

### debugging-tools

Debugging helpers for Scope, MCPProxy, and other development tools.

**Skills:** scope, mcpproxy-debug

### dev-tools

General development tools including scratch area management and productivity helpers.

**Skills:** working-in-scratch-areas

## Usage

### Using Skills

Skills are available in Claude Code via the Skill tool:

```
Use the technicalpickles:working-in-monorepos skill
```

Or reference them in custom skills:

```markdown
@technicalpickles:buildkite-status for checking CI status
```

### Using Commands

Slash commands are available after plugin installation:

```
/monorepo-init
```

### Hooks

Some plugins include hooks that run automatically:

- **working-in-monorepos**: SessionStart hook detects monorepo structure

## Development

### Plugin Structure

Each plugin follows the Claude Code plugin specification:

```
plugins/{plugin-name}/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata
├── skills/              # One or more skills
│   └── {skill-name}/
│       └── SKILL.md
├── commands/            # Optional slash commands
│   └── {command}.md
└── hooks/              # Optional event hooks
    ├── hooks.json
    └── scripts/
```

### Modifying Plugins

To modify plugins:

1. Edit files in `~/workspace/pickled-claude-plugins/plugins/`
2. Changes are immediately available to Claude (if installed via symlink)
3. Commit and push to share across machines

## Version History

- **1.0.0** (2025-11-13): Initial marketplace release with five plugins

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Josh Nichols ([@technicalpickles](https://github.com/technicalpickles))
```

**Step 3: Verify markdown formatting**

Run: `head -50 README.md`

Expected: Well-formatted markdown with clear sections.

**Step 4: Commit README update**

```bash
git add README.md
git commit -m "docs: update README for plugin marketplace

Reflect new plugin-based structure and marketplace organization."
```

---

## Task 12: Remove Empty skills/ Directory

**Files:**
- Delete: `skills/` (should be empty after moves)

**Step 1: Verify skills/ is empty**

Run: `ls -la skills/`

Expected: Directory should be empty or not exist.

**Step 2: Remove empty directory**

```bash
rmdir skills/ 2>/dev/null || echo "Directory already removed or not empty"
```

**Step 3: Verify removal**

Run: `ls -d skills/ 2>/dev/null || echo "skills/ directory removed successfully"`

Expected: "skills/ directory removed successfully"

**Step 4: Commit removal**

```bash
git add -A
git commit -m "chore: remove empty skills directory

All skills migrated to plugins/ structure."
```

---

## Task 13: Remove .gitkeep Files

**Files:**
- Delete all `.gitkeep` files added in Task 1

**Step 1: Find and remove .gitkeep files**

```bash
find plugins -name .gitkeep -delete
```

**Step 2: Verify removal**

Run: `find plugins -name .gitkeep`

Expected: No output (all .gitkeep files removed).

**Step 3: Commit cleanup**

```bash
git add -A
git commit -m "chore: remove .gitkeep files

Remove placeholder files now that directories contain real content."
```

---

## Task 14: Final Verification

**Step 1: Verify all plugins have metadata**

Run: `find plugins -name plugin.json | sort`

Expected: Five plugin.json files, one per plugin.

**Step 2: Verify all skills migrated**

Run: `find plugins -name "SKILL.md" | wc -l`

Expected: 7 (all original skills present).

**Step 3: Verify git history preserved**

Run: `git log --follow plugins/working-in-monorepos/skills/working-in-monorepos/SKILL.md | head -20`

Expected: Git log shows history from before the move.

**Step 4: Verify marketplace configuration**

Run: `cat .claude-plugin/marketplace.json | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Plugins: {len(data[\"plugins\"])}')"`

Expected: "Plugins: 5"

**Step 5: Review commit log**

Run: `git log --oneline --graph | head -20`

Expected: Clean series of commits for each task.

---

## Post-Implementation

After completing all tasks, the repository structure will be:

```
pickled-claude-plugins/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json (with 5 plugins)
├── plugins/
│   ├── working-in-monorepos/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/working-in-monorepos/
│   │   ├── commands/monorepo-init.md
│   │   └── hooks/hooks.json + scripts/
│   ├── git-workflows/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/ (2 skills)
│   ├── ci-cd-tools/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/buildkite-status/
│   ├── debugging-tools/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/ (2 skills)
│   └── dev-tools/
│       ├── .claude-plugin/plugin.json
│       └── skills/working-in-scratch-areas/
├── docs/plans/ (design + this plan)
├── README.md (updated)
└── LICENSE
```

All tasks preserve git history, follow Claude Code plugin specification, and maintain backwards compatibility with existing skill names.

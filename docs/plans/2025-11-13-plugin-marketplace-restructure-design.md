# Plugin Marketplace Restructure Design

**Date:** 2025-11-13
**Status:** Approved

## Summary

Transform claude-skills repository into pickled-claude-plugins, a personal plugin marketplace. Each plugin will contain skills, commands, hooks, and supporting files organized under a unified structure.

## Current State

The repository contains seven standalone skills in a flat `skills/` directory:
- working-in-monorepos (scripts, examples, tests)
- buildkite-status (references, scripts)
- scope (references, scripts)
- mcpproxy-debug (references, scripts, assets)
- working-in-scratch-areas (scripts)
- git-preferences-and-practices (single file)
- gh-pr (single file)

Repository metadata exists at `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

## Target State

### Repository Structure

```
pickled-claude-plugins/
├── .claude-plugin/
│   ├── plugin.json           # Root marketplace metadata
│   └── marketplace.json      # Plugin registry
├── plugins/
│   ├── working-in-monorepos/
│   ├── git-workflows/
│   ├── ci-cd-tools/
│   ├── debugging-tools/
│   └── dev-tools/
├── README.md
└── LICENSE
```

### Plugin Organization

Skills group into five plugins by domain:

1. **working-in-monorepos** (standalone)
   - Skill: working-in-monorepos
   - Command: /monorepo-init
   - Hook: SessionStart detection

2. **git-workflows** (combined)
   - Skills: git-preferences-and-practices, gh-pr

3. **ci-cd-tools**
   - Skill: buildkite-status

4. **debugging-tools**
   - Skills: scope, mcpproxy-debug

5. **dev-tools**
   - Skill: working-in-scratch-areas

### Plugin Directory Layout

Each plugin follows this structure:

```
plugins/{plugin-name}/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── {skill-name}/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── examples/
├── commands/          # Optional
│   └── {command}.md
└── hooks/             # Optional
    ├── hooks.json
    └── scripts/
```

### Working-in-Monorepos Plugin Detail

This plugin demonstrates the full structure:

**Metadata** (`.claude-plugin/plugin.json`):
```json
{
  "name": "working-in-monorepos",
  "version": "1.0.0",
  "description": "Navigate and execute commands in monorepo subprojects",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT"
}
```

**SessionStart Hook** (hooks/hooks.json):
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

**Slash Command** (commands/monorepo-init.md):
```markdown
---
name: monorepo-init
description: Initialize monorepo configuration
---

Run monorepo-init script to detect subprojects and generate .monorepo.json.

Preview detection:
~/.claude/plugins/working-in-monorepos/skills/working-in-monorepos/scripts/monorepo-init --dry-run

Write configuration:
~/.claude/plugins/working-in-monorepos/skills/working-in-monorepos/scripts/monorepo-init --write
```

## Migration Plan

### Phase 1: Create Structure

Create plugin directories:
```bash
mkdir -p plugins/{working-in-monorepos,git-workflows,ci-cd-tools,debugging-tools,dev-tools}/{.claude-plugin,skills}
mkdir -p plugins/working-in-monorepos/{commands,hooks/scripts}
```

### Phase 2: Move Skills

Use `git mv` to preserve history:

```bash
# Standalone plugin
git mv skills/working-in-monorepos plugins/working-in-monorepos/skills/

# Combined plugins
git mv skills/git-preferences-and-practices plugins/git-workflows/skills/
git mv skills/gh-pr.md plugins/git-workflows/skills/gh-pr/SKILL.md

# Domain-grouped plugins
git mv skills/buildkite-status plugins/ci-cd-tools/skills/
git mv skills/scope plugins/debugging-tools/skills/
git mv skills/mcpproxy-debug plugins/debugging-tools/skills/
git mv skills/working-in-scratch-areas plugins/dev-tools/skills/
```

### Phase 3: Create Plugin Files

Write for each plugin:
- `.claude-plugin/plugin.json` with metadata
- Hook configurations where applicable
- Command definitions where applicable

### Phase 4: Update Root Files

Update marketplace registry:
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
      "source": "./plugins/working-in-monorepos",
      "version": "1.0.0"
    },
    {
      "name": "git-workflows",
      "source": "./plugins/git-workflows",
      "version": "1.0.0"
    },
    {
      "name": "ci-cd-tools",
      "source": "./plugins/ci-cd-tools",
      "version": "1.0.0"
    },
    {
      "name": "debugging-tools",
      "source": "./plugins/debugging-tools",
      "version": "1.0.0"
    },
    {
      "name": "dev-tools",
      "source": "./plugins/dev-tools",
      "version": "1.0.0"
    }
  ]
}
```

Update README.md to reflect marketplace structure.

### Phase 5: Clean Up

Remove empty `skills/` directory:
```bash
rmdir skills
```

## Installation Path

Installation path remains `~/.claude/plugins/technicalpickles`, pointing to repository root. The marketplace structure allows Claude Code to discover all plugins within.

## Testing Strategy

After migration:
1. Verify each plugin loads in Claude Code
2. Test SessionStart hook for working-in-monorepos
3. Test /monorepo-init command
4. Verify skills invoke correctly
5. Confirm git history preserved for moved files

## Success Criteria

- All skills accessible through new plugin structure
- Git history preserved for all moved files
- SessionStart hook activates working-in-monorepos skill
- /monorepo-init command available
- README accurately documents new structure
- Repository renamed to pickled-claude-plugins

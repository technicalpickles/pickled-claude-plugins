---
name: working-in-monorepos
description: Use when working in repositories with multiple subprojects (monorepos) where commands need to run from specific directories - prevents directory confusion, redundant cd commands, and ensures commands execute from correct locations
---

# Working in Monorepos

## Overview

Helps Claude work effectively in monorepo environments by ensuring commands always execute from the correct location using absolute paths.

**Core principle:** Bash shell state is not guaranteed between commands. Always use absolute paths.

## When to Use

Use this skill when:

- Repository contains multiple subprojects (ruby/, cli/, components/\*, etc.)
- Commands must run from specific directories
- Working across multiple subprojects in one session

Don't use for:

- Single-project repositories
- Repositories where all commands run from root

## Use Absolute Paths

Run each command in a monorepo subproject with an absolute `cd` prefix:

✅ **CORRECT:**

```bash
cd /Users/josh/workspace/schemaflow/ruby && bundle exec rspec
cd /Users/josh/workspace/schemaflow/cli && npm test
```

❌ **WRONG:**

```bash
# Relative paths (assumes current directory)
cd ruby && bundle exec rspec

# No cd prefix (assumes location)
bundle exec rspec

# Chaining cd (compounds errors)
cd ruby && cd ruby && rspec
```

**Why:** You cannot rely on shell state. Absolute paths guarantee correct execution location regardless of where the shell currently is.

## Constructing Absolute Paths

### With .monorepo.json Config

If `.monorepo.json` exists at repo root:

1. Read `root` field for absolute repo path
2. Read subproject `path` from `subprojects` map
3. Construct: `cd {root}/{path} && command`

Example:

```json
{
  "root": "/Users/josh/workspace/schemaflow",
  "subprojects": { "ruby": { "path": "ruby" } }
}
```

→ `cd /Users/josh/workspace/schemaflow/ruby && bundle exec rspec`

### Without Config

Use git to find repo root, then construct absolute path:

1. Get the repo root once per session: `git rev-parse --show-toplevel`
2. Use that absolute path: `cd /absolute/path/to/repo/ruby && bundle exec rspec`

**Example workflow:**

```bash
# Step 1: Get repo root
git rev-parse --show-toplevel
# Output: /Users/josh/workspace/schemaflow

# Step 2: Use absolute path in commands
cd /Users/josh/workspace/schemaflow/ruby && bundle exec rspec
```

**Why not use command substitution:** `cd $(git rev-parse --show-toplevel)/ruby` requires user approval. Instead, run `git rev-parse` once, then use the absolute path directly in all subsequent commands.

**⚠️ Git subtree caveat:** In repositories containing git subtrees (nested git repos), `git rev-parse --show-toplevel` returns the innermost repo root, not the monorepo root. This makes it unreliable for subtree scenarios. Creating a `.monorepo.json` config is the robust solution that works in all cases.

## Setup Workflow (No Config Present)

When the repo looks like a monorepo but has no `.monorepo.json`, offer to generate one with `scripts/monorepo-init`. If the user agrees, run it with `--dry-run`, show the output, and run it with `--write` once they approve. If not, get the repo root once with `git rev-parse` and use absolute paths. They can also write `.monorepo.json` by hand from the schema below.

**Script location:** `scripts/monorepo-init` in this skill's base directory. Call it by absolute path so it works from any directory. `--help` documents every flag, so there's no need to read the source.

## Command Execution Rules (With Config)

If `.monorepo.json` defines command rules:

```json
{
  "commands": {
    "rubocop": { "location": "root" },
    "rspec": {
      "location": "subproject",
      "command": "bundle exec rspec",
      "overrides": { "root": { "command": "bin/rspec" } }
    }
  }
}
```

**Check rules before executing:**

1. Look up command in `commands` map
2. Check `location`: "root" | "subproject"
3. Check for `command` override
4. Check for context-specific `overrides`

**Example:**

- rubocop: Always run from repo root
- rspec in ruby/: Use `bundle exec rspec`
- rspec in root project: Use `bin/rspec`

## Quick Reference

| Task                    | Command Pattern                                                                                         |
| ----------------------- | ------------------------------------------------------------------------------------------------------- |
| Get repo root           | `git rev-parse --show-toplevel` (run once, use result in all commands)                                  |
| Run tests in subproject | `cd /absolute/path/to/repo/subproject && test-command`                                                  |
| With config             | `cd {root}/{subproject.path} && command`                                                                |
| Check for config        | `test -f .monorepo.json`                                                                                |
| Generate config         | `<skill-dir>/scripts/monorepo-init --dry-run` (works from any directory)      |
| Always rule             | Absolute path and `cd` prefix on each command. Get the repo root once, then use it directly.          |

## Configuration Schema

`.monorepo.json` at repository root:

```json
{
  "root": "/absolute/path/to/repo",
  "subprojects": {
    "subproject-id": {
      "path": "relative/path",
      "type": "ruby|node|go|python|rust|java",
      "description": "Optional"
    }
  },
  "commands": {
    "command-name": {
      "location": "root|subproject",
      "command": "optional override",
      "overrides": {
        "context": { "command": "context-specific" }
      }
    }
  }
}
```

**Minimal example:**

```json
{
  "root": "/Users/josh/workspace/schemaflow",
  "subprojects": {
    "ruby": { "path": "ruby", "type": "ruby" },
    "cli": { "path": "cli", "type": "node" }
  }
}
```

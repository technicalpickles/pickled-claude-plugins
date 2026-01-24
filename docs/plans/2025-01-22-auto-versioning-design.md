# Auto-Versioning Design

Automatic version bumping for plugins using git hooks and conventional commits.

## Problem

1. **New plugins don't get registered** - Adding a plugin directory doesn't add it to `marketplace.json`
2. **Changes don't bump versions** - The marketplace only sees updates when versions change

## Solution

Two git hooks via [hk](https://github.com/jdx/hk):

| Hook | Purpose |
|------|---------|
| `pre-commit` | Block if new plugins aren't in `marketplace.json` |
| `commit-msg` | Validate conventional commit format, bump versions, amend commit |

## Conventional Commit Mapping

| Prefix | Bump |
|--------|------|
| `feat:` | minor |
| `fix:`, `perf:`, `refactor:` | patch |
| `BREAKING CHANGE:` in body or `!` | major |
| `chore:`, `docs:`, `test:`, `ci:`, `style:`, `build:` | none |

## Multi-Plugin Commits

When a commit touches multiple plugins:

- **No scope** (`feat: add discovery`) → bump ALL changed plugins
- **With scope** (`feat(tool-routing): add discovery`) → bump ONLY the scoped plugin

This lets you make focused bumps when needed while defaulting to bumping everything that changed.

## Files

```
hk.pkl                                    # hk configuration
scripts/hooks/
├── check-marketplace-registry.sh         # pre-commit guard
└── version-bump.py                       # commit-msg validation + bumping
```

### hk.pkl

```pkl
amends "package://pkg.hk.jdx.dev/hk@1/Config.pkl"

linters {
  ["check-registry"] {
    check = "scripts/hooks/check-marketplace-registry.sh"
  }
  ["version-bump"] {
    check = "uv run scripts/hooks/version-bump.py {{commit_msg_file}}"
  }
}

hooks {
  ["pre-commit"] {
    steps = ["check-registry"]
  }
  ["commit-msg"] {
    steps = ["version-bump"]
  }
}
```

### check-marketplace-registry.sh

**Logic:**
1. Find all directories matching `plugins/*/` containing `.claude-plugin/plugin.json`
2. Parse `.claude-plugin/marketplace.json` to get registered plugin names
3. If any plugin dirs aren't registered, exit 1 with message

**Output on failure:**
```
ERROR: Unregistered plugins detected

The following plugins are not in .claude-plugin/marketplace.json:
  - my-new-plugin

Add them to marketplace.json before committing:
  "my-new-plugin": { "source": "./plugins/my-new-plugin" }
```

### version-bump.py

**Logic:**
1. Parse commit message from file passed as argument
2. Validate conventional commit format (exit 1 if invalid)
3. Determine bump type from commit type
4. If bump type is "none" (chore, docs, etc.), exit 0 early
5. Get staged files via `git diff --cached --name-only`
6. Extract unique plugin names from `plugins/{name}/...` paths
7. If scope matches a plugin name, filter to only that plugin
8. For each affected plugin:
   - Read `.claude-plugin/plugin.json`
   - Increment version according to bump type
   - Write updated file
   - Stage with `git add`
9. Amend commit with `git commit --amend --no-edit`

**Commit message validation pattern:**
```
^(feat|fix|perf|refactor|chore|docs|test|ci|style|build)(\(.+\))?!?: .+
```

**Output on invalid message:**
```
ERROR: Commit message doesn't follow conventional commit format

Expected: <type>(<scope>): <description>
Got: "updated stuff"

Valid types: feat, fix, perf, refactor, chore, docs, test, ci, style, build
Examples:
  feat: add new route type
  fix(tool-routing): handle missing config
  chore: update dependencies
```

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| No plugins changed | Skip versioning, just validate format |
| Invalid version in plugin.json | Error with clear message |
| Scope doesn't match any plugin | Warning, bump all changed plugins anyway |
| Amend fails | Warning (don't fail commit), user can amend manually |

## Setup

1. Install hk: `mise use -g hk` or `brew install jdx/tap/hk`
2. Run `hk install` in repo root

## CLAUDE.md Update

Add to CLAUDE.md:

```markdown
## Versioning

This repo uses conventional commits with automatic version bumping.

**Commit format:** `<type>(<scope>): <description>`

| Type | Version Bump |
|------|--------------|
| `feat` | minor |
| `fix`, `perf`, `refactor` | patch |
| `chore`, `docs`, `test`, `ci` | none |

Add `BREAKING CHANGE:` in body or `!` after type for major bump.

**Multi-plugin commits:** All changed plugins are bumped unless you specify a scope matching a plugin name.

**New plugins:** Must be added to `.claude-plugin/marketplace.json` before committing.
```

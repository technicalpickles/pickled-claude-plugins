# hk Skill Design

## Goal

Create a reference skill for working with hk (git hook manager by jdx) in the dev-tools plugin. The skill helps Claude detect hk usage, understand configuration, use builtins, and find documentation/issues.

## Key Decisions

- **Location:** `plugins/dev-tools/skills/hk/`
- **Scope:** Configuration, troubleshooting, reference lookups (all equally common)
- **Progressive disclosure:** Core concepts inline, detailed reference in separate files
- **Detection:** Include signals for hk vs other hook managers
- **Documentation strategy:** Embed stable reference, crawl/gh for issues and latest
- **Custom steps:** Out of scope - focus on builtins only

## File Structure

```
plugins/dev-tools/skills/hk/
├── SKILL.md              # Core: detection, commands, concepts, lookup guidance
├── hk-pkl-reference.md   # hk.pkl structure, syntax, examples
└── builtins-reference.md # Full builtins list with options
```

## Implementation Tasks

### Task 1: Create SKILL.md

**Frontmatter:**
```yaml
name: hk
description: Use when hk.pkl exists in project, hook output shows hk running, or working with git hooks in hk-managed projects. Also use when setting up, configuring, or troubleshooting hk git hooks.
```

**Content sections:**

1. **Overview** - What hk is (git hook manager by jdx, uses pkl config)

2. **Detection** - How to identify hk vs other hook managers:
   - `hk.pkl` at root → hk
   - `lefthook.yml` → lefthook
   - `.husky/` directory → husky
   - `.pre-commit-config.yaml` → pre-commit (python)

3. **Key Commands:**
   - `hk init` - Create initial hk.pkl
   - `hk install` - Set up git hooks
   - `hk check` - Run checks manually
   - `hk fix` - Auto-fix issues
   - `hk builtins` - List available builtins
   - `hk validate` - Validate config

4. **Core Concepts:**
   - Hooks (pre-commit, commit-msg, pre-push)
   - Steps (named units of work within hooks)
   - Builtins (pre-built linters/checkers)
   - Profiles (enable/disable groups of steps)

5. **Finding Help:**
   - Stable reference: Load hk-pkl-reference.md or builtins-reference.md
   - Latest docs: `npx @mdream/crawl https://hk.jdx.dev/`
   - GitHub issues: `gh issue list -R jdx/hk` or `gh search issues --repo jdx/hk "<query>"`
   - Repo: https://github.com/jdx/hk

6. **Quick Reference Table** - Common tasks with commands

### Task 2: Create hk-pkl-reference.md

Extract from crawled docs at `/tmp/hk-docs.md/configuration-html.md`:

1. **Basic Structure:**
   - `amends` declaration
   - Importing Builtins.pkl
   - Hook definitions

2. **Hook Types:**
   - pre-commit
   - commit-msg
   - prepare-commit-msg
   - pre-push

3. **Step Definition:**
   - `check` - command to run
   - `fix` - optional auto-fix command
   - `glob` - file patterns
   - `stage_fixed` - re-stage fixed files

4. **Using Builtins:**
   - Import syntax
   - Customizing builtin options
   - Common builtins with examples

5. **Working Examples:**
   - From this repo's hk.pkl
   - Common patterns

### Task 3: Create builtins-reference.md

Extract from `/tmp/hk-docs.md/builtins-html.md`:

1. **Quick Lookup Table** - Name, purpose, common options

2. **Categories:**
   - Validation (check-conventional-commit, check-merge-conflict, etc.)
   - Formatting (trailing-whitespace, end-of-file-fixer, etc.)
   - Security (detect-private-key, check-added-large-files, etc.)

3. **Per-builtin details** - Only most commonly used ones with full options

### Task 4: Test the skill

Per writing-skills TDD approach:
- Create pressure scenarios
- Run without skill (baseline)
- Run with skill
- Verify improvement

## Reference Materials

- Crawled docs: `/tmp/hk-docs.md/`
- This repo's hk.pkl: `/Users/josh.nichols/workspace/pickled-claude-plugins/hk.pkl`
- GitHub: https://github.com/jdx/hk
- Docs site: https://hk.jdx.dev/

## Success Criteria

1. Skill activates when hk.pkl detected or user mentions hk
2. Core SKILL.md is concise (<300 words) with progressive disclosure to reference files
3. Reference files provide complete information for configuration and builtins
4. Troubleshooting guidance helps find docs/issues dynamically

# Plugin Versioning

This document explains how plugin versions are managed in this marketplace.

## Quick Reference

```bash
# Check what bumps are needed
./scripts/analyze-version-bumps.sh

# Bump a plugin manually
./scripts/bump-version.sh git minor

# Auto-bump all plugins based on commits
./scripts/bump-version.sh --auto
```

## How It Works

**Single source of truth:** Versions live only in `.claude-plugin/marketplace.json`, not in individual plugin.json files.

**Conventional commits drive bumps:** The commit message format determines what version changes are needed.

**Bump in your PR before merging.** Run `./scripts/bump-version.sh --auto` and commit the result as `chore(<plugin>): bump version to X.Y.Z`. The Version Check workflow fails if pending bumps aren't applied, so you can't merge without doing this.

## Commit Format

All commits use [Conventional Commits](https://www.conventionalcommits.org/). The type decides the bump:

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | minor |
| `fix` | Bug fix | patch |
| `perf` | Performance improvement | patch |
| `docs` | Documentation only | none |
| `style` | Formatting, no code change | none |
| `refactor` | Code change, no feature/fix | none |
| `test` | Adding tests | none |
| `chore` | Maintenance | none |
| `ci` | CI configuration | none |
| `build` | Build system changes | none |

### Scopes

**Required for:** `feat`, `fix`, `perf` (changes that affect plugin behavior)

**Optional for:** `chore`, `docs`, `ci`, `style`, `test`, `refactor`, `build`

**Valid scopes:** any plugin `name` in `.claude-plugin/marketplace.json` (`scripts/check-commit-scope.sh` reads the list from there), or `repo` for repo-wide changes.

### Breaking Changes

Add `!` after the type or include `BREAKING CHANGE:` in the footer for major version bumps:

```
feat(git)!: change commit message format

BREAKING CHANGE: The --message flag now requires quotes.
```

## PR Workflow

Branch from main, commit in conventional format, run `./scripts/bump-version.sh --auto` and commit the bump, then open the PR. CI checks commit format, that scopes are plugin names, and that pending bumps are applied (blocks merge otherwise).

## Local Validation

Hooks run automatically on commit via [hk](https://hk.jdx.dev/):

- **pre-commit:** Validates no version in plugin.json files
- **commit-msg:** Validates conventional commit format and scope

To run hooks manually:
```bash
hk run pre-commit
```

## Scripts

### analyze-version-bumps.sh

Analyzes commits on current branch vs main to determine required bumps.

```bash
# Show required bumps
./scripts/analyze-version-bumps.sh

# Output as JSON
./scripts/analyze-version-bumps.sh --json

# Exit 1 if bumps needed (for CI)
./scripts/analyze-version-bumps.sh --require
```

### bump-version.sh

Applies version bumps to marketplace.json.

```bash
# Bump specific plugin
./scripts/bump-version.sh <plugin> <major|minor|patch>
./scripts/bump-version.sh git minor

# Auto-bump all based on commits
./scripts/bump-version.sh --auto

# Dry run (show what would change)
./scripts/bump-version.sh --auto --dry-run
```

### validate-plugin-versions.sh

Ensures version consistency:
- No plugin.json files have version fields
- All marketplace plugins have plugin.json files

```bash
./scripts/validate-plugin-versions.sh
```

### check-commit-scope.sh

Validates commit message scopes (called by hk commit-msg hook).

```bash
./scripts/check-commit-scope.sh .git/COMMIT_EDITMSG
```

## Troubleshooting

### "Commit type 'feat' requires a scope" / "Invalid scope 'foo'"

`feat`, `fix`, and `perf` need a scope that is a plugin name or `repo` (see Scopes above).

### Version not bumping

1. Check your commit types - only `feat`, `fix`, `perf` trigger bumps
2. Check your scope - scopeless commits don't bump plugins
3. Run `./scripts/analyze-version-bumps.sh` to see what's detected

### A `docs()` commit that's really a feature

`bump-version.sh --auto` bumps by conventional commit type (`feat` → minor, `docs` → no bump), not by intent. For plugins, documentation often IS the deliverable (skills are markdown content), so a `docs()` commit that adds a new reference file under `skills/<skill>/references/` or otherwise expands what a skill teaches Claude is a feature in plugin terms even though the commit type is `docs`.

Before pushing a `docs(<plugin>):` commit, ask: does this change what the skill teaches Claude? If yes, bump by hand:

```bash
./scripts/bump-version.sh <plugin> minor
git add .claude-plugin/marketplace.json
git commit -m "chore(<plugin>): bump version to X.Y.0"
```

If it's a typo fix, internal note, or commentary on existing content with no behavior change, no bump needed.

### Hook not running

Ensure hk is installed:
```bash
hk install
```

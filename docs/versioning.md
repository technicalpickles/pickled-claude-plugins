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

**Auto-bump on PR approval:** When a PR is approved, GitHub Actions automatically commits the version bumps.

## Commit Format

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

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

**Valid scopes:**
- Plugin names: `git`, `ci-cd-tools`, `tool-routing`, `dev-tools`, `mcpproxy`, `second-brain`, `stay-on-target`, `working-in-monorepos`
- Repo-wide: `repo`

### Breaking Changes

Add `!` after the type or include `BREAKING CHANGE:` in the footer for major version bumps:

```
feat(git)!: change commit message format

BREAKING CHANGE: The --message flag now requires quotes.
```

### Examples

```bash
# Minor bump to git plugin
feat(git): add stash list command

# Patch bump to ci-cd-tools
fix(ci-cd-tools): handle build timeout gracefully

# No version bump (docs only)
docs(git): update README with examples

# No version bump (repo-wide maintenance)
chore: update dependencies

# Major bump (breaking change)
feat(tool-routing)!: change route configuration format
```

## PR Workflow

1. **Create branch** from main
2. **Make commits** using conventional format
3. **Push and create PR**
4. **CI validates:**
   - Commit format is correct
   - Scopes are valid plugin names
   - Reports what version bumps are needed
   - **Fails if bumps are pending** (blocks merge until applied)
5. **Get PR approved**
6. **Auto-bump:** GitHub Actions commits version updates to your branch
7. **CI re-runs:** Now passes (no pending bumps)
8. **Merge PR**

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

### "Commit type 'feat' requires a scope"

Add a scope to your commit message:
```bash
# Wrong
git commit -m "feat: add new feature"

# Right
git commit -m "feat(git): add new feature"
```

### "Invalid scope 'foo'"

Use a valid plugin name or `repo`:
```bash
# Valid scopes
feat(git): ...
feat(ci-cd-tools): ...
feat(repo): ...  # for repo-wide features
chore: ...       # scope optional for chore
```

### Version not bumping

1. Check your commit types - only `feat`, `fix`, `perf` trigger bumps
2. Check your scope - scopeless commits don't bump plugins
3. Run `./scripts/analyze-version-bumps.sh` to see what's detected

### Hook not running

Ensure hk is installed:
```bash
hk install
```

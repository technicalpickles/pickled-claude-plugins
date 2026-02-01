# Plan: Semantic Versioning Automation

## Goal

Automate plugin version management using conventional commits:
- Enforce semantic commit format on all commits
- Detect which plugins changed and what bump is needed
- Block PR merge if version bump is missing
- Make bumping easy with tooling

## Current State

- ✅ Single source of truth: `marketplace.json` (version removed from plugin.json)
- ✅ Pre-commit validation script exists: `scripts/validate-plugin-versions.sh`
- ⚠️ Manual symlink for pre-commit hook (not managed)
- ❌ No conventional commit enforcement
- ❌ No version bump detection/automation
- ❌ No CI checks on PRs

## Workflow After Implementation

```
1. Create feature branch
2. Make changes with conventional commits:
   - feat(git): add stash support     → minor bump
   - fix(ci-cd-tools): handle timeout → patch bump
   - chore(git): update docs          → no bump
3. Create PR
4. CI analyzes commits, reports required bumps
5. Run `./scripts/bump-version.sh git minor` (or auto-bump)
6. CI passes, merge PR
```

## Tasks

### Phase 1: Hook Management with hk ✅

- [x] Upgrade hk to v1.35.0 (has `check-conventional-commit` builtin)
- [x] Create `hk.pkl` configuration
- [x] Run `hk install` to set up hooks
- [x] Remove manual pre-commit symlink
- [x] Create `scripts/check-commit-scope.sh` for scope validation

**hk.pkl hooks configured:**
1. `pre-commit`: Run `validate-plugin-versions.sh`
2. `commit-msg`: Enforce conventional commit format + valid scopes

### Phase 2: Version Bump Tooling ✅

- [x] Create `scripts/analyze-version-bumps.sh`
  - Compare current branch to main
  - Detect which plugins have file changes
  - Parse conventional commits to determine bump type
  - Output required version bumps (text and JSON)

- [x] Create `scripts/bump-version.sh`
  - Usage: `./scripts/bump-version.sh <plugin> <major|minor|patch>`
  - Usage: `./scripts/bump-version.sh --auto`
  - Updates version in `marketplace.json`
  - Auto-detects bump type from commits with `--auto`

### Phase 3: CI Enforcement & Auto-Bump ✅

- [x] Create `.github/workflows/version-check.yml`
  - Runs on PRs to main
  - Validates conventional commit format
  - Validates commit scopes
  - Analyzes commits to determine required bumps
  - Comments on PR with bump info

- [x] Create `.github/workflows/auto-bump.yml`
  - Triggers on PR approval
  - Runs analyze script
  - Auto-commits version bumps to PR branch
  - Comments on PR when done

- [ ] Enable branch protection on main (manual step)
  - Require status checks to pass
  - Require PR reviews

### Phase 4: Documentation ✅

- [x] Create `docs/versioning.md` with full workflow details
- [x] Update CLAUDE.md with brief reference (progressive disclosure)
- [x] Document conventional commit format and examples
- [x] Document all scripts and their usage

## Conventional Commit Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | minor |
| `fix` | Bug fix | patch |
| `docs` | Documentation only | none |
| `style` | Formatting, no code change | none |
| `refactor` | Code change, no feature/fix | none |
| `perf` | Performance improvement | patch |
| `test` | Adding tests | none |
| `chore` | Maintenance | none |
| `ci` | CI configuration | none |
| `build` | Build system changes | none |

**Scope:** Plugin name (e.g., `git`, `ci-cd-tools`, `tool-routing`)

**Breaking changes:** Add `!` after type or `BREAKING CHANGE:` in footer → major bump

**Examples:**
```
feat(git): add stash list command
fix(ci-cd-tools): handle build timeout gracefully
feat(tool-routing)!: change route config format
chore: update dependencies
```

## File Changes

```
pickled-claude-plugins/
├── hk.pkl                                    # NEW: hk configuration
├── scripts/
│   ├── validate-plugin-versions.sh           # EXISTS: update to work with hk
│   ├── analyze-version-bumps.sh              # NEW: detect required bumps
│   └── bump-version.sh                       # NEW: apply version bumps
├── .github/
│   └── workflows/
│       └── version-check.yml                 # NEW: PR enforcement
└── .git/hooks/
    ├── pre-commit                            # MANAGED BY hk
    └── commit-msg                            # MANAGED BY hk
```

## Decisions

1. **Auto-bump:** Yes - CI will auto-commit version bumps to PR branch when approved

2. **Scope required:** Yes, with special scopes for repo-wide changes:
   - `feat(git):` - affects git plugin → bump git
   - `fix(ci-cd-tools):` - affects ci-cd-tools → bump ci-cd-tools
   - `chore(repo):` or `chore:` - repo-wide maintenance → no bump
   - `ci:` - CI changes only → no bump
   - `docs:` - documentation only → no bump

3. **Multiple plugins:** Each plugin scope = separate bump. One commit can only have one scope.

**Valid scopes:**
- Plugin names: `git`, `ci-cd-tools`, `tool-routing`, `dev-tools`, `mcpproxy`, `second-brain`, `stay-on-target`, `working-in-monorepos`
- Repo-wide: `repo`, or no scope for `chore`, `ci`, `docs`, `style`, `test`

## Success Criteria

- [ ] All commits validated against conventional format
- [ ] `hk check` runs without errors
- [ ] PRs blocked if version bump missing
- [ ] Easy to bump: single command updates marketplace.json
- [ ] Clear error messages when things are wrong

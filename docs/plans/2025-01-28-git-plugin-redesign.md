# Git Plugin Redesign

## Overview

Rename `git-workflows` to `git` and restructure skills so qualified names read naturally (e.g., `git:commit`, `git:pull-request`). Add new skills for work inventory and PR review workflow.

## Plugin Structure

```
plugins/git/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── commit/
│   │   └── SKILL.md
│   ├── pull-request/
│   │   ├── SKILL.md
│   │   └── tool-routes.yaml
│   ├── inbox/
│   │   └── SKILL.md
│   ├── checkout/
│   │   └── SKILL.md
│   └── triage/
│       └── SKILL.md
└── README.md
```

## Skills

### `git:commit` (migrated from `writing-git-commits`)

- Staging best practices (specific files, never `git add .`)
- Commit message workflow (draft to scratch/, use `-t` or `-F`)
- Signing handling (1Password failures, user authorization)
- Pre-commit hook handling (auto-fix, no skip without confirmation)

### `git:pull-request` (migrated from `writing-pull-requests`)

- PR creation, updates, comments
- Safety-first: draft to `.scratch/pr-bodies/` before executing
- Manual edit detection, material change checks
- Tool routes for multiline body handling

### `git:inbox` (new)

- Fetch PRs awaiting your review from GitHub
- Show: title, author, age, repo, review status
- Include full PR URL (clickable/copy-pasteable)
- Offer to check out for local review (→ `git:checkout`)

### `git:checkout` (new, absorbs `checkout-pr`)

- Accept: PR URL/number, branch name, ref
- For PRs: fetch branch, create worktree, summarize PR context
- For branches: create worktree or switch
- Worktree naming: `pr-{number}-{desc}` or `{branch-slug}`
- Uses `superpowers:using-git-worktrees` for directory selection

### `git:triage` (new)

Full work inventory with rich context for decision-making.

**Scope:** Full inventory by default, or scoped to: `worktrees`, `stash`, `branches`

**For each worktree:**
- Branch name
- Associated PR (full URL, status, reviews)
- Linked plan file if exists in `docs/plans/`
- Uncommitted/unpushed work summary:
  - Files changed, grouped by area
  - Inferred purpose from diff/commit messages
  - Unpushed commit subjects

**For each stash:**
- Age, description
- Source branch status (exists? merged?)
- What was being worked on

**For each branch:**
- Merged status, remote tracking
- Last commit age
- Related PR (full URL)

**Output format:**
- Full PR URLs for copy-paste
- Summarize uncommitted work with context (e.g., "3 files modified in `src/auth/` - adding Google OAuth provider")
- Note associated plan files

**Actions:**
- Surface actionable recommendations with reasoning
- Never auto-delete - require user confirmation via `AskUserQuestion`
- Options: "Delete these 3 merged worktrees? (A) Yes, all (B) Let me pick (C) Skip"

## Migration

| Current | Action |
|---------|--------|
| `plugins/git-workflows/` | Rename to `plugins/git/`, restructure skills |
| `~/.claude/skills/checkout-pr/` | Absorb into `git:checkout`, remove from personal skills |
| `review-queue` (in code-review) | Functionality moves to `git:inbox` |

**Code-review skill** stays separate (in working-with-pickles / dev-tools) - it's about the review process, not git operations. References `git:checkout` for setup.

**Tool routes** from `writing-pull-requests` migrate to `git:pull-request`.

## Comparison to Anthropic Official Plugins

| Skill | Anthropic Equivalent | Difference |
|-------|---------------------|------------|
| `git:commit` | `/commit` | More workflow: scratch file drafts, signing handling, hook auto-fix |
| `git:pull-request` | `/commit-push-pr` | Focused on PR writing only, not bundled with commit+push |
| `git:inbox` | None | Unique |
| `git:checkout` | None | Unique |
| `git:triage` | `/clean_gone` | Much broader: full inventory with context vs just [gone] branches |

## Dependencies

- `superpowers:using-git-worktrees` - worktree directory selection
- `gh` CLI - GitHub operations (PRs, reviews, repo info)
- Git - local operations (worktrees, stash, branches, diff)

## Announcement Pattern

Each skill announces when invoked:
- "Using git:triage to inventory your work in progress..."
- "Using git:checkout to set up a worktree for PR #1234..."

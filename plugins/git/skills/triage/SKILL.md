---
name: triage
description: Use when reviewing git state across worktrees, stashes, and branches - helps decide what to clean up, resume, or address
---

# Git Triage

## Overview

Full inventory of your git work state with rich context for decision-making. Shows worktrees, stashes, branches, and uncommitted work with enough detail to decide what to clean up, resume, or address.

**Announce:** "Using git:triage to inventory your work in progress..."

## When to Use

- Starting your day - "what was I working on?"
- User asks about git state, worktrees, stashes
- User wants to clean up old work
- User says "triage", "inventory", "what's in progress?"

## Scope

Full inventory by default. User can scope to:
- `worktrees` - just worktrees
- `stash` - just stashes
- `branches` - just local branches

## Workflow

### 1. Gather State

```bash
# Worktrees
git worktree list --porcelain

# Stashes
git stash list

# Local branches with tracking info
git branch -vv

# Current status
git status --porcelain
```

### 2. Enrich Each Item

#### For Worktrees

For each worktree, gather:

```bash
# Get branch and status
cd {worktree_path}
branch=$(git branch --show-current)
git status --porcelain

# Check for associated PR
gh pr list --head {branch} --json number,title,state,url

# Check for plan file
ls docs/plans/*{branch-keywords}* 2>/dev/null
```

**If uncommitted changes exist:**
- List files changed, grouped by directory
- Summarize what the changes appear to be doing (infer from diff)
- Show unpushed commit subjects

#### For Stashes

```bash
# Get stash details
git stash show stash@{N} --stat

# Check if source branch still exists
git branch --list {branch_from_stash_message}
```

#### For Branches

```bash
# Check if merged to main
git branch --merged main | grep {branch}

# Get associated PR
gh pr list --head {branch} --state all --json number,state,url

# Last commit age
git log -1 --format="%cr" {branch}
```

### 3. Present Inventory

Format with full context:

```markdown
## Git Triage

### Worktrees

#### `.worktrees/feature-oauth` (feature/oauth)
- **PR:** https://github.com/owner/repo/pull/1234 (open, 2 approvals)
- **Plan:** `docs/plans/2025-01-15-oauth-design.md`
- **Uncommitted:** 3 files in `src/auth/`
  - Adding Google OAuth provider configuration
  - `oauth.ts`, `config.ts`, `types.ts` modified
- **Unpushed:** 1 commit - "Add OAuth config scaffolding"
- **Recommendation:** Resume - PR is approved, needs final push

#### `.worktrees/pr-999-fix-typo`
- **PR:** https://github.com/owner/repo/pull/999 (merged)
- **Clean:** No uncommitted changes
- **Recommendation:** Safe to delete - PR merged

---

### Stashes

#### `stash@{0}` - "WIP on feature/auth: debugging session"
- **Age:** 3 weeks
- **Source branch:** feature/auth (exists)
- **Files:** 5 files in `src/auth/`
- **Recommendation:** Review - branch exists, may be superseded

#### `stash@{1}` - "WIP on old-feature: abandoned work"
- **Age:** 2 months
- **Source branch:** old-feature (deleted)
- **Recommendation:** Likely safe to drop - source branch gone

---

### Branches

#### `feature/old-experiment`
- **Last commit:** 6 weeks ago
- **PR:** https://github.com/owner/repo/pull/800 (closed, not merged)
- **Tracking:** origin/feature/old-experiment (gone)
- **Recommendation:** Safe to delete - PR closed, remote deleted

---

## Summary

- **2 worktrees** (1 active, 1 safe to delete)
- **2 stashes** (1 to review, 1 likely droppable)
- **1 branch** safe to delete

Ready to clean up?
```

### 4. Offer Actions

Use AskUserQuestion for cleanup decisions:

```
What would you like to do?
(A) Delete merged worktree `.worktrees/pr-999-fix-typo`
(B) Review stash@{0} contents
(C) Delete stale branch `feature/old-experiment`
(D) Clean up all safe-to-delete items
(E) Nothing right now
```

**Never auto-delete** - always require user confirmation.

For option (D), list exactly what will be deleted and confirm:

```
This will delete:
- Worktree: .worktrees/pr-999-fix-typo
- Branch: feature/old-experiment
- Stash: stash@{1}

Proceed?
(A) Yes, delete all
(B) Let me pick individually
(C) Cancel
```

## Quick Reference

| Item | Key Info | Commands |
|------|----------|----------|
| Worktree | Branch, PR, plan, uncommitted | `git worktree list`, `gh pr list --head` |
| Stash | Age, source branch, files | `git stash list`, `git stash show` |
| Branch | Merged?, PR, tracking, age | `git branch -vv`, `gh pr list --head` |

## Output Guidelines

- **Full PR URLs** - always clickable/copy-pasteable
- **Summarize uncommitted work** - infer purpose from diff, not just file count
- **Include plan references** - link to docs/plans/ if relevant
- **Actionable recommendations** - explain why something is safe/needs attention
- **Never auto-delete** - always confirm destructive actions

## Related

- `git:checkout` - Resume work on a worktree
- `git:inbox` - PRs awaiting your review (inbound work)
- `superpowers:finishing-a-development-branch` - Clean up after completing work

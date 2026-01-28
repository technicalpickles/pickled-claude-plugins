# Git Plugin Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename git-workflows to git and add new skills for work inventory and PR review workflow.

**Architecture:** Rename plugin directory, migrate existing skills with simplified names, add three new skills (inbox, checkout, triage). Each skill is a standalone SKILL.md with optional supporting files.

**Tech Stack:** Claude Code plugin system, YAML frontmatter, gh CLI, git

---

## Task 1: Rename Plugin Directory

**Files:**
- Rename: `plugins/git-workflows/` → `plugins/git/`
- Modify: `plugins/git/.claude-plugin/plugin.json`

**Step 1: Rename the directory**

```bash
cd /Users/josh.nichols/workspace/pickled-claude-plugins/.worktrees/git-plugin-redesign
git mv plugins/git-workflows plugins/git
```

**Step 2: Update plugin.json**

Edit `plugins/git/.claude-plugin/plugin.json`:

```json
{
  "name": "git",
  "version": "2.0.0",
  "description": "Git workflow tools: commits, PRs, review inbox, checkout, and work triage",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT"
}
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: rename git-workflows plugin to git"
```

---

## Task 2: Rename commit skill

**Files:**
- Rename: `plugins/git/skills/writing-git-commits/` → `plugins/git/skills/commit/`
- Modify: `plugins/git/skills/commit/SKILL.md` (update frontmatter)

**Step 1: Rename the directory**

```bash
git mv plugins/git/skills/writing-git-commits plugins/git/skills/commit
```

**Step 2: Update SKILL.md frontmatter**

Change the name in frontmatter from `writing-git-commits` to `commit`. The description should start with "Use when...".

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: rename writing-git-commits to commit"
```

---

## Task 3: Rename pull-request skill

**Files:**
- Rename: `plugins/git/skills/writing-pull-requests/` → `plugins/git/skills/pull-request/`
- Modify: `plugins/git/skills/pull-request/SKILL.md` (update frontmatter)

**Step 1: Rename the directory**

```bash
git mv plugins/git/skills/writing-pull-requests plugins/git/skills/pull-request
```

**Step 2: Update SKILL.md frontmatter**

Change the name in frontmatter from `writing-pull-requests` to `pull-request`. The description should start with "Use when...".

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: rename writing-pull-requests to pull-request"
```

---

## Task 4: Create git:inbox skill

**Files:**
- Create: `plugins/git/skills/inbox/SKILL.md`

**Step 1: Create the skill directory and file**

```bash
mkdir -p plugins/git/skills/inbox
```

**Step 2: Write SKILL.md**

Create `plugins/git/skills/inbox/SKILL.md`:

```markdown
---
name: inbox
description: Use when checking what PRs are waiting for your review, or when starting your day to see what needs attention
---

# Git Inbox

## Overview

Show PRs awaiting your review across repositories. Surfaces what needs your attention with context to prioritize.

**Announce:** "Using git:inbox to check PRs awaiting your review..."

## When to Use

- Starting your day - "what needs my attention?"
- User asks about PRs to review
- User says "inbox", "review queue", "what's waiting on me?"

## Workflow

### 1. Fetch PRs Awaiting Review

```bash
# PRs where you're requested reviewer
gh search prs --review-requested=@me --state=open --json repository,number,title,author,createdAt,url

# PRs where you're assigned
gh search prs --assignee=@me --state=open --json repository,number,title,author,createdAt,url
```

### 2. Enrich with Review Status

For each PR, get review state:

```bash
gh pr view {number} --repo {owner}/{repo} --json reviews,reviewRequests
```

### 3. Present Inbox

Format as actionable list:

```markdown
## PRs Awaiting Your Review

### {repo} #{number}: {title}
- **Author:** @{author}
- **Age:** {days} days
- **URL:** {full_url}
- **Status:** {review_status}

---

{N} PRs need your attention. Check out a PR for local review?
```

**Important:**
- Always show full PR URL (clickable/copy-pasteable)
- Sort by age (oldest first) or priority
- Show review status (no reviews yet, changes requested, approved by others)

### 4. Offer Next Action

Use AskUserQuestion:

```
Which PR would you like to check out for review?
(A) #{number} - {title}
(B) #{number} - {title}
(C) #{number} - {title}
(D) None right now
```

If user picks one → invoke `git:checkout` with the PR.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `gh search prs --review-requested=@me --state=open` | PRs requesting your review |
| `gh pr view {n} --repo {r} --json reviews` | Get review status |

## Related

- `git:checkout` - Check out a PR for local review
- `code-review` - Guide the actual review process (separate skill)
```

**Step 3: Commit**

```bash
git add plugins/git/skills/inbox/
git commit -m "feat: add git:inbox skill for PR review queue"
```

---

## Task 5: Create git:checkout skill

**Files:**
- Create: `plugins/git/skills/checkout/SKILL.md`

**Step 1: Create the skill directory**

```bash
mkdir -p plugins/git/skills/checkout
```

**Step 2: Write SKILL.md**

Create `plugins/git/skills/checkout/SKILL.md`:

```markdown
---
name: checkout
description: Use when checking out a PR, branch, or ref for local work - sets up worktree with context
---

# Git Checkout

## Overview

Check out a PR, branch, or ref into an isolated worktree with relevant context.

**Announce:** "Using git:checkout to set up a worktree for {target}..."

## When to Use

- User wants to review a PR locally
- User wants to work on a specific branch in isolation
- User provides PR URL/number or branch name
- Following `git:inbox` when user picks a PR

## Input Formats

Accept:
- Full PR URL: `https://github.com/{owner}/{repo}/pull/{number}`
- Short PR: `{repo}#{number}` or `#{number}` (infer repo from cwd)
- PR number only: `{number}` (infer owner/repo from git remote)
- Branch name: `feature/auth`, `main`, etc.
- Ref: commit SHA, tag

## Workflow

### For PRs

#### 1. Parse PR Reference

```bash
# Get owner/repo from current directory if needed
gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'
```

#### 2. Fetch PR Details

```bash
gh pr view {number} --json title,body,author,state,baseRefName,headRefName,url,reviews,reviewRequests
```

#### 3. Set Up Worktree

**REQUIRED:** Use `superpowers:using-git-worktrees` skill for directory selection.

```bash
# Fetch the PR branch
git fetch origin {headRefName}

# Create worktree
git worktree add .worktrees/pr-{number}-{short-desc} origin/{headRefName}
```

Naming: `pr-{number}-{2-3-word-description}` (e.g., `pr-1234-add-oauth`)

#### 4. Present Context

```markdown
## PR #{number} Ready for Review

**Title:** {title}
**Author:** @{author}
**Branch:** {headRefName} → {baseRefName}
**URL:** {full_url}

### Summary
{1-3 sentence summary from PR body}

### Files Changed ({count})
{Grouped by directory}

### Review Status
{Existing reviews, requested reviewers}

---

**Worktree ready at:** `{full_path}`
```

### For Branches

#### 1. Create Worktree

```bash
# For existing branch
git worktree add .worktrees/{branch-slug} {branch}

# For new branch
git worktree add .worktrees/{branch-slug} -b {branch}
```

#### 2. Report Ready

```markdown
**Worktree ready at:** `{full_path}`
**Branch:** {branch}
```

## Quick Reference

| Input | Action |
|-------|--------|
| PR URL/number | Fetch PR, create worktree, show PR context |
| Branch name | Create worktree for branch |
| Ref/SHA | Create worktree at that ref |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Creating worktree before fetching PR branch | Always `git fetch` first |
| Generic worktree name | Include PR number AND short description |
| Missing PR context | Always summarize PR and show review status |

## Related

- `superpowers:using-git-worktrees` - Handles directory selection and verification
- `git:inbox` - Discover PRs needing review
- `code-review` - Guide the actual review process
```

**Step 3: Commit**

```bash
git add plugins/git/skills/checkout/
git commit -m "feat: add git:checkout skill for PR/branch worktree setup"
```

---

## Task 6: Create git:triage skill

**Files:**
- Create: `plugins/git/skills/triage/SKILL.md`

**Step 1: Create the skill directory**

```bash
mkdir -p plugins/git/skills/triage
```

**Step 2: Write SKILL.md**

Create `plugins/git/skills/triage/SKILL.md`:

```markdown
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
```

**Step 3: Commit**

```bash
git add plugins/git/skills/triage/
git commit -m "feat: add git:triage skill for work inventory"
```

---

## Task 7: Update README

**Files:**
- Modify: `plugins/git/README.md`

**Step 1: Rewrite README**

Replace `plugins/git/README.md` with updated content reflecting new plugin name and skills.

**Step 2: Commit**

```bash
git add plugins/git/README.md
git commit -m "docs: update README for git plugin redesign"
```

---

## Task 8: Remove old checkout-pr skill

**Files:**
- Delete: `~/.claude/skills/checkout-pr/`

**Step 1: Remove the skill**

```bash
rm -rf ~/.claude/skills/checkout-pr/
```

**Step 2: Verify removed**

```bash
ls ~/.claude/skills/
```

Note: This is outside the repo, no commit needed.

---

## Task 9: Final verification

**Step 1: Verify plugin structure**

```bash
find plugins/git -type f
```

Expected:
```
plugins/git/.claude-plugin/plugin.json
plugins/git/README.md
plugins/git/skills/commit/SKILL.md
plugins/git/skills/pull-request/SKILL.md
plugins/git/skills/pull-request/tool-routes.yaml
plugins/git/skills/inbox/SKILL.md
plugins/git/skills/checkout/SKILL.md
plugins/git/skills/triage/SKILL.md
```

**Step 2: Verify qualified names**

Skill names in frontmatter should be:
- `commit` (qualified: `git:commit`)
- `pull-request` (qualified: `git:pull-request`)
- `inbox` (qualified: `git:inbox`)
- `checkout` (qualified: `git:checkout`)
- `triage` (qualified: `git:triage`)

**Step 3: Final commit if any adjustments**

```bash
git status
# If changes, commit them
```

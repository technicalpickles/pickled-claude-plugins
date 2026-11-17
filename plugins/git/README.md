# git Plugin

Git workflow tools: commits, PRs, review inbox, checkout, and work triage.

## Skills

### git:commit

Best practices for creating git commits, handling pre-commit hooks, and managing commit signing.

**Key guidelines:**
- Always use `git add` with specific files, never `git add .` or `git add -A`
- Write commit messages to `.scratch/` directory first
- Handle pre-commit hook failures with auto-fix when possible
- Respect commit signing configuration

### git:pull-request

Create, update, and comment on GitHub pull requests with focus on material impact, safety, and human reviewability.

**Key principles:**
- Safety first: All PR bodies written to `.scratch/pr-bodies/` before use
- Material impact: Focus on why changes matter, not metrics or file counts
- Smart merge: Detect manual edits, only update when changes are material
- Human-friendly: Concise, warm tone; assume busy reviewer

### git:inbox

Show PRs awaiting your review across repositories.

**Use when:**
- Starting your day - "what needs my attention?"
- Checking your review queue
- Looking for PRs waiting on you

### git:checkout

Check out a PR, branch, or ref into an isolated worktree with relevant context.

**Use when:**
- Reviewing a PR locally
- Working on a branch in isolation
- Following up from `git:inbox`

**Supports:**
- PR URLs, numbers, or short references
- Branch names
- Commit SHAs or tags

### git:triage

Full inventory of git work state with context for decision-making.

**Use when:**
- Starting your day - "what was I working on?"
- Cleaning up old worktrees, stashes, or branches
- Getting an overview of work in progress

**Shows:**
- Worktrees with PR status, uncommitted changes, and plans
- Stashes with age and source branch status
- Branches with merge status and PR links

### git:update

Update your branch with upstream changes, intelligently resolving conflicts.

**Use when:**
- PR has merge conflicts
- Branch is behind main/master
- User says "update", "sync", or "pull in latest"

**Key features:**
- Auto-detects upstream from tracking branch or PR base
- Merges (not rebases) to preserve history
- Analyzes conflicts using git history for context
- Resolves autonomously, presents for approval

### git:git-worktrees

Create and remove worktrees with [worktrunk](https://github.com/max-sixty/worktrunk) (`wt`), and clean them up once their PR merges.

**Use when:**
- Creating a worktree (`wt switch --create`)
- A PR whose branch has a `.claude/worktrees/` checkout has merged
- `wt remove` says "Branch unmerged", or a worktree hits `Operation not permitted` under the sandbox

## Hooks

### Post-merge worktree cleanup

`PostToolUse` on Bash. After a `gh pr merge`, the hook asks `gh pr view` whether the PR is merged. If it is, and the head branch still has a worktree under `.claude/worktrees/`, it tells the agent to remove that worktree now. A queued `--auto` merge, a branch with no worktree, or any other Bash call stays silent, and only `gh pr merge` commands make a network call.

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```bash
/plugin install git@pickled-claude-plugins
```

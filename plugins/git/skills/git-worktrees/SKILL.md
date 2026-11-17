---
name: git-worktrees
description: Use when creating or removing a git worktree with worktrunk (`wt switch --create`, `wt remove`), when a PR whose branch has a worktree under `.claude/worktrees/` has merged, or when `wt` reports "Branch unmerged" or `Operation not permitted`. Covers the create flags, cleanup after merge, and the sandbox and EnterWorktree gotchas.
---

# Git worktrees with worktrunk

`wt` (worktrunk) puts worktrees at `<repo>/.claude/worktrees/<branch>`, the same place `EnterWorktree` uses. Prefer it when it's on `PATH`: it has non-interactive flags and lifecycle hooks (bootstrap on create, teardown on remove) that `EnterWorktree` lacks.

## Create

```bash
wt switch --create <name> --base origin/<default> --yes --no-cd --format=json
```

- Always pass `--base`. Without it `wt` branches from local `main`, and when that is ahead of origin the first push drags unpushed commits into the PR.
- Parse `.path` from the JSON and `cd` there, or pass `-C <path>`. The binary can't change your shell's directory.
- A trailing `git branch --unset-upstream ... has no upstream information` error after the worktree is created is harmless. Check `git worktree list` before retrying.

## Remove after merge

Once a worktree's PR merges, remove it in the same session without asking, and report it as done. Cleanup is not a step to hand back to the user.

```bash
git fetch
wt remove <branch> -y
```

- Fetch first. `wt remove` never fetches, so after a squash-merge stale refs make it report "Branch unmerged" ([worktrunk#3519](https://github.com/max-sixty/worktrunk/issues/3519)).
- It refuses a dirty worktree and keeps an unmerged branch, so nothing uncommitted or unmerged is lost. Don't reach for `-f` or `-D` to get past a refusal. Read what it refused on and report it.
- Keep the worktree only when the user said they're still using it, or it is the root of a live session (a desktop-app worktree session, this one included), since removing that breaks the session. Say which exception applied.
- If the shell's cwd is inside the worktree, `cd` to the main checkout first.
- Nothing cleans up at session end. A worktree you don't remove stays until someone notices.

## Gotchas

- Under the command sandbox, `Operation not permitted` in a worktree is usually the path denylist (`.claude/agents/*`, `.claude/commands/*`, `.mcp.json`, `.git/hooks/*`, rc files), not the worktree location. If `wt switch --create` fails that way, retry `wt switch <name>` (no `--create`) unsandboxed; the branch already exists.
- Fall back to `EnterWorktree` only when `wt` isn't installed or you're outside a git repo. Pass a branch name you'd keep (it prefixes `worktree-`), keep Bash commands simple (its guard rejects `&&`, `$(...)`, multi-line), and check `git log origin/main..main` first, since it branches from `origin/<default>` and drops local-only commits.

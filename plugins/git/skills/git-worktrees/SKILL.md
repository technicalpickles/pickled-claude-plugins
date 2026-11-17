---
name: git-worktrees
description: Use when creating or removing a git worktree (`git worktree add`, `wt switch --create`, `EnterWorktree`), when a PR whose branch has a worktree checked out has merged, or when removing one reports "Branch unmerged" or `Operation not permitted`. Covers branching from the right base, cleanup after merge, and the sandbox gotchas.
---

# Git worktrees

Use whichever worktree tool the user prefers. If none is stated and `wt` (worktrunk) is on `PATH`, lean toward it: it has non-interactive flags and lifecycle hooks the others lack.

## Create

Branch from `origin/<default>`, not local `main`. When local `main` is ahead of origin, the first push drags unpushed commits into the PR.

- `git worktree add -b <branch> <path> origin/<default>`
- wt: `wt switch --create <branch> --base origin/<default> --yes --no-cd --format=json`, then `cd` to `.path`. A trailing "has no upstream information" error after creation is harmless; check `git worktree list` before retrying.
- `EnterWorktree`: it already branches from `origin/<default>`, so check `git log origin/main..main` for local-only commits first. Its guard rejects `&&`, `$(...)` and multi-line commands.

## Remove after merge

Once a worktree's PR merges, remove it in the same session without asking, and report it as done. Cleanup is not a step to hand back to the user.

- Keep it only when the user said they're still using it, or it is the root of a live session (a desktop-app worktree session, this one included), since removing that breaks the session. Say which exception applied.
- `git fetch` first. After a squash-merge, stale refs make removal tools think the branch is unmerged.
- `cd` out of the worktree before removing it.
- Never force. Removal refuses a dirty worktree, and that refusal is the safety net. Read what it refused on and report it instead of passing `-f` or `-D`.

By tool:

- `git worktree remove <path>`, then `git branch -d <branch>` if the branch isn't needed.
- wt: `wt remove <branch> -y`. It keeps an unmerged branch on its own.
- A worktree this session entered with `EnterWorktree`: `ExitWorktree` with the remove action.

## Sandbox

Under the command sandbox, `Operation not permitted` in a worktree is usually the path denylist (`.claude/agents/*`, `.claude/commands/*`, `.mcp.json`, `.git/hooks/*`, rc files), not the worktree location. If creating one fails that way partway through, the branch may already exist; retry without creating it (`wt switch <branch>`, or `git worktree add <path> <branch>`) unsandboxed.

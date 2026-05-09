---
name: push
description: Use when running git push or diagnosing why a push failed. Especially when output mixes SSH transport with hook output (lefthook, husky, pre-commit), errors include "Permission denied (publickey)" or "rejected/non-fast-forward", a pre-push hook fails, or about to debug SSH with `-v`.
---

# Git Push

Preferences for `git push`, especially diagnosing failures.

## Reading push failure output

When `git push` exits non-zero, output mixes three layers:

- SSH/transport (key offered, accepted)
- Hook driver header (lefthook, husky, pre-commit, etc.)
- Hook output (test/lint/coverage walls)

Identify the failed layer before debugging:

- `lefthook` or `hook: pre-push` → pre-push hook failed; transport was fine
- `Permission denied (publickey)` → SSH auth refused
- `! [rejected]` / `non-fast-forward` → push needs rebase

A wall of test or coverage output is NOT an SSH problem. The hook ran tests, the tests failed, the push was blocked.

## pre-push hook failures

Same rules as `pre-commit failures` in the commit skill: analyze the failures, autofix when possible, ask the user when unclear. Do NOT skip with `--no-verify` without explicit confirmation.

## Debugging SSH

Before adding `-v` to debug an SSH issue, check whether `core.sshCommand` is configured:

```
git config --get core.sshCommand
```

If it returns nothing, `GIT_SSH_COMMAND="ssh -v" git push origin <branch>` is fine.

If it returns *anything* (custom IdentityFile, IdentityAgent, deploy-key flags, etc.), DO NOT use `GIT_SSH_COMMAND="ssh -v"`. It REPLACES `core.sshCommand` entirely, dropping every flag. Output will look like the wrong keys are being offered, because they are, but only because you removed the constraint.

Append `-v` to the existing command instead:

```
GIT_SSH_COMMAND="$(git config core.sshCommand) -v" git push origin <branch>
```

## Background push gotcha

If you started a push with `run_in_background` and then ran a foreground retry (e.g., because the first looked stuck), the background push may have already succeeded. Before re-investigating "why is push failing":

1. `git -C <worktree> log --oneline origin/<branch>..HEAD`. Empty output means the push went through.
2. Verify retry's cwd: `pwd` and `git rev-parse --show-toplevel`.
3. `gh pr view <pr>` to see if the commit landed.

Don't escalate to "SSH might be broken" before confirming the push didn't already complete.

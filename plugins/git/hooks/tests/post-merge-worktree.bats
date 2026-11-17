#!/usr/bin/env bats
# Tests for the post-merge worktree hook. gh is stubbed on PATH; git runs for real
# against a throwaway repo with worktrees in and out of `.claude/worktrees/`.

HOOK="$BATS_TEST_DIRNAME/../post-merge-worktree.sh"

setup() {
  REPO="$BATS_TEST_TMPDIR/repo"
  BIN="$BATS_TEST_TMPDIR/bin"
  export GH_CALLS="$BATS_TEST_TMPDIR/gh-calls"
  mkdir -p "$REPO" "$BIN"
  git -C "$REPO" init -q -b main
  git -C "$REPO" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m init
  git -C "$REPO" worktree add -q -b feat "$REPO/.claude/worktrees/feat"
  git -C "$REPO" worktree add -q -b elsewhere "$BATS_TEST_TMPDIR/elsewhere"

  cat > "$BIN/gh" <<'STUB'
#!/usr/bin/env bash
echo "$*" >> "$GH_CALLS"
printf '{"state":"%s","headRefName":"%s","number":42}\n' "${GH_STATE:-MERGED}" "${GH_BRANCH:-feat}"
STUB
  printf '#!/bin/sh\nexit 0\n' > "$BIN/wt"
  chmod +x "$BIN/gh" "$BIN/wt"
  for tool in jq git awk sed head; do ln -s "$(command -v "$tool")" "$BIN/$tool"; done
  export PATH="$BIN:/usr/bin:/bin"
}

run_hook() { # run_hook <command> [cwd]
  local cwd=${2:-$REPO}
  run bash -c "jq -n --arg c \"\$1\" --arg d \"\$2\" '{tool_name:\"Bash\",cwd:\$d,tool_input:{command:\$c}}' | '$HOOK'" _ "$1" "$cwd"
}

@test "ignores commands that are not gh pr merge" {
  run_hook "gh pr view 42"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  [ ! -e "$GH_CALLS" ]
}

@test "merged PR with a .claude/worktrees checkout gets a remove nudge" {
  run_hook "gh pr merge 42 --squash"
  [ "$status" -eq 0 ]
  context=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
  [[ "$context" == *"PR #42 (feat) is merged"* ]]
  [[ "$context" == *"/.claude/worktrees/feat"* ]]
  [[ "$context" == *'`wt remove feat -y`'* ]]
}

@test "passes the selector and --repo through, and stops at &&" {
  run_hook "gh pr merge 42 --squash -t 'x' -R owner/repo && git pull"
  [ "$(cat "$GH_CALLS")" = "pr view 42 --repo owner/repo --json state,headRefName,number" ]
}

@test "no selector asks gh about the current branch" {
  run_hook "gh pr merge --squash --delete-branch"
  [ "$(cat "$GH_CALLS")" = "pr view --json state,headRefName,number" ]
}

@test "silent when the PR is still open (auto-merge queued)" {
  GH_STATE=OPEN run_hook "gh pr merge 42 --auto --squash"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "silent when the merged branch has no worktree" {
  GH_BRANCH=other run_hook "gh pr merge 42"
  [ -z "$output" ]
}

@test "silent for a worktree outside .claude/worktrees" {
  GH_BRANCH=elsewhere run_hook "gh pr merge 42"
  [ -z "$output" ]
}

@test "works when the session cwd is the worktree itself" {
  run_hook "gh pr merge 42" "$REPO/.claude/worktrees/feat"
  [[ "$output" == *"/.claude/worktrees/feat"* ]]
}

@test "falls back to git worktree remove without wt" {
  rm "$BIN/wt"
  run_hook "gh pr merge 42"
  [[ "$output" == *"git worktree remove "* ]]
}

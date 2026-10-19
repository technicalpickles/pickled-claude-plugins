#!/usr/bin/env bash
# Shared gate for the hk agent hooks (sourced, not run).
#
# Both hooks target hk 2.5 and later, where `hk agent stop-hook` exists. hk has no
# "is this project configured" probe (`hk validate` also fails for unrelated
# reasons), so the gate is: an hk config file at or above the hook's cwd, and an
# hk that runs and knows `agent stop-hook`. The last two matter because the mise
# shim errors in directories with no hk version set, and older hk answers
# `agent stop-hook` with a usage error that exits 2, which Claude Code treats as a
# block. Any miss means the hook stays silent.

HOOK_INPUT=$(cat)

# Project dir: the hook payload's cwd, else CLAUDE_PROJECT_DIR, else PWD.
hk_project_dir() {
  local dir
  dir=$(printf '%s' "$HOOK_INPUT" | jq -r '.cwd // empty' 2>/dev/null)
  printf '%s' "${dir:-${CLAUDE_PROJECT_DIR:-$PWD}}"
}

# Walk up from $1 looking for one of the paths hk reads its config from.
hk_config_present() {
  local dir=$1 file
  while :; do
    for file in hk.local.pkl .config/hk.local.pkl hk.pkl .config/hk.pkl; do
      [ -f "$dir/$file" ] && return 0
    done
    [ "$dir" = "/" ] && return 1
    dir=$(dirname "$dir")
  done
}

# 0 when the project uses hk and this hk is 2.5 or later.
hk_ready() {
  local dir
  dir=$(hk_project_dir)
  [ -d "$dir" ] || return 1
  hk_config_present "$dir" || return 1
  (cd "$dir" && hk --version >/dev/null 2>&1 && hk agent stop-hook --help >/dev/null 2>&1)
}

#!/usr/bin/env bash
# Shared gate for the hk agent hooks (sourced, not run).
#
# Both hooks mirror what `hk agent hooks` / `hk agent instructions` print for
# Claude Code, but only in projects that use hk. hk has no "is this project
# configured" probe (`hk validate` also fails for unrelated reasons), so the
# gate is: an hk.pkl at or above the hook's cwd, and an hk that actually runs.
# The second part matters because the mise shim errors in directories with no
# hk version set. Any miss means the hook stays silent.

HOOK_INPUT=$(cat)

# Project dir: the hook payload's cwd, else CLAUDE_PROJECT_DIR, else PWD.
hk_project_dir() {
  local dir
  dir=$(printf '%s' "$HOOK_INPUT" | jq -r '.cwd // empty' 2>/dev/null)
  printf '%s' "${dir:-${CLAUDE_PROJECT_DIR:-$PWD}}"
}

# Walk up from $1 looking for hk.pkl.
hk_config_present() {
  local dir=$1
  while :; do
    [ -f "$dir/hk.pkl" ] && return 0
    [ "$dir" = "/" ] && return 1
    dir=$(dirname "$dir")
  done
}

# 0 when hk.pkl exists and hk runs from the project dir. `hk agent` shipped in
# hk 1.55 alongside `--safe`; older hk rejects `--safe` outright, which the Stop
# hook would report as a failing check, so those versions count as not ready.
hk_ready() {
  local dir
  dir=$(hk_project_dir)
  [ -d "$dir" ] || return 1
  hk_config_present "$dir" || return 1
  (cd "$dir" && hk --version >/dev/null 2>&1 && hk agent --help >/dev/null 2>&1)
}

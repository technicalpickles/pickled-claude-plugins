#!/usr/bin/env bash
# Shared gate for the hk agent hooks and MCP launcher (sourced, not run).
#
# Everything targets hk 2.5 and later, where `hk agent stop-hook` exists. hk has no
# "is this project configured" probe (`hk validate` also fails for unrelated
# reasons), so the gate is: an hk config file at or above the project dir, and an
# hk that runs and knows `agent stop-hook`. The last two matter because the mise
# shim errors in directories with no hk version set, and older hk answers
# `agent stop-hook` with a usage error that exits 2, which Claude Code treats as a
# block. Any miss means the caller stays silent.
#
# This file reads nothing from stdin: the MCP launcher's stdin is the MCP stream.

# Project dir from a hook payload on $1 (JSON), else CLAUDE_PROJECT_DIR, else PWD.
hk_payload_dir() {
  local dir
  dir=$(printf '%s' "$1" | jq -r '.cwd // empty' 2>/dev/null)
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

# 0 when the project at $1 uses hk and this hk is 2.5 or later.
hk_ready() {
  local dir=$1
  [ -d "$dir" ] || return 1
  hk_config_present "$dir" || return 1
  (cd "$dir" && hk --version >/dev/null 2>&1 && hk agent stop-hook --help >/dev/null 2>&1)
}

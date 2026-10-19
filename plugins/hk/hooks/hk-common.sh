# Shared gate for the hk agent hooks and MCP launcher (sourced, not run).
#
# Everything targets hk 2.6 and later. 2.5 added `hk agent stop-hook` and 2.6 made it
# pass quietly in a project whose config has no `check` hook (2.5.x blocks there).
# Older hk answers `agent stop-hook` with a usage error that exits 2, which Claude
# Code treats as a block. hk has no "is this project configured" probe (`hk validate`
# also fails for unrelated reasons), so the gate is: an hk config file at or above
# the project dir, and an hk that runs and reports version 2.6 or later. `hk
# --version` failing covers the mise shim, which errors in directories with no hk
# version set. Any miss means the sourcing script stays silent.
#
# One gate covers all three scripts on purpose. `hk agent instructions` and `hk mcp`
# exist since hk 1.55, but the plugin is built around the Stop hook, and a project on
# an older hk would otherwise get instructions and an MCP server with no Stop hook
# behind them. Probing hk once is simpler than three capability checks. The config
# walk goes up to `/`, same as hk's own discovery, and checks only that a file
# exists: a broken hk.pkl still counts as present.
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

# 0 when hk, run from $1, reports version 2.6 or later.
hk_version_ok() {
  local major minor
  set -- $(cd "$1" && hk --version 2>/dev/null | sed -n '1s/^hk \([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\1 \2/p')
  major=${1:-} minor=${2:-}
  [ -n "$major" ] && [ -n "$minor" ] || return 1
  [ "$major" -gt 2 ] || { [ "$major" -eq 2 ] && [ "$minor" -ge 6 ]; }
}

# 0 when the project at $1 uses hk and this hk is 2.6 or later.
hk_ready() {
  local dir=$1
  [ -d "$dir" ] || return 1
  hk_config_present "$dir" || return 1
  hk_version_ok "$dir"
}

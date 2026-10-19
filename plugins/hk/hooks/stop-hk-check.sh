#!/usr/bin/env bash
# Stop: run `hk run check --safe --format json`, exactly what
# `hk agent hooks --target claude-code` prints, only in projects that use hk.
#
# hk 2.0.0 exits 1 on a failing check, and Claude Code treats exit 1 from a hook
# as non-blocking. Exit 2 is what blocks Stop and feeds stderr back to Claude, so
# this wrapper maps any failure to 2. It also bows out when stop_hook_active is
# set, otherwise a check Claude can't fix would keep it from ever stopping.

# shellcheck source=hk-common.sh
. "$(dirname "${BASH_SOURCE[0]}")/hk-common.sh"

if printf '%s' "$HOOK_INPUT" | jq -e '.stop_hook_active // false' >/dev/null 2>&1; then
  exit 0
fi

hk_ready || exit 0

output=$(cd "$(hk_project_dir)" && hk run check --safe --format json 2>&1)
status=$?
[ "$status" -eq 0 ] && exit 0

# An hk.pkl with no `check` hook also exits 1, which isn't a failing check.
case "$output" in
  *"Hook 'check' not found"*) exit 0 ;;
esac

printf '%s\n' "$output" >&2
exit 2

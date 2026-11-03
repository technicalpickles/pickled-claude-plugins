#!/usr/bin/env bash
# Print the name of the vault a note for the current session should go to, or
# nothing when sb's default vault is the right one.
#
# Order:
#   1. SB_NOTE_VAULT, when set (a per-project override, e.g. in .claude/settings.json "env").
#   2. The registered vault whose path contains the working directory.
#   3. Nothing: the caller omits --vault and sb uses its default.
#
# Rule 2 matters because a session working inside a vault is about that vault, so its
# notes belong there regardless of which vault is the default.
#
# Usage: resolve-vault.sh [dir]       (vault list from `sb config vaults`)
#        SB_VAULTS_JSON='[{"name":..,"path":..}]' resolve-vault.sh [dir]   (tests)

set -euo pipefail

if [ -n "${SB_NOTE_VAULT:-}" ]; then
  printf '%s\n' "$SB_NOTE_VAULT"
  exit 0
fi

dir=$(cd "${1:-$PWD}" 2>/dev/null && pwd -P) || exit 0

vaults_json="${SB_VAULTS_JSON:-}"
if [ -z "$vaults_json" ]; then
  vaults_json=$(npx @techpickles/sb config vaults 2>/dev/null) || exit 0
fi

best_name=""
best_len=0
while IFS=$'\t' read -r name path; do
  [ -n "$path" ] || continue
  real=$(cd "$path" 2>/dev/null && pwd -P) || continue
  case "$dir/" in
    "$real"/*)
      if [ "${#real}" -gt "$best_len" ]; then
        best_name=$name
        best_len=${#real}
      fi
      ;;
  esac
done < <(printf '%s' "$vaults_json" | jq -r '.[] | [.name, .path] | @tsv')

[ -n "$best_name" ] && printf '%s\n' "$best_name"
exit 0

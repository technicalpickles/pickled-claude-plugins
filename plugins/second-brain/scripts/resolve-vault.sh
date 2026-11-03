#!/usr/bin/env bash
# Print the vault a session's note belongs in, or nothing when sb's default applies.
# SB_NOTE_VAULT wins; else the registered vault containing the directory. A session working
# inside a vault writes there, because a vault can have rules about what may be stored in it.
# SB_VAULTS_JSON replaces `sb config vaults` (tests).

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

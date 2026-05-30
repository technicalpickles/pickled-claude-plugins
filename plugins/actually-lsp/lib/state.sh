#!/usr/bin/env bash
# lib/state.sh: project state file read/write for actually-lsp
# Sourced by hooks. Requires $PROJECT_DIR env var.

_state_file() {
  echo "$PROJECT_DIR/.claude/actually-lsp.json"
}

# read_state <ecosystem> <field>
#   Print the field value, or empty if missing.
read_state() {
  local ecosystem="$1"
  local field="$2"
  local file
  file=$(_state_file)

  if [[ ! -f "$file" ]]; then
    return 0
  fi
  jq -r --arg eco "$ecosystem" --arg f "$field" \
    '.ecosystems[$eco][$f] // empty' "$file" 2>/dev/null || true
}

# write_state <ecosystem> <state> <dismissed> <last_check_at> <last_marker_mtime> <last_plugin_list_hash> <last_error> [readiness_source]
#   Atomic: write to temp file, then rename.
#   readiness_source records how the `ready`/`server-not-runnable` verdict was
#   reached: "probe" (real documentSymbol), "heuristic" (shell env_check
#   fallback), "binary" (server binary missing), or "" (earlier short-circuit).
write_state() {
  local ecosystem="$1"
  local state="$2"
  local dismissed="$3"
  local last_check_at="$4"
  local last_marker_mtime="$5"
  local last_plugin_list_hash="$6"
  local last_error="$7"
  local readiness_source="${8:-}"

  local file
  file=$(_state_file)
  local dir
  dir=$(dirname "$file")
  mkdir -p "$dir"

  local existing="{}"
  if [[ -f "$file" ]]; then
    existing=$(cat "$file")
  fi

  local tmpfile="$file.tmp.$$"
  echo "$existing" | jq \
    --arg eco "$ecosystem" \
    --arg state "$state" \
    --argjson dismissed "$dismissed" \
    --arg last_check_at "$last_check_at" \
    --argjson last_marker_mtime "$last_marker_mtime" \
    --arg last_plugin_list_hash "$last_plugin_list_hash" \
    --argjson last_error "$last_error" \
    --arg readiness_source "$readiness_source" \
    '
      .version = 1 |
      .ecosystems //= {} |
      .ecosystems[$eco] = {
        state: $state,
        dismissed: $dismissed,
        last_check_at: $last_check_at,
        last_marker_mtime: $last_marker_mtime,
        last_plugin_list_hash: $last_plugin_list_hash,
        last_error: $last_error,
        readiness_source: $readiness_source
      }
    ' > "$tmpfile"
  mv "$tmpfile" "$file"
}

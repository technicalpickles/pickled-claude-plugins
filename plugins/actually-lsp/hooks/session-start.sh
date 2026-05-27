#!/usr/bin/env bash
# hooks/session-start.sh: SessionStart hook for actually-lsp
#
# Detects ecosystems in $CLAUDE_PROJECT_DIR, computes LSP state per ecosystem,
# emits nudges or activation context via additionalContext (stdout).

set -eo pipefail

# Consume stdin (hook receives JSON we don't use)
cat > /dev/null

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=../lib/ecosystems.sh
source "$PLUGIN_ROOT/lib/ecosystems.sh"
# shellcheck source=../lib/detect.sh
source "$PLUGIN_ROOT/lib/detect.sh"
# shellcheck source=../lib/state.sh
source "$PLUGIN_ROOT/lib/state.sh"

# get_plugin_list: call `claude plugin list --json` with 5s timeout, fallback to []
get_plugin_list() {
  timeout 5s claude plugin list --json 2>/dev/null || echo "[]"
}

# is_plugin_enabled <plugin_id>
is_plugin_enabled() {
  local plugin_id="$1"
  local plugin_list
  plugin_list=$(get_plugin_list)
  echo "$plugin_list" | jq -e --arg id "$plugin_id" \
    '.[] | select(.enabled and .id == $id)' >/dev/null 2>&1
}

# compute_state <ecosystem> <marker_path> <recommended_plugin> <server_binary> <env_check>
compute_state() {
  local ecosystem="$1" marker_path="$2" recommended_plugin="$3" server_binary="$4" env_check="$5"

  # 1. dismissed flag
  if [[ "$(read_state "$ecosystem" "dismissed")" == "true" ]]; then
    echo "dismissed"
    return
  fi

  # 2. LSP plugin enabled?
  if ! is_plugin_enabled "$recommended_plugin"; then
    echo "no-lsp-plugin"
    return
  fi

  # 3. server binary on PATH? (test override available)
  if [[ "${ACTUALLY_LSP_SKIP_BINARY_CHECK:-0}" != "1" ]]; then
    if ! command -v "$server_binary" >/dev/null 2>&1; then
      echo "server-not-runnable"
      return
    fi
  fi

  # 4. env_check passes?
  if ! (cd "$PROJECT_DIR" && eval "$env_check") >/dev/null 2>&1; then
    echo "server-not-runnable"
    return
  fi

  echo "ready"
}

# emit_for_state <ecosystem> <state> <recommended_plugin>
emit_for_state() {
  local ecosystem="$1" state="$2" recommended_plugin="$3"

  case "$state" in
    dismissed|not-detected)
      ;;
    no-lsp-plugin)
      echo "[actually-lsp] Detected $ecosystem. Recommended LSP plugin: $recommended_plugin."
      echo "Run \`/actually-lsp-doctor\` to set up, or \`/actually-lsp-ignore $ecosystem\` to ignore."
      ;;
    server-not-runnable)
      echo "[actually-lsp] $ecosystem LSP plugin installed but env not ready (server binary missing or env check failed)."
      echo "Run \`/actually-lsp-doctor $ecosystem\` to fix."
      ;;
    ready)
      cat "$PLUGIN_ROOT/activation/$ecosystem.md"
      ;;
    error)
      echo "[actually-lsp] Detection failed for $ecosystem."
      echo "Run \`/actually-lsp-doctor $ecosystem\` for details."
      ;;
  esac
}

# Main loop
detected=$(detect_ecosystems "$PROJECT_DIR")
if [[ -z "$detected" ]]; then
  exit 0
fi

while IFS='|' read -r ecosystem marker_path; do
  # Find the matching ecosystem row to get recommended_plugin, server_binary, env_check
  for row in "${ecosystems[@]}"; do
    IFS='|' read -r e_name e_marker e_plugin e_server e_envcheck <<< "$row"
    if [[ "$e_name" == "$ecosystem" ]]; then
      state=$(compute_state "$ecosystem" "$marker_path" "$e_plugin" "$e_server" "$e_envcheck")
      emit_for_state "$ecosystem" "$state" "$e_plugin"
      # Persist state
      now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
      mtime=$(stat -c %Y "$marker_path" 2>/dev/null || stat -f %m "$marker_path" 2>/dev/null || echo 0)
      # Slice in bash rather than `| head -c 8`: piping into a truncating
      # reader is the same antipattern that broke detect.sh under pipefail.
      # sha256sum's output is small enough that it's safe in practice today,
      # but there's no reason to keep the fragile shape.
      plugin_hash=$(get_plugin_list | sha256sum)
      plugin_hash="${plugin_hash:0:8}"
      write_state "$ecosystem" "$state" false "$now" "$mtime" "$plugin_hash" null
      break
    fi
  done
done <<< "$detected"

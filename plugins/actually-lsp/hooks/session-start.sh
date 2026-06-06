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

# _verdict <state> <readiness_source>: emit the compute_state result as a single
# tab-separated line. compute_state runs inside a command substitution (subshell),
# so the readiness source can't ride out on a global; it travels on stdout.
_verdict() { printf '%s\t%s\n' "$1" "$2"; }

# compute_state <ecosystem> <marker_path> <recommended_plugin> <server_binary> <env_check>
#   Prints "<state>\t<readiness_source>". Caller splits on tab.
compute_state() {
  local ecosystem="$1" marker_path="$2" recommended_plugin="$3" server_binary="$4" env_check="$5"

  # 1. dismissed flag
  if [[ "$(read_state "$ecosystem" "dismissed")" == "true" ]]; then
    _verdict "dismissed" ""
    return
  fi

  # 2. LSP plugin enabled?
  if ! is_plugin_enabled "$recommended_plugin"; then
    _verdict "no-lsp-plugin" ""
    return
  fi

  # 3. server binary on PATH? (test override available)
  if [[ "${ACTUALLY_LSP_SKIP_BINARY_CHECK:-0}" != "1" ]]; then
    if ! command -v "$server_binary" >/dev/null 2>&1; then
      _verdict "server-not-runnable" "binary"
      return
    fi
  fi

  # 4. capability probe: ground readiness in a real documentSymbol response
  #    instead of a shell heuristic. The probe is correct across ecosystems
  #    where the per-ecosystem shell env_checks each mispredict differently
  #    (gt-5ugv). Exit codes from lib/probe-server.mjs:
  #      0 -> server navigates (ready, source=probe)
  #      1 -> server answered but can't navigate (server-not-runnable, source=probe)
  #      2/124/other -> couldn't probe (no node, no sample, timeout) -> fall back
  #    Probe disabled by ACTUALLY_LSP_SKIP_PROBE=1 (falls straight to env_check).
  if [[ "${ACTUALLY_LSP_SKIP_PROBE:-0}" != "1" ]]; then
    local pinputs langid sample probe_args probe_rc
    pinputs=$(probe_inputs "$ecosystem")
    if [[ -n "$pinputs" ]] && command -v node >/dev/null 2>&1; then
      IFS=$'\t' read -r langid sample probe_args <<< "$pinputs"
      # probe_args is unquoted on purpose: empty -> no extra args, "--no-stdio" -> one flag
      # shellcheck disable=SC2086
      timeout 5s node "$PLUGIN_ROOT/lib/probe-server.mjs" \
        --server "$server_binary" --root "$PROJECT_DIR" --sample "$sample" --langid "$langid" $probe_args \
        >/dev/null 2>&1
      probe_rc=$?
      case "$probe_rc" in
        0) _verdict "ready" "probe"; return ;;
        1) _verdict "server-not-runnable" "probe"; return ;;
        *) : ;;  # couldn't probe -> fall through to the env_check heuristic
      esac
    fi
  fi

  # 4b. fallback heuristic: shell env_check (used only when the probe can't run)
  if (cd "$PROJECT_DIR" && eval "$env_check") >/dev/null 2>&1; then
    _verdict "ready" "heuristic"
    return
  fi
  _verdict "server-not-runnable" "heuristic"
}

# probe_inputs <ecosystem>: print "<langid>\t<sample_file>\t<probe_args>" for the
# probe, or nothing if no sample source file is found. probe_args is extra flags
# for lib/probe-server.mjs: empty for tsserver/ruby-lsp (which take the default
# --stdio), "--no-stdio" for rust-analyzer (which is the server with no args and
# rejects --stdio). TS is the wired+validated ecosystem; ruby and rust are mapped
# and unblocked here but get their own validation before shipping.
probe_inputs() {
  local ecosystem="$1" langid sample probe_args=""
  case "$ecosystem" in
    typescript)
      langid="typescript"
      sample=$(find "$PROJECT_DIR" -maxdepth 4 -type f \( -name '*.ts' -o -name '*.tsx' \) -print -quit 2>/dev/null)
      ;;
    ruby)
      langid="ruby"
      sample=$(find "$PROJECT_DIR" -maxdepth 4 -type f -name '*.rb' -print -quit 2>/dev/null)
      ;;
    rust)
      langid="rust"
      sample=$(find "$PROJECT_DIR" -maxdepth 4 -type f -name '*.rs' -print -quit 2>/dev/null)
      probe_args="--no-stdio"
      ;;
    *)
      return 0
      ;;
  esac
  [[ -n "$sample" ]] && printf '%s\t%s\t%s' "$langid" "$sample" "$probe_args"
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
      IFS=$'\t' read -r state readiness_source < <(compute_state "$ecosystem" "$marker_path" "$e_plugin" "$e_server" "$e_envcheck")
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
      write_state "$ecosystem" "$state" false "$now" "$mtime" "$plugin_hash" null "$readiness_source"
      break
    fi
  done
done <<< "$detected"

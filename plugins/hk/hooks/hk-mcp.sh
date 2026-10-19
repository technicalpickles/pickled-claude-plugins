#!/usr/bin/env bash
# MCP launcher for the plugin's `hk` server. $1 is the project root.
#
# A plugin MCP server starts in every project where the plugin is enabled and
# can't be made conditional, and a command that fails shows up as a failed server.
# So in a project that doesn't use hk (or has an hk older than 2.5) this serves an
# inert MCP session with no tools instead, and in one that does it becomes the real
# `hk mcp --root <project>`.

# shellcheck source=hk-common.sh
. "$(dirname "${BASH_SOURCE[0]}")/hk-common.sh"

root=${1:-${CLAUDE_PROJECT_DIR:-$PWD}}

if hk_ready "$root"; then
  cd "$root" || exit 1
  exec hk mcp --root "$root"
fi

# Newline-delimited JSON-RPC: answer the handshake and ping, advertise nothing.
while IFS= read -r line; do
  id=$(printf '%s' "$line" | jq -c '.id // empty' 2>/dev/null)
  [ -n "$id" ] || continue # notifications get no reply
  case $(printf '%s' "$line" | jq -r '.method // empty' 2>/dev/null) in
    initialize)
      printf '%s' "$line" | jq -c '{jsonrpc: "2.0", id: .id, result: {
        protocolVersion: (.params.protocolVersion // "2025-06-18"),
        capabilities: {},
        serverInfo: {name: "hk", version: "inactive"},
        instructions: "No hk 2.5+ project here, so this server offers no tools."}}' ;;
    ping)
      printf '{"jsonrpc":"2.0","id":%s,"result":{}}\n' "$id" ;;
    *)
      printf '{"jsonrpc":"2.0","id":%s,"error":{"code":-32601,"message":"Method not found"}}\n' "$id" ;;
  esac
done

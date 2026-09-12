#!/usr/bin/env bash
# Resolve the tailnet URL for something running on a local port.
#
# Usage: resolve-tailnet-url.sh <port> [path]
#
# Prints a URL on stdout (http://<tailnet-hostname>:<port>/<path>, falling
# back to the node's first Tailscale IP if the DNS name isn't usable) and
# exits 0. If Tailscale isn't installed or isn't connected, prints nothing
# to stdout, an explanation to stderr, and exits 1 -- callers should fall
# back to a plain localhost URL in that case rather than guessing.
set -euo pipefail

port="${1:-}"
path="${2:-}"

if [[ -z "$port" ]]; then
  echo "usage: $(basename "$0") <port> [path]" >&2
  exit 2
fi

find_tailscale_binary() {
  if command -v tailscale >/dev/null 2>&1; then
    command -v tailscale
    return 0
  fi
  # macOS GUI app (Tailscale.app) does not symlink onto $PATH by default.
  local gui_binary="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
  if [[ -x "$gui_binary" ]]; then
    echo "$gui_binary"
    return 0
  fi
  return 1
}

if ! ts_bin="$(find_tailscale_binary)"; then
  echo "tailscale binary not found (checked \$PATH and /Applications/Tailscale.app)" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to parse 'tailscale status --json' but isn't on \$PATH" >&2
  exit 1
fi

status_json="$("$ts_bin" status --json 2>/dev/null)" || {
  echo "'$ts_bin status --json' failed -- is tailscaled running?" >&2
  exit 1
}

backend_state="$(jq -r '.BackendState // "Unknown"' <<<"$status_json")"
if [[ "$backend_state" != "Running" ]]; then
  echo "tailscale is not connected (BackendState=$backend_state)" >&2
  exit 1
fi

# Self.DNSName carries a trailing dot (e.g. "host.tailnet.ts.net."); strip it.
dns_name="$(jq -r '.Self.DNSName // ""' <<<"$status_json" | sed 's/\.$//')"
fallback_ip="$(jq -r '.Self.TailscaleIPs[0] // ""' <<<"$status_json")"

host=""
if [[ -n "$dns_name" ]]; then
  host="$dns_name"
elif [[ -n "$fallback_ip" ]]; then
  host="$fallback_ip"
else
  echo "could not determine this node's tailnet hostname or IP from 'tailscale status --json'" >&2
  exit 1
fi

url="http://${host}:${port}/"
if [[ -n "$path" ]]; then
  url="${url}${path#/}"
fi

echo "$url"

#!/usr/bin/env bash
# Usage: check-overlays.sh [PSTACK_PLUGIN_DIR]
#   PSTACK_PLUGIN_DIR holds skills/poteto-mode/. Defaults to the newest
#   installed pstack-claude version in the Claude config dir.
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"

pstack="${1:-}"
if [ -z "$pstack" ]; then
  config_dirs="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  old_ifs="$IFS"
  IFS=':,'
  for dir in $config_dirs; do
    cache="$dir/plugins/cache/pstack-claude/pstack"
    if [ -d "$cache" ]; then
      newest="$(ls "$cache" | sort -V | tail -n 1)"
      if [ -n "$newest" ]; then
        pstack="$cache/$newest"
        break
      fi
    fi
  done
  IFS="$old_ifs"
fi

checker="$pstack/skills/poteto-mode/scripts/check-playbooks.mjs"
if [ -z "$pstack" ] || [ ! -f "$checker" ]; then
  echo "check-overlays: no pstack checker found (pass the pstack plugin dir as the first argument)" >&2
  exit 2
fi

echo "Checking $here/.agents/playbooks against $pstack"
node "$checker" "$here"

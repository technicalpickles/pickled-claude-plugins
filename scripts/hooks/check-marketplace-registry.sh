#!/usr/bin/env bash
set -euo pipefail

# Get repo root
REPO_ROOT="$(git rev-parse --show-toplevel)"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"

# Check if marketplace.json exists
if [[ ! -f "$MARKETPLACE_JSON" ]]; then
    echo "ERROR: marketplace.json not found at $MARKETPLACE_JSON"
    exit 1
fi

# Get registered plugin names from marketplace.json
registered_plugins=$(jq -r '.plugins[].name' "$MARKETPLACE_JSON" 2>/dev/null || echo "")

# Find all plugin directories that have a .claude-plugin/plugin.json
unregistered=()
for plugin_dir in "$REPO_ROOT"/plugins/*/; do
    plugin_name=$(basename "$plugin_dir")
    plugin_json="$plugin_dir/.claude-plugin/plugin.json"

    # Skip if no plugin.json (not a real plugin)
    [[ -f "$plugin_json" ]] || continue

    # Check if registered
    if ! echo "$registered_plugins" | grep -qx "$plugin_name"; then
        unregistered+=("$plugin_name")
    fi
done

# Report unregistered plugins
if [[ ${#unregistered[@]} -gt 0 ]]; then
    echo "ERROR: Unregistered plugins detected"
    echo ""
    echo "The following plugins are not in .claude-plugin/marketplace.json:"
    for plugin in "${unregistered[@]}"; do
        echo "  - $plugin"
    done
    echo ""
    echo "Add them to marketplace.json before committing:"
    for plugin in "${unregistered[@]}"; do
        echo "  \"$plugin\": { \"source\": \"./plugins/$plugin\" }"
    done
    exit 1
fi

exit 0

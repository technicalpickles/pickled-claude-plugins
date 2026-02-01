#!/usr/bin/env bash
#
# Validates plugin versioning consistency for the marketplace.
#
# Rules:
# 1. plugin.json files must NOT contain "version" field (marketplace.json is source of truth)
# 2. All plugins in marketplace.json must have a corresponding plugin.json
# 3. All plugin directories must have a plugin.json file
# 4. All plugins with plugin.json must be registered in marketplace.json
#
# Usage:
#   ./scripts/validate-plugin-versions.sh
#
# Can also be used as a pre-commit hook:
#   ln -sf ../../scripts/validate-plugin-versions.sh .git/hooks/pre-commit
#

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"
PLUGINS_DIR="$REPO_ROOT/plugins"

errors=0

echo "Validating plugin versioning..."
echo

# Check 1: No plugin.json should have a "version" field
echo "Checking plugin.json files for version field..."
while IFS= read -r -d '' plugin_json; do
    # Skip worktrees
    if [[ "$plugin_json" == *".worktrees"* ]]; then
        continue
    fi

    if jq -e 'has("version")' "$plugin_json" > /dev/null 2>&1; then
        echo "  ERROR: $plugin_json contains 'version' field"
        echo "         Version should only be in marketplace.json"
        errors=$((errors + 1))
    fi
done < <(find "$PLUGINS_DIR" -name "plugin.json" -print0 2>/dev/null)

if [[ $errors -eq 0 ]]; then
    echo "  OK: No plugin.json files contain version field"
fi
echo

# Check 2: All plugins in marketplace.json have corresponding plugin.json
echo "Checking marketplace.json plugins have plugin.json files..."
if [[ -f "$MARKETPLACE_JSON" ]]; then
    marketplace_plugins=$(jq -r '.plugins[].name' "$MARKETPLACE_JSON" 2>/dev/null || echo "")
    for plugin in $marketplace_plugins; do
        plugin_json_path="$PLUGINS_DIR/$plugin/.claude-plugin/plugin.json"
        if [[ ! -f "$plugin_json_path" ]]; then
            echo "  ERROR: Plugin '$plugin' in marketplace.json but no plugin.json at:"
            echo "         $plugin_json_path"
            errors=$((errors + 1))
        fi
    done

    if [[ $errors -eq 0 ]]; then
        echo "  OK: All marketplace plugins have plugin.json files"
    fi
else
    echo "  WARNING: marketplace.json not found at $MARKETPLACE_JSON"
fi
echo

# Check 3: All plugin directories have plugin.json
echo "Checking all plugin directories have plugin.json..."
for plugin_dir in "$PLUGINS_DIR"/*/; do
    plugin_name=$(basename "$plugin_dir")
    plugin_json_path="$plugin_dir.claude-plugin/plugin.json"

    if [[ ! -f "$plugin_json_path" ]]; then
        echo "  WARNING: Plugin directory '$plugin_name' missing plugin.json"
        echo "           Expected: $plugin_json_path"
        # Not an error, just a warning - plugin might be work-in-progress
    fi
done
echo

# Check 4: All plugin directories with plugin.json are registered in marketplace.json
echo "Checking all plugins are registered in marketplace.json..."
if [[ -f "$MARKETPLACE_JSON" ]]; then
    marketplace_plugins=$(jq -r '.plugins[].name' "$MARKETPLACE_JSON" 2>/dev/null || echo "")

    for plugin_dir in "$PLUGINS_DIR"/*/; do
        plugin_name=$(basename "$plugin_dir")
        plugin_json_path="$plugin_dir.claude-plugin/plugin.json"

        # Only check plugins that have a plugin.json (i.e., are complete)
        if [[ -f "$plugin_json_path" ]]; then
            if ! echo "$marketplace_plugins" | grep -q "^${plugin_name}$"; then
                echo "  ERROR: Plugin '$plugin_name' has plugin.json but is not in marketplace.json"
                echo "         Add entry to .claude-plugin/marketplace.json:"
                echo "         {"
                echo "           \"name\": \"$plugin_name\","
                echo "           \"source\": \"./plugins/$plugin_name\","
                echo "           \"version\": \"1.0.0\""
                echo "         }"
                errors=$((errors + 1))
            fi
        fi
    done

    if [[ $errors -eq 0 ]]; then
        echo "  OK: All plugins are registered in marketplace.json"
    fi
else
    echo "  WARNING: marketplace.json not found at $MARKETPLACE_JSON"
fi
echo

# Summary
if [[ $errors -gt 0 ]]; then
    echo "FAILED: $errors error(s) found"
    exit 1
else
    echo "PASSED: All validations passed"
    exit 0
fi

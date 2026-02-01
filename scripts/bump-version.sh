#!/usr/bin/env bash
#
# Bumps the version of a plugin in marketplace.json.
#
# Usage:
#   ./scripts/bump-version.sh <plugin> <major|minor|patch>
#   ./scripts/bump-version.sh git minor
#   ./scripts/bump-version.sh ci-cd-tools patch
#
# Can also auto-detect bump type from commits:
#   ./scripts/bump-version.sh --auto
#

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <plugin> <major|minor|patch>"
    echo "       $0 --auto"
    echo ""
    echo "Arguments:"
    echo "  plugin    Plugin name (e.g., git, ci-cd-tools)"
    echo "  bump      Bump type: major, minor, or patch"
    echo ""
    echo "Options:"
    echo "  --auto    Auto-detect and apply all needed bumps from commits"
    echo "  --dry-run Show what would be changed without modifying files"
    echo ""
    echo "Examples:"
    echo "  $0 git minor       # Bump git from 2.2.0 to 2.3.0"
    echo "  $0 git patch       # Bump git from 2.2.0 to 2.2.1"
    echo "  $0 --auto          # Bump all plugins based on commits"
}

# Get current version of a plugin
get_plugin_version() {
    local plugin="$1"
    jq -r --arg name "$plugin" '.plugins[] | select(.name == $name) | .version' "$MARKETPLACE_JSON" 2>/dev/null
}

# Check if plugin exists in marketplace
plugin_exists() {
    local plugin="$1"
    jq -e --arg name "$plugin" '.plugins[] | select(.name == $name)' "$MARKETPLACE_JSON" > /dev/null 2>&1
}

# Bump a semver version
bump_version() {
    local version="$1"
    local bump_type="$2"

    IFS='.' read -r major minor patch <<< "$version"

    case "$bump_type" in
        major)
            echo "$((major + 1)).0.0"
            ;;
        minor)
            echo "$major.$((minor + 1)).0"
            ;;
        patch)
            echo "$major.$minor.$((patch + 1))"
            ;;
        *)
            echo "ERROR: Invalid bump type: $bump_type" >&2
            exit 1
            ;;
    esac
}

# Update version in marketplace.json
update_version() {
    local plugin="$1"
    local new_version="$2"

    # Use jq to update the version
    local tmp_file
    tmp_file=$(mktemp)

    jq --arg name "$plugin" --arg version "$new_version" \
        '(.plugins[] | select(.name == $name) | .version) = $version' \
        "$MARKETPLACE_JSON" > "$tmp_file"

    mv "$tmp_file" "$MARKETPLACE_JSON"
}

# Bump a single plugin
bump_plugin() {
    local plugin="$1"
    local bump_type="$2"
    local dry_run="${3:-false}"

    if ! plugin_exists "$plugin"; then
        echo -e "${RED}ERROR: Plugin '$plugin' not found in marketplace.json${NC}" >&2
        echo ""
        echo "Available plugins:"
        jq -r '.plugins[].name' "$MARKETPLACE_JSON" | sed 's/^/  - /'
        exit 1
    fi

    local current_version
    current_version=$(get_plugin_version "$plugin")

    if [[ -z "$current_version" ]]; then
        echo -e "${RED}ERROR: Could not get version for plugin '$plugin'${NC}" >&2
        exit 1
    fi

    local new_version
    new_version=$(bump_version "$current_version" "$bump_type")

    if [[ "$dry_run" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would bump $plugin: $current_version → $new_version ($bump_type)"
    else
        update_version "$plugin" "$new_version"
        echo -e "${GREEN}✓${NC} Bumped $plugin: $current_version → $new_version ($bump_type)"
    fi
}

# Auto-bump based on commits
auto_bump() {
    local dry_run="${1:-false}"

    echo "Analyzing commits for required version bumps..."
    echo ""

    # Get bumps as JSON
    local bumps_json
    bumps_json=$("$REPO_ROOT/scripts/analyze-version-bumps.sh" --json)

    # Check if there are any bumps needed
    local num_bumps
    num_bumps=$(echo "$bumps_json" | jq '.bumps | length')

    if [[ "$num_bumps" -eq 0 ]]; then
        echo "No version bumps required."
        exit 0
    fi

    # Apply each bump
    echo "$bumps_json" | jq -r '.bumps | to_entries[] | "\(.key) \(.value.bump)"' | while read -r plugin bump_type; do
        bump_plugin "$plugin" "$bump_type" "$dry_run"
    done

    echo ""
    if [[ "$dry_run" == "true" ]]; then
        echo "Run without --dry-run to apply changes."
    else
        echo "Done! Don't forget to commit the updated marketplace.json"
    fi
}

# Parse arguments
DRY_RUN=false
AUTO_MODE=false
PLUGIN=""
BUMP_TYPE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
        *)
            if [[ -z "$PLUGIN" ]]; then
                PLUGIN="$1"
            elif [[ -z "$BUMP_TYPE" ]]; then
                BUMP_TYPE="$1"
            else
                echo "Too many arguments" >&2
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Execute
if [[ "$AUTO_MODE" == "true" ]]; then
    auto_bump "$DRY_RUN"
elif [[ -n "$PLUGIN" && -n "$BUMP_TYPE" ]]; then
    bump_plugin "$PLUGIN" "$BUMP_TYPE" "$DRY_RUN"
else
    echo "ERROR: Missing required arguments" >&2
    echo ""
    usage
    exit 1
fi

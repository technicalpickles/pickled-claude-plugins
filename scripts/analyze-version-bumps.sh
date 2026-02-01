#!/usr/bin/env bash
#
# Analyzes commits to determine required version bumps.
#
# Compares current branch to main and parses conventional commits
# to determine what version bumps are needed for each plugin.
#
# Usage:
#   ./scripts/analyze-version-bumps.sh              # Analyze current branch
#   ./scripts/analyze-version-bumps.sh --require    # Exit 1 if bumps needed but not done
#   ./scripts/analyze-version-bumps.sh --json       # Output JSON format
#
# Conventional commit → version bump:
#   feat(plugin):     → minor
#   fix(plugin):      → patch
#   perf(plugin):     → patch
#   feat(plugin)!:    → major
#   BREAKING CHANGE   → major
#

set -eo pipefail
# Note: -u disabled because empty associative arrays cause issues

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

# Parse arguments
REQUIRE_BUMP=false
JSON_OUTPUT=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --require|--require-bump)
            REQUIRE_BUMP=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Get commits that are on current branch but not on main
get_branch_commits() {
    git log "$DEFAULT_BRANCH..HEAD" --pretty=format:"%H %s" 2>/dev/null || echo ""
}

# Get the full commit message (including body) for a commit hash
get_commit_body() {
    local hash="$1"
    git log -1 --pretty=format:"%B" "$hash" 2>/dev/null || echo ""
}

# Parse conventional commit and return: type scope breaking
parse_commit() {
    local subject="$1"

    # Skip merge commits
    if [[ "$subject" =~ ^Merge ]]; then
        echo "skip"
        return
    fi

    # Match: type(scope)!: description or type!: description or type: description
    if [[ "$subject" =~ ^([a-z]+)(\(([a-z0-9-]+)\))?(!)?\:\ .+ ]]; then
        local type="${BASH_REMATCH[1]}"
        local scope="${BASH_REMATCH[3]:-}"
        local breaking="${BASH_REMATCH[4]:-}"
        echo "$type $scope $breaking"
    else
        echo "invalid"
    fi
}

# Determine bump type from commit type and breaking flag
get_bump_type() {
    local type="$1"
    local breaking="$2"
    local body="$3"

    # Check for breaking change
    if [[ -n "$breaking" ]] || [[ "$body" =~ BREAKING[[:space:]]CHANGE ]]; then
        echo "major"
        return
    fi

    case "$type" in
        feat)
            echo "minor"
            ;;
        fix|perf)
            echo "patch"
            ;;
        *)
            echo "none"
            ;;
    esac
}

# Compare version bumps (major > minor > patch > none)
compare_bump() {
    local current="$1"
    local new="$2"

    case "$current" in
        major) echo "major" ;;
        minor)
            if [[ "$new" == "major" ]]; then echo "major"; else echo "minor"; fi
            ;;
        patch)
            case "$new" in
                major) echo "major" ;;
                minor) echo "minor" ;;
                *) echo "patch" ;;
            esac
            ;;
        none|"")
            echo "$new"
            ;;
    esac
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
            echo "$version"
            ;;
    esac
}

# Get current version of a plugin from marketplace.json
get_plugin_version() {
    local plugin="$1"
    jq -r --arg name "$plugin" '.plugins[] | select(.name == $name) | .version' "$MARKETPLACE_JSON" 2>/dev/null || echo "0.0.0"
}

# Main analysis
declare -A PLUGIN_BUMPS=()  # plugin -> bump type (major, minor, patch)
declare -A PLUGIN_COMMITS=()  # plugin -> list of commit descriptions

# Analyze each commit
while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    hash="${line%% *}"
    subject="${line#* }"

    parsed=$(parse_commit "$subject")
    [[ "$parsed" == "skip" || "$parsed" == "invalid" ]] && continue

    read -r type scope breaking <<< "$parsed"

    # Skip commits without scope (repo-wide, no plugin bump)
    [[ -z "$scope" || "$scope" == "repo" ]] && continue

    # Get full commit body for BREAKING CHANGE detection
    body=$(get_commit_body "$hash")

    bump_type=$(get_bump_type "$type" "$breaking" "$body")
    [[ "$bump_type" == "none" ]] && continue

    # Update plugin bump (keep highest)
    current_bump="${PLUGIN_BUMPS[$scope]:-none}"
    PLUGIN_BUMPS[$scope]=$(compare_bump "$current_bump" "$bump_type")

    # Track commits for this plugin
    PLUGIN_COMMITS[$scope]+="  - $subject"$'\n'

done < <(get_branch_commits)

# Output results
num_bumps="${#PLUGIN_BUMPS[@]}"

if [[ "$JSON_OUTPUT" == "true" ]]; then
    echo "{"
    echo '  "bumps": {'
    if [[ $num_bumps -gt 0 ]]; then
        first=true
        for plugin in "${!PLUGIN_BUMPS[@]}"; do
            bump="${PLUGIN_BUMPS[$plugin]}"
            current=$(get_plugin_version "$plugin")
            new=$(bump_version "$current" "$bump")

            [[ "$first" != "true" ]] && echo ","
            first=false

            printf '    "%s": {"current": "%s", "bump": "%s", "new": "%s"}' "$plugin" "$current" "$bump" "$new"
        done
        echo ""
    fi
    echo "  }"
    echo "}"
else
    if [[ $num_bumps -eq 0 ]]; then
        echo "No version bumps required."
        echo ""
        echo "Commits analyzed from: $DEFAULT_BRANCH..HEAD"
        echo "Only feat, fix, and perf commits with plugin scopes trigger bumps."
        exit 0
    fi

    echo "Version Bumps Required"
    echo "======================"
    echo ""

    needs_bump=false
    for plugin in $(echo "${!PLUGIN_BUMPS[@]}" | tr ' ' '\n' | sort); do
        bump="${PLUGIN_BUMPS[$plugin]}"
        current=$(get_plugin_version "$plugin")
        new=$(bump_version "$current" "$bump")

        echo "Plugin: $plugin"
        echo "  Current version: $current"
        echo "  Bump type: $bump"
        echo "  New version: $new"
        echo "  Commits:"
        echo "${PLUGIN_COMMITS[$plugin]}"

        # Check if bump is already done
        if [[ "$current" != "$new" ]]; then
            needs_bump=true
        fi
    done

    echo ""
    echo "To apply bumps, run:"
    for plugin in "${!PLUGIN_BUMPS[@]}"; do
        bump="${PLUGIN_BUMPS[$plugin]}"
        echo "  ./scripts/bump-version.sh $plugin $bump"
    done

    if [[ "$REQUIRE_BUMP" == "true" && "$needs_bump" == "true" ]]; then
        echo ""
        echo "ERROR: Version bumps required but not applied."
        exit 1
    fi
fi

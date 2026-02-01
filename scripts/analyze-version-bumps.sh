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
# How bump detection works:
#   1. Get version at merge-base (when branch diverged from main)
#   2. Calculate expected version based on commits (base + bump)
#   3. Compare: current >= expected means bump already applied
#
# This allows CI to pass after auto-bump, since expected stays stable
# (calculated from merge-base) while current increases.
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

# Get version of a plugin at merge-base with main
get_base_version() {
    local plugin="$1"
    local merge_base
    merge_base=$(git merge-base "$DEFAULT_BRANCH" HEAD 2>/dev/null) || merge_base="$DEFAULT_BRANCH"
    # Use relative path for git show
    git show "$merge_base:.claude-plugin/marketplace.json" 2>/dev/null | jq -r --arg name "$plugin" '.plugins[] | select(.name == $name) | .version' 2>/dev/null || echo "0.0.0"
}

# Compare two semver versions: returns 0 if v1 >= v2, 1 otherwise
version_gte() {
    local v1="$1"
    local v2="$2"

    IFS='.' read -r v1_major v1_minor v1_patch <<< "$v1"
    IFS='.' read -r v2_major v2_minor v2_patch <<< "$v2"

    if (( v1_major > v2_major )); then return 0; fi
    if (( v1_major < v2_major )); then return 1; fi
    if (( v1_minor > v2_minor )); then return 0; fi
    if (( v1_minor < v2_minor )); then return 1; fi
    if (( v1_patch >= v2_patch )); then return 0; fi
    return 1
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
    # Build JSON with only pending bumps (where current < expected)
    pending_bumps=""
    pending_count=0
    if [[ $num_bumps -gt 0 ]]; then
        for plugin in "${!PLUGIN_BUMPS[@]}"; do
            bump="${PLUGIN_BUMPS[$plugin]}"
            base=$(get_base_version "$plugin")
            current=$(get_plugin_version "$plugin")
            expected=$(bump_version "$base" "$bump")

            # Only include if current version hasn't reached expected
            if ! version_gte "$current" "$expected"; then
                [[ $pending_count -gt 0 ]] && pending_bumps+=","$'\n'
                pending_bumps+="    \"$plugin\": {\"current\": \"$current\", \"bump\": \"$bump\", \"new\": \"$expected\"}"
                pending_count=$((pending_count + 1))
            fi
        done
    fi

    echo "{"
    echo '  "bumps": {'
    if [[ $pending_count -gt 0 ]]; then
        echo "$pending_bumps"
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

    echo "Version Bumps Analysis"
    echo "======================"
    echo ""

    needs_bump=false
    declare -A PENDING_PLUGINS=()
    for plugin in $(echo "${!PLUGIN_BUMPS[@]}" | tr ' ' '\n' | sort); do
        bump="${PLUGIN_BUMPS[$plugin]}"
        base=$(get_base_version "$plugin")
        current=$(get_plugin_version "$plugin")
        expected=$(bump_version "$base" "$bump")

        echo "Plugin: $plugin"
        echo "  Base version (at merge-base): $base"
        echo "  Current version: $current"
        echo "  Required bump: $bump"
        echo "  Expected version: $expected"

        # Check if bump is already done (current >= expected)
        if version_gte "$current" "$expected"; then
            echo "  Status: ✓ Already bumped"
        else
            echo "  Status: ✗ Needs bump"
            needs_bump=true
            PENDING_PLUGINS[$plugin]="$bump"
        fi
        echo "  Commits:"
        echo "${PLUGIN_COMMITS[$plugin]}"
    done

    if [[ ${#PENDING_PLUGINS[@]} -gt 0 ]]; then
        echo ""
        echo "To apply pending bumps, run:"
        for plugin in "${!PENDING_PLUGINS[@]}"; do
            bump="${PENDING_PLUGINS[$plugin]}"
            echo "  ./scripts/bump-version.sh $plugin $bump"
        done
    else
        echo ""
        echo "All version bumps have been applied."
    fi

    if [[ "$REQUIRE_BUMP" == "true" && "$needs_bump" == "true" ]]; then
        echo ""
        echo "ERROR: Version bumps required but not applied."
        exit 1
    fi
fi

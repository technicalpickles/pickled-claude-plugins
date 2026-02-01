#!/usr/bin/env bash
#
# Validates conventional commit scopes.
#
# Rules:
# 1. feat, fix, perf commits MUST have a scope (they affect a specific plugin)
# 2. Scope must be a valid plugin name or 'repo' for repo-wide changes
# 3. chore, ci, docs, style, test, refactor, build, revert can omit scope
#
# Usage:
#   ./scripts/check-commit-scope.sh <commit-msg-file>
#   ./scripts/check-commit-scope.sh .git/COMMIT_EDITMSG
#

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"

# Get commit message file
COMMIT_MSG_FILE="${1:-.git/COMMIT_EDITMSG}"

if [[ ! -f "$COMMIT_MSG_FILE" ]]; then
    echo "ERROR: Commit message file not found: $COMMIT_MSG_FILE"
    exit 1
fi

# Read first line of commit message (the subject)
COMMIT_SUBJECT=$(head -1 "$COMMIT_MSG_FILE")

# Skip merge commits, revert commits (auto-generated)
if [[ "$COMMIT_SUBJECT" =~ ^Merge|^Revert ]]; then
    exit 0
fi

# Parse conventional commit format: type(scope)!: description
# or: type!: description
# or: type: description
if [[ ! "$COMMIT_SUBJECT" =~ ^([a-z]+)(\(([a-z0-9-]+)\))?(!)?\:\ .+ ]]; then
    echo "ERROR: Commit message does not match conventional commit format"
    echo "Expected: type(scope): description"
    echo "Got: $COMMIT_SUBJECT"
    exit 1
fi

TYPE="${BASH_REMATCH[1]}"
SCOPE="${BASH_REMATCH[3]:-}"  # May be empty
BREAKING="${BASH_REMATCH[4]:-}"

# Types that REQUIRE a scope (they change plugin behavior)
SCOPE_REQUIRED_TYPES="feat fix perf"

# Types that can omit scope (repo-wide or non-functional changes)
SCOPE_OPTIONAL_TYPES="chore ci docs style test refactor build revert"

# Get valid plugin scopes from marketplace.json
if [[ -f "$MARKETPLACE_JSON" ]]; then
    VALID_PLUGINS=$(jq -r '.plugins[].name' "$MARKETPLACE_JSON" 2>/dev/null | tr '\n' ' ')
else
    echo "WARNING: marketplace.json not found, skipping scope validation"
    exit 0
fi

# Add 'repo' as valid scope for repo-wide changes
VALID_SCOPES="$VALID_PLUGINS repo"

# Check if scope is required
if [[ " $SCOPE_REQUIRED_TYPES " =~ " $TYPE " ]]; then
    if [[ -z "$SCOPE" ]]; then
        echo "ERROR: Commit type '$TYPE' requires a scope"
        echo ""
        echo "Valid scopes (plugin names):"
        echo "  $VALID_PLUGINS"
        echo ""
        echo "Use 'repo' for repo-wide changes:"
        echo "  $TYPE(repo): your message"
        echo ""
        echo "Example:"
        echo "  feat(git): add stash support"
        echo "  fix(ci-cd-tools): handle timeout"
        exit 1
    fi
fi

# Validate scope if provided
if [[ -n "$SCOPE" ]]; then
    if [[ ! " $VALID_SCOPES " =~ " $SCOPE " ]]; then
        echo "ERROR: Invalid scope '$SCOPE'"
        echo ""
        echo "Valid scopes:"
        for plugin in $VALID_PLUGINS; do
            echo "  - $plugin"
        done
        echo "  - repo (for repo-wide changes)"
        exit 1
    fi
fi

# All checks passed
exit 0

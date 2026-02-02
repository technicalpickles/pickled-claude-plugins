#!/usr/bin/env bash
# Integration tests for manifest-driven route discovery
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$(dirname "$PLUGIN_DIR")")"

cd "$PLUGIN_DIR"

echo "=== Integration Tests for Manifest-Driven Discovery ==="
echo ""

# Test 1: Single route file
echo "Test 1: Single route file discovery"
output=$(TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml" uv run tool-routing list 2>&1)
if echo "$output" | grep -q "merged from 1 sources"; then
    echo "  ✓ Single file: found 1 source"
else
    echo "  ✗ Single file: expected 1 source"
    echo "$output"
    exit 1
fi

# Test 2: Multiple route files
echo "Test 2: Multiple route files discovery"
output=$(TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml,$REPO_ROOT/plugins/git/skills/pull-request/tool-routes.yaml" uv run tool-routing list 2>&1)
if echo "$output" | grep -q "merged from 2 sources"; then
    echo "  ✓ Multiple files: found 2 sources"
else
    echo "  ✗ Multiple files: expected 2 sources"
    echo "$output"
    exit 1
fi

# Test 3: Routes from both plugins appear
echo "Test 3: Routes from both plugins appear in merged output"
if echo "$output" | grep -q "bash-cat-heredoc" && echo "$output" | grep -q "github-pr"; then
    echo "  ✓ Routes from both plugins present"
else
    echo "  ✗ Missing routes from one or both plugins"
    echo "$output"
    exit 1
fi

# Test 4: Inline tests pass
echo "Test 4: Inline tests pass"
output=$(TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml" uv run tool-routing test 2>&1)
if echo "$output" | grep -q "0 failed"; then
    echo "  ✓ All inline tests pass"
else
    echo "  ✗ Some inline tests failed"
    echo "$output"
    exit 1
fi

# Test 5: Check command works with explicit routes
echo "Test 5: Check command blocks matching route"
input='{"tool_name": "Bash", "tool_input": {"command": "cat << EOF > file.txt\ntest\nEOF"}}'
result=$(echo "$input" | TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml" uv run tool-routing check 2>&1 || true)
exit_code=$?
# Note: check returns 2 for blocked, 0 for allowed
if echo "$result" | grep -q "Write tool"; then
    echo "  ✓ Check command correctly blocks heredoc"
else
    echo "  ✗ Check command did not block as expected"
    echo "Exit code: $exit_code"
    echo "$result"
    exit 1
fi

# Test 6: Check command allows non-matching
echo "Test 6: Check command allows non-matching route"
input='{"tool_name": "Bash", "tool_input": {"command": "ls -la"}}'
result=$(echo "$input" | TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml" uv run tool-routing check 2>&1)
exit_code=$?
if [ "$exit_code" -eq 0 ]; then
    echo "  ✓ Check command allows non-matching"
else
    echo "  ✗ Check command incorrectly blocked"
    echo "Exit code: $exit_code"
    echo "$result"
    exit 1
fi

echo ""
echo "=== All integration tests passed ==="

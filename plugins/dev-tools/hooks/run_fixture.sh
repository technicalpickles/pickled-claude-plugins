#!/bin/bash
# Helper script to manually test fixtures
# Usage: ./run_fixture.sh <fixture-path> [debug]
#
# Examples:
#   ./run_fixture.sh fixtures/webfetch/atlassian-url.json
#   ./run_fixture.sh fixtures/bash/mcp-search.json debug

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
HOOK_SCRIPT="$SCRIPT_DIR/check_tool_routing.py"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <fixture-path> [debug]"
    echo ""
    echo "Examples:"
    echo "  $0 fixtures/webfetch/atlassian-url.json"
    echo "  $0 fixtures/bash/mcp-search.json debug"
    echo ""
    echo "Available fixtures:"
    find "$SCRIPT_DIR/fixtures" -name "*.json" -type f | sed "s|$SCRIPT_DIR/||" | sort
    exit 1
fi

FIXTURE_PATH="$1"
DEBUG_MODE="${2:-}"

# Resolve fixture path
if [ ! -f "$FIXTURE_PATH" ]; then
    # Try relative to script directory
    if [ -f "$SCRIPT_DIR/$FIXTURE_PATH" ]; then
        FIXTURE_PATH="$SCRIPT_DIR/$FIXTURE_PATH"
    else
        echo "Error: Fixture not found: $FIXTURE_PATH"
        exit 1
    fi
fi

echo "=========================================="
echo "Running fixture: $(basename "$FIXTURE_PATH")"
echo "=========================================="
echo ""

# Load fixture
FIXTURE_NAME=$(jq -r '.name' "$FIXTURE_PATH")
EXPECTED_EXIT=$(jq -r '.expected_exit' "$FIXTURE_PATH")
TOOL_CALL=$(jq '.tool_call' "$FIXTURE_PATH")

echo "Test: $FIXTURE_NAME"
echo "Expected exit: $EXPECTED_EXIT"
echo ""

# Set up environment
export CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR"
if [ "$DEBUG_MODE" = "debug" ]; then
    export TOOL_ROUTING_DEBUG=1
    echo "[Debug mode enabled]"
    echo ""
fi

# Run the hook
echo "Running hook..."
echo ""
set +e  # Don't exit on error
echo "$TOOL_CALL" | uv run "$HOOK_SCRIPT" 2>&1
ACTUAL_EXIT=$?
set -e

echo ""
echo "=========================================="
echo "Actual exit: $ACTUAL_EXIT"
echo "Expected exit: $EXPECTED_EXIT"

if [ $ACTUAL_EXIT -eq $EXPECTED_EXIT ]; then
    echo "✅ PASSED"
    exit 0
else
    echo "❌ FAILED - Exit code mismatch"
    exit 1
fi

#!/usr/bin/env bash
# Test scenarios for the buildkite plugin hook behavior.
#
# Runs Claude Code with the plugin installed via test-claude,
# gives it prompts that should trigger (or not trigger) the hook,
# and checks the output for expected behavior.
#
# Usage:
#   ./tests/scenarios/test-hook-behavior.sh
#
# Logs are saved to tmp/test-results/<timestamp>/ for review.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_CLAUDE="$REPO_ROOT/bin/test-claude"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="$REPO_ROOT/tmp/test-results/$TIMESTAMP"
mkdir -p "$LOG_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
DIM='\033[2m'
NC='\033[0m'

pass() { echo -e "${GREEN}PASS${NC} $1"; }
fail() { echo -e "${RED}FAIL${NC} $1"; }
info() { echo -e "${BLUE}INFO${NC} $1"; }
section() { echo -e "\n${YELLOW}=== $1 ===${NC}\n"; }

PASSED=0
FAILED=0
SCENARIO_NUM=0

run_scenario() {
    local name="$1"
    local prompt="$2"
    local expect_pattern="$3"
    local expect_absent="${4:-}"

    SCENARIO_NUM=$((SCENARIO_NUM + 1))
    local slug
    slug=$(echo "$name" | tr ' ' '-' | tr -cd 'a-zA-Z0-9-')
    local logfile="$LOG_DIR/${SCENARIO_NUM}-${slug}.log"

    info "Running: $name"
    "$TEST_CLAUDE" -p "$prompt" --verbose --output-format stream-json --include-hook-events --max-turns 3 > "$logfile" 2>&1 || true

    echo -e "  ${DIM}Log: $logfile${NC}"

    local matched=true

    if [ -n "$expect_pattern" ]; then
        if grep -qi "$expect_pattern" "$logfile"; then
            : # found
        else
            matched=false
            fail "$name: expected to find '$expect_pattern' in output"
        fi
    fi

    if [ -n "$expect_absent" ]; then
        if grep -qi "$expect_absent" "$logfile"; then
            matched=false
            fail "$name: expected NOT to find '$expect_absent' in output"
        fi
    fi

    if [ "$matched" = true ]; then
        pass "$name"
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi

    echo ""
}

section "Scenario 1: Hook blocks explicit bk build usage"
# The prompt explicitly asks to use bk build view.
# The hook should intercept this and block it, suggesting bktide instead.
run_scenario \
    "explicit bk build blocked" \
    "Run this command: bk build view 151 -p claude-code --org gusto. Do not use any other tool." \
    "bktide"

section "Scenario 2: Hook blocks bk job log"
run_scenario \
    "explicit bk job log blocked" \
    "Run this command: bk job log --job abc123. Do not use any other tool." \
    "bktide"

section "Scenario 3: bk auth passes through"
# bk auth status should NOT be intercepted.
run_scenario \
    "bk auth not blocked" \
    "Run this command and report the output: bk auth status" \
    "" \
    "was intercepted"

section "Scenario 4: Natural build investigation uses bktide"
# Give a build URL and ask to investigate. The skill should guide
# the agent to use bktide snapshot. If it tries bk instead, the hook catches it.
run_scenario \
    "natural investigation prefers bktide" \
    "Investigate this failing Buildkite build: https://buildkite.com/gusto/claude-code/builds/151. Tell me what failed and why. Be concise." \
    "bktide"

section "Results"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "\nAll logs: ${DIM}$LOG_DIR/${NC}"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi

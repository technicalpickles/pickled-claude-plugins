#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Simple test runner for tool routing hook
Run from plugins/dev-tools: uv run hooks/test_tool_routing.py

For design principles and implementation details, see:
docs/tool-routing-hook.md
"""
import subprocess
import json
import os
import sys

# Setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)
HOOK_SCRIPT = os.path.join(SCRIPT_DIR, 'check_tool_routing.py')
os.environ['CLAUDE_PLUGIN_ROOT'] = PLUGIN_DIR

passed = 0
failed = 0

def test(name, input_data, expected_exit, should_contain=None, should_not_contain=None, debug_mode=False):
    """Run a single test case."""
    global passed, failed

    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"Expected exit: {expected_exit}")
    if should_contain:
        print(f"Should contain: '{should_contain}'")
    if should_not_contain:
        print(f"Should NOT contain: '{should_not_contain}'")
    if debug_mode:
        print(f"Debug mode: enabled")

    # Setup environment
    env = os.environ.copy()
    if debug_mode:
        env['TOOL_ROUTING_DEBUG'] = '1'
    elif 'TOOL_ROUTING_DEBUG' in env:
        del env['TOOL_ROUTING_DEBUG']

    # Run the hook
    try:
        result = subprocess.run(
            ['uv', 'run', HOOK_SCRIPT],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=2,
            env=env
        )

        actual_exit = result.returncode
        output = result.stdout + result.stderr

        print(f"Actual exit: {actual_exit}")

        # Check exit code
        if actual_exit != expected_exit:
            print(f"❌ FAILED - Exit code mismatch")
            print(f"\nOutput:\n{output}")
            failed += 1
            return

        # Check output contains expected text
        if should_contain and should_contain not in output:
            print(f"❌ FAILED - Output doesn't contain expected text")
            print(f"\nOutput:\n{output}")
            failed += 1
            return

        # Check output does NOT contain text
        if should_not_contain and should_not_contain in output:
            print(f"❌ FAILED - Output contains text that should be excluded")
            print(f"\nOutput:\n{output}")
            failed += 1
            return

        print(f"✅ PASSED")
        if output.strip():
            print(f"Output: {output[:200]}")  # Show first 200 chars
        passed += 1

    except subprocess.TimeoutExpired:
        print(f"❌ FAILED - Timeout")
        failed += 1
    except Exception as e:
        print(f"❌ FAILED - Exception: {e}")
        failed += 1

def main():
    print("Tool Routing Hook Test Suite")
    print(f"Plugin root: {os.environ['CLAUDE_PLUGIN_ROOT']}")
    print(f"Hook script: {HOOK_SCRIPT}")

    # Test 1: Atlassian URL should block
    test(
        "Atlassian URL blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://company.atlassian.net/browse/PROJ-123"}
        },
        expected_exit=2,
        should_contain="Atlassian MCP tools"
    )

    # Test 2: GitHub PR URL should block
    test(
        "GitHub PR URL blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://github.com/user/repo/pull/42"}
        },
        expected_exit=2,
        should_contain="gh pr view"
    )

    # Test 3: Random URL should allow
    test(
        "Random URL allows",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com/page"}
        },
        expected_exit=0
    )

    # Test 4: Non-WebFetch tool ignores
    test(
        "Non-WebFetch tool ignores",
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file"}
        },
        expected_exit=0
    )

    # Test 5: WebFetch with no URL allows
    test(
        "WebFetch with no URL allows",
        {
            "tool_name": "WebFetch",
            "tool_input": {}
        },
        expected_exit=0
    )

    # Test 6: Empty input allows (fail-open)
    test(
        "Empty input allows (fail-open)",
        {},
        expected_exit=0
    )

    # Test 7: Atlassian subdomain
    test(
        "Atlassian subdomain blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://myteam.atlassian.net/wiki/spaces/TEAM"}
        },
        expected_exit=2,
        should_contain="Atlassian MCP tools"
    )

    # Test 8: GitHub issues URL
    test(
        "GitHub issues URL blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://github.com/user/repo/pull/123"}
        },
        expected_exit=2,
        should_contain="gh pr view"
    )

    # Test 9: Normal mode should NOT include debug info
    test(
        "Normal mode excludes matched URL",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://github.com/user/repo/pull/42"}
        },
        expected_exit=2,
        should_contain="gh pr view",
        should_not_contain="Matched URL:",
        debug_mode=False
    )

    # Test 10: Normal mode should NOT include route name
    test(
        "Normal mode excludes route name",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://company.atlassian.net/browse/PROJ-123"}
        },
        expected_exit=2,
        should_contain="Atlassian MCP tools",
        should_not_contain="Tool Routing:",
        debug_mode=False
    )

    # Test 11: Debug mode SHOULD include matched URL
    test(
        "Debug mode includes matched URL",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://github.com/user/repo/pull/42"}
        },
        expected_exit=2,
        should_contain="Matched URL: https://github.com/user/repo/pull/42",
        debug_mode=True
    )

    # Test 12: Debug mode SHOULD include route name
    test(
        "Debug mode includes route name",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://company.atlassian.net/browse/PROJ-123"}
        },
        expected_exit=2,
        should_contain="Tool Routing: atlassian",
        debug_mode=True
    )

    # Test 13: Debug mode SHOULD include pattern
    test(
        "Debug mode includes pattern",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://github.com/user/repo/pull/42"}
        },
        expected_exit=2,
        should_contain="Pattern:",
        debug_mode=True
    )

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()

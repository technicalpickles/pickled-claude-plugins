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
from pathlib import Path

# Setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)
HOOK_SCRIPT = os.path.join(SCRIPT_DIR, 'check_tool_routing.py')
FIXTURES_DIR = os.path.join(SCRIPT_DIR, 'fixtures')
os.environ['CLAUDE_PLUGIN_ROOT'] = PLUGIN_DIR

passed = 0
failed = 0

def load_fixtures():
    """Load all fixture files from the fixtures directory."""
    fixtures = []
    fixtures_path = Path(FIXTURES_DIR)

    if not fixtures_path.exists():
        print(f"Warning: Fixtures directory not found: {FIXTURES_DIR}")
        return fixtures

    # Recursively find all .json files
    for fixture_file in fixtures_path.rglob('*.json'):
        try:
            with open(fixture_file, 'r') as f:
                fixture = json.load(f)
                fixture['_source'] = str(fixture_file.relative_to(fixtures_path))
                fixtures.append(fixture)
        except Exception as e:
            print(f"Warning: Failed to load fixture {fixture_file}: {e}")

    return fixtures

def test_from_fixture(fixture, debug_mode=False):
    """Run a test from a fixture definition."""
    assertions = fixture.get('assertions', {})
    test(
        name=fixture['name'],
        input_data=fixture['tool_call'],
        expected_exit=fixture['expected_exit'],
        should_contain=assertions.get('should_contain'),
        should_not_contain=assertions.get('should_not_contain'),
        debug_mode=debug_mode,
        source=fixture.get('_source')
    )

def test(name, input_data, expected_exit, should_contain=None, should_not_contain=None, debug_mode=False, source=None):
    """Run a single test case."""
    global passed, failed

    print(f"\n{'='*60}")
    print(f"Test: {name}")
    if source:
        print(f"Source: {source}")
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

    # Load and run fixture-based tests
    print("\n" + "="*60)
    print("FIXTURE-BASED TESTS")
    print("="*60)
    fixtures = load_fixtures()
    print(f"Loaded {len(fixtures)} fixtures from {FIXTURES_DIR}")

    for fixture in fixtures:
        test_from_fixture(fixture)

    # Legacy inline tests below
    print("\n" + "="*60)
    print("INLINE TESTS (Legacy)")
    print("="*60)

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

    # Test 3: Buildkite build URL should block
    test(
        "Buildkite build URL blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://buildkite.com/gusto/zenpayroll-deployment/builds/180747"}
        },
        expected_exit=2,
        should_contain="Buildkite MCP tools"
    )

    # Test 4: Buildkite build URL with different org/pipeline
    test(
        "Buildkite different org blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://buildkite.com/myorg/my-pipeline/builds/123"}
        },
        expected_exit=2,
        should_contain="Buildkite MCP tools"
    )

    # Test 5: Random URL should allow
    test(
        "Random URL allows",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com/page"}
        },
        expected_exit=0
    )

    # Test 6: Non-WebFetch tool ignores
    test(
        "Non-WebFetch tool ignores",
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file"}
        },
        expected_exit=0
    )

    # Test 7: WebFetch with no URL allows
    test(
        "WebFetch with no URL allows",
        {
            "tool_name": "WebFetch",
            "tool_input": {}
        },
        expected_exit=0
    )

    # Test 8: Empty input allows (fail-open)
    test(
        "Empty input allows (fail-open)",
        {},
        expected_exit=0
    )

    # Test 9: Atlassian subdomain
    test(
        "Atlassian subdomain blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://myteam.atlassian.net/wiki/spaces/TEAM"}
        },
        expected_exit=2,
        should_contain="Atlassian MCP tools"
    )

    # Test 10: GitHub issues URL
    test(
        "GitHub issues URL blocks",
        {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://github.com/user/repo/pull/123"}
        },
        expected_exit=2,
        should_contain="gh pr view"
    )

    # Test 11: Normal mode should NOT include debug info
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

    # Test 12: Normal mode should NOT include route name
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

    # Test 13: Debug mode SHOULD include matched URL
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

    # Test 14: Debug mode SHOULD include route name
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

    # Test 15: Debug mode SHOULD include pattern
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

    # Test 16: Bash with 'mcp list-tools' should block
    test(
        "Bash 'mcp list-tools' blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp list-tools 2>&1 | grep -i buildkite"}
        },
        expected_exit=2,
        should_contain="mcp__MCPProxy__retrieve_tools"
    )

    # Test 17: Bash with 'mcp search' should block
    test(
        "Bash 'mcp search' blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp search buildkite"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call the 'mcp' CLI"
    )

    # Test 18: Bash with 'mcp__MCPProxy__retrieve_tools' should block
    test(
        "Bash 'mcp__MCPProxy__retrieve_tools' blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp__MCPProxy__retrieve_tools buildkite"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call MCP tool functions"
    )

    # Test 19: Bash with 'mcp__MCPProxy__call_tool' should block
    test(
        "Bash 'mcp__MCPProxy__call_tool' blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp__MCPProxy__call_tool buildkite:get_build"}
        },
        expected_exit=2,
        should_contain="MCP tools like 'mcp__MCPProxy__retrieve_tools' are tool calls"
    )

    # Test 20: Normal bash command should allow
    test(
        "Normal bash command allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"}
        },
        expected_exit=0
    )

    # Test 21: Bash with 'echo' should allow
    test(
        "Bash 'echo' allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'mcp is mentioned but not as command'"}
        },
        expected_exit=0
    )

    # Test 22: Bash with spaces before 'mcp' should block
    test(
        "Bash with leading spaces 'mcp' blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "  mcp list-tools"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call the 'mcp' CLI"
    )

    # Test 23: Debug mode for Bash command should show command
    test(
        "Debug mode shows matched command",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp__MCPProxy__retrieve_tools buildkite"}
        },
        expected_exit=2,
        should_contain="Matched Command:",
        debug_mode=True
    )

    # Test 24: Bash 'mcp' with pipes should block
    test(
        "Bash 'mcp' with pipes blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp list-tools 2>&1 | grep -i buildkite"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call the 'mcp' CLI"
    )

    # Test 25: Bash 'mcp' with redirects should block
    test(
        "Bash 'mcp' with redirects blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp search github > /tmp/output.txt"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call the 'mcp' CLI"
    )

    # Test 26: Bash 'mcp__' with pipes should block
    test(
        "Bash 'mcp__' with pipes blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp__MCPProxy__retrieve_tools github | jq ."}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call MCP tool functions"
    )

    # Test 27: Bash with command substitution containing 'mcp' should block
    test(
        "Bash command substitution with 'mcp' blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp list-tools | head -n 5"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call the 'mcp' CLI"
    )

    # Test 28: Bash 'mcp' in middle of pipeline should allow (not at start)
    test(
        "Bash 'mcp' in middle of command allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'test mcp stuff' | grep mcp"}
        },
        expected_exit=0
    )

    # Test 29: Bash with tab characters before 'mcp' should block
    test(
        "Bash with tabs before 'mcp' blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "\t\tmcp search test"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call the 'mcp' CLI"
    )

    # Test 30: Bash 'mcp' with complex shell syntax should block
    test(
        "Bash 'mcp' with complex syntax blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "mcp list-tools 2>&1 | grep buildkite | wc -l"}
        },
        expected_exit=2,
        should_contain="Don't use Bash to call the 'mcp' CLI"
    )

    # Test 31: Bash cat with heredoc and redirect should block
    test(
        "Bash cat heredoc with redirect blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "cat > file.txt << 'EOF'\nHello world\nEOF"}
        },
        expected_exit=2,
        should_contain="Use the Write tool"
    )

    # Test 32: Bash cat with heredoc (no redirect) should block
    test(
        "Bash cat heredoc without redirect blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "cat << EOF\nSome content\nEOF"}
        },
        expected_exit=2,
        should_contain="displaying text to the user"
    )

    # Test 33: Bash cat with heredoc and append should block
    test(
        "Bash cat heredoc with append blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "cat <<-EOF >> file.log\nLog entry\nEOF"}
        },
        expected_exit=2,
        should_contain="Use the Write tool"
    )

    # Test 34: Bash cat heredoc reversed order should block
    test(
        "Bash cat heredoc reversed order blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "cat << 'DATA' > output.txt\nContent here\nDATA"}
        },
        expected_exit=2,
        should_contain="Use the Write tool"
    )

    # Test 35: Bash cat heredoc with pipe should allow
    test(
        "Bash cat heredoc with pipe allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "cat <<EOF | jq .\n{\"key\": \"value\"}\nEOF"}
        },
        expected_exit=0
    )

    # Test 36: Bash cat heredoc piped to grep should allow
    test(
        "Bash cat heredoc piped to grep allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "cat <<'DATA' | grep foo\nfoo bar\nDATA"}
        },
        expected_exit=0
    )

    # Test 37: Bash triple echo chain should block
    test(
        "Bash triple echo chain blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo \"=== SUMMARY ===\" && echo \"\" && echo \"✅ Task complete\""}
        },
        expected_exit=2,
        should_contain="Output text directly"
    )

    # Test 38: Bash single echo should allow
    test(
        "Bash single echo allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'test' > file.txt"}
        },
        expected_exit=0
    )

    # Test 39: Bash conditional echo with || should allow
    test(
        "Bash conditional echo allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "test -f file.txt && echo 'found' || echo 'not found'"}
        },
        expected_exit=0
    )

    # Test 40: Bash double echo chain should allow (requires 3+ to block)
    test(
        "Bash double echo chain allows",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'Step 1' && echo 'Step 2'"}
        },
        expected_exit=0
    )

    # Test 41: Bash very long echo chain should block
    test(
        "Bash long echo chain blocks",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo \"Line 1\" && echo \"Line 2\" && echo \"Line 3\" && echo \"Line 4\" && echo \"Line 5\""}
        },
        expected_exit=2,
        should_contain="Don't use chained echo commands"
    )

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()

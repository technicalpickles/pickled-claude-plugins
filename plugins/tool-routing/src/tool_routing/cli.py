"""Command-line interface for tool-routing."""

import argparse
import json
import os
import sys
from pathlib import Path

from tool_routing.checker import check_tool_call
from tool_routing.config import load_routes_file

DEBUG = os.environ.get("TOOL_ROUTING_DEBUG", "").lower() in ("1", "true", "yes")


def get_plugin_root() -> Path:
    """Get plugin root from environment."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        return Path(plugin_root)
    return Path.cwd()


def cmd_check(args: argparse.Namespace) -> int:
    """Check a tool call against routes (hook entry point)."""
    plugin_root = get_plugin_root()

    # Load routes from plugin's hooks directory
    routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    routes = load_routes_file(routes_file)

    if not routes:
        # No routes configured, allow
        return 0

    # Read tool call from stdin
    try:
        raw_input = sys.stdin.read()
        tool_call = json.loads(raw_input)
    except json.JSONDecodeError:
        # Invalid input, fail open
        return 0

    # Check against routes
    result = check_tool_call(tool_call, routes)

    if result.blocked:
        if DEBUG:
            print(f"❌ Tool Routing: {result.route_name}", file=sys.stderr)
            if result.matched_value:
                display = result.matched_value
                if len(display) > 200:
                    display = display[:200] + "..."
                print(f"Matched: {display}", file=sys.stderr)
            print(f"Pattern: {result.pattern}", file=sys.stderr)
            print("", file=sys.stderr)
        print(result.message, file=sys.stderr)
        return 2

    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run inline test fixtures."""
    from tool_routing.test_runner import format_results, run_route_tests

    plugin_root = get_plugin_root()

    # Load routes from plugin's hooks directory
    routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    routes = load_routes_file(routes_file)

    if not routes:
        print("No routes found", file=sys.stderr)
        return 1

    # Count tests
    total_tests = sum(len(r.tests) for r in routes.values())
    if total_tests == 0:
        print("No tests found in routes")
        return 0

    # Run tests
    results = run_route_tests(routes)

    # Format and print results
    print(format_results(results, str(routes_file)))
    print()

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"{passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


def cmd_list(args: argparse.Namespace) -> int:
    """List merged routes."""
    plugin_root = get_plugin_root()

    # Load routes from plugin's hooks directory
    routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    routes = load_routes_file(routes_file)

    if not routes:
        print("No routes found")
        return 0

    print(f"Routes (from {routes_file}):\n")

    for name, route in routes.items():
        print(f"{name}")
        print(f"  tool: {route.tool}")
        print(f"  pattern: {route.pattern}")
        if route.tests:
            print(f"  tests: {len(route.tests)}")
        print()

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="tool-routing",
        description="Route tool calls to better alternatives",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check subcommand
    check_parser = subparsers.add_parser(
        "check",
        help="Check a tool call against routes (hook entry point)",
    )
    check_parser.set_defaults(func=cmd_check)

    # test subcommand
    test_parser = subparsers.add_parser(
        "test",
        help="Run inline test fixtures",
    )
    test_parser.set_defaults(func=cmd_test)

    # list subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="List merged routes from all sources",
    )
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

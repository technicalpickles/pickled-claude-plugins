"""Command-line interface for tool-routing."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from tool_routing.checker import check_tool_call
from tool_routing.config import RouteConflictError, load_routes_file
from tool_routing.integration_runner import (
    evaluate_report,
    format_evaluate_results,
    list_integration_tests,
)

if TYPE_CHECKING:
    from tool_routing.config import Route

DEBUG = os.environ.get("TOOL_ROUTING_DEBUG", "").lower() in ("1", "true", "yes")


def get_all_routes() -> tuple[dict[str, "Route"], list[str]]:
    """Load routes from all sources using manifest-driven discovery.

    Returns:
        Tuple of (merged routes dict, list of source files)

    Environment:
        TOOL_ROUTING_ROUTES: Comma-separated list of explicit route file paths.
            If set, use these instead of Claude CLI discovery. Useful for testing.
    """
    from tool_routing.config import merge_routes_dicts
    from tool_routing.discovery import discover_all_routes

    # Check for explicit routes (testing mode)
    explicit_routes = os.environ.get("TOOL_ROUTING_ROUTES", "")
    if explicit_routes:
        paths = [Path(p.strip()) for p in explicit_routes.split(",") if p.strip()]
    else:
        project_root = os.environ.get("CLAUDE_PROJECT_ROOT", str(Path.cwd()))
        paths = discover_all_routes(project_root)

    all_routes = []
    all_sources = []

    for path in paths:
        routes = load_routes_file(path)
        if routes:
            all_routes.append(routes)
            all_sources.append(str(path))

    if not all_routes:
        return {}, []

    merged = merge_routes_dicts(all_routes, all_sources)
    return merged, all_sources


def cmd_check(args: argparse.Namespace) -> int:
    """Check a tool call against routes (hook entry point)."""
    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 0  # Fail open

    if not routes:
        return 0

    # Read tool call from stdin
    try:
        raw_input = sys.stdin.read()
        tool_call = json.loads(raw_input)
    except json.JSONDecodeError:
        return 0

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

    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    if not routes:
        print("No routes found", file=sys.stderr)
        return 1

    total_tests = sum(len(r.tests) for r in routes.values())
    if total_tests == 0:
        print("No tests found in routes")
        return 0

    results = run_route_tests(routes)

    # Group results by source
    by_source = {}
    for result in results:
        route = routes[result.route_name]
        source = route.source or "unknown"
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(result)

    # Print grouped results
    for source, source_results in by_source.items():
        print(format_results(source_results, source))
        print()

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    print(f"{passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


def cmd_list(args: argparse.Namespace) -> int:
    """List merged routes."""
    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    if not routes:
        print("No routes found")
        return 0

    print(f"Routes (merged from {len(sources)} sources):\n")

    for name, route in routes.items():
        print(f"{name} (from: {route.source})")
        print(f"  tool: {route.tool}")
        print(f"  pattern: {route.pattern}")
        if route.tests:
            print(f"  tests: {len(route.tests)}")
        print()

    return 0


def cmd_integration_test(args: argparse.Namespace) -> int:
    """Run integration test operations."""
    if args.list_tests:
        return cmd_integration_list()
    elif args.evaluate:
        return cmd_integration_evaluate(args)
    else:
        print("Either --list or --evaluate is required", file=sys.stderr)
        return 1


def cmd_integration_list() -> int:
    """List integration tests as JSON."""
    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    if not routes:
        print("[]")
        return 0

    tests = list_integration_tests(routes)
    print(json.dumps(tests, indent=2))
    return 0


def cmd_integration_evaluate(args: argparse.Namespace) -> int:
    """Evaluate integration test report."""
    if not args.tests or not args.report:
        print("--tests and --report are required with --evaluate", file=sys.stderr)
        return 1

    # Load tests file
    try:
        with open(args.tests) as f:
            tests = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading tests file: {e}", file=sys.stderr)
        return 1

    # Load report file
    try:
        with open(args.report) as f:
            report = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading report file: {e}", file=sys.stderr)
        return 1

    result = evaluate_report(tests, report)
    print(format_evaluate_results(result, json_output=args.json_output))

    return 0 if result.failed == 0 else 1


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

    # integration-test subcommand
    integration_parser = subparsers.add_parser(
        "integration-test",
        help="Integration testing via subagents",
    )
    integration_parser.add_argument(
        "--list",
        dest="list_tests",
        action="store_true",
        help="List test cases as JSON",
    )
    integration_parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate subagent report",
    )
    integration_parser.add_argument(
        "--tests",
        type=str,
        help="Path to tests JSON file (for --evaluate)",
    )
    integration_parser.add_argument(
        "--report",
        type=str,
        help="Path to report JSON file (for --evaluate)",
    )
    integration_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output results as JSON",
    )
    integration_parser.set_defaults(func=cmd_integration_test)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

"""Command-line interface for tool-routing."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from tool_routing.checker import check_tool_call
from tool_routing.config import RouteConflictError, load_routes_file

if TYPE_CHECKING:
    from tool_routing.config import Route

DEBUG = os.environ.get("TOOL_ROUTING_DEBUG", "").lower() in ("1", "true", "yes")


def get_plugin_root() -> Path:
    """Get plugin root from environment."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        return Path(plugin_root)
    return Path.cwd()


def get_all_routes() -> tuple[dict[str, "Route"], list[str]]:
    """Load routes from all sources.

    Returns:
        Tuple of (merged routes dict, list of source files)
    """
    from tool_routing.config import (
        discover_plugin_routes,
        discover_project_routes,
        merge_routes_dicts,
    )

    plugin_root = get_plugin_root()
    plugins_dir = Path(os.environ.get("CLAUDE_PLUGINS_DIR", ""))
    project_root = Path(os.environ.get("CLAUDE_PROJECT_ROOT", Path.cwd()))

    all_routes = []
    all_sources = []

    # 1. This plugin's routes
    own_routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    if own_routes_file.exists():
        routes = load_routes_file(own_routes_file)
        if routes:
            all_routes.append(routes)
            all_sources.append(str(own_routes_file))

    # 2. Other plugins' routes
    if plugins_dir.exists():
        for path in discover_plugin_routes(plugins_dir):
            # Skip our own routes (already loaded)
            if path == own_routes_file:
                continue
            routes = load_routes_file(path)
            if routes:
                all_routes.append(routes)
                all_sources.append(str(path))

    # 3. Project routes
    project_routes_path = discover_project_routes(project_root)
    if project_routes_path:
        routes = load_routes_file(project_routes_path)
        if routes:
            all_routes.append(routes)
            all_sources.append(str(project_routes_path))

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

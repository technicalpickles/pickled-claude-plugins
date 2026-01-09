"""Command-line interface for tool-routing."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from tool_routing.checker import check_tool_call
from tool_routing.config import RouteConflictError, discover_craftdesk_routes, load_routes_file
from tool_routing.integration_runner import (
    evaluate_report,
    format_evaluate_results,
    list_integration_tests,
)

if TYPE_CHECKING:
    from tool_routing.config import Route

DEBUG = os.environ.get("TOOL_ROUTING_DEBUG", "").lower() in ("1", "true", "yes")


def get_plugin_root() -> Path:
    """Get plugin root from environment."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        return Path(plugin_root)
    return Path.cwd()


def derive_plugins_dir(plugin_root: Path) -> Path:
    """Derive plugins directory from plugin root.

    Handles both layouts:
    - Flat: plugins_dir/this-plugin/ -> parent is plugins_dir
    - Versioned: plugins_dir/this-plugin/1.0.0/ -> grandparent is plugins_dir

    Uses CLAUDE_PLUGINS_DIR env var if set, otherwise derives from plugin_root.
    """
    plugins_dir_env = os.environ.get("CLAUDE_PLUGINS_DIR", "")
    if plugins_dir_env:
        return Path(plugins_dir_env)

    # Check if we're in versioned layout by looking at directory structure
    # Versioned: .../plugins_dir/plugin-name/1.0.0/
    parent = plugin_root.parent  # plugin-name/
    grandparent = parent.parent  # plugins_dir/

    # Heuristic: if grandparent has multiple subdirectories that look like plugins
    # (i.e., have version subdirs with hooks/ or skills/), use grandparent
    if grandparent.exists():
        plugin_like_siblings = 0
        for sibling in grandparent.iterdir():
            if sibling.is_dir() and sibling != parent:
                # Check if sibling has version subdirs with hooks/skills
                for subdir in sibling.iterdir():
                    if subdir.is_dir() and ((subdir / "hooks").exists() or (subdir / "skills").exists()):
                        plugin_like_siblings += 1
                        break
        if plugin_like_siblings > 0:
            # This looks like versioned layout
            return grandparent

    # Default to flat layout
    return parent


def get_all_routes() -> tuple[dict[str, "Route"], list[str]]:
    """Load routes from all sources.

    Returns:
        Tuple of (merged routes dict, list of source files)

    Environment:
        TOOL_ROUTING_ISOLATED: If set to "1", only load routes from CLAUDE_PLUGIN_ROOT,
            skipping sibling plugin discovery and project routes. Useful for testing.
    """
    from tool_routing.config import (
        discover_plugin_routes,
        discover_project_routes,
        merge_routes_dicts,
    )

    plugin_root = get_plugin_root()
    project_root = Path(os.environ.get("CLAUDE_PROJECT_ROOT", Path.cwd()))
    isolated = os.environ.get("TOOL_ROUTING_ISOLATED", "").lower() in ("1", "true", "yes")

    all_routes = []
    all_sources = []

    # 1. This plugin's routes
    own_routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    if own_routes_file.exists():
        routes = load_routes_file(own_routes_file)
        if routes:
            all_routes.append(routes)
            all_sources.append(str(own_routes_file))

    # Skip sibling/project discovery in isolated mode
    if not isolated:
        plugins_dir = derive_plugins_dir(plugin_root)

        # 2. Other plugins' routes
        if plugins_dir.exists():
            for path in discover_plugin_routes(plugins_dir):
                # Skip our own routes (already loaded) - resolve to absolute for comparison
                if path.resolve() == own_routes_file.resolve():
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

    # 4. Craftdesk-installed skills' routes
    for path in discover_craftdesk_routes(project_root):
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

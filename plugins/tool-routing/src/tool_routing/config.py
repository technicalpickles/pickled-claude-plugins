"""Configuration loading and merging for tool routing."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


class RouteConflictError(Exception):
    """Raised when two sources define the same route name."""

    pass


@dataclass
class TestCase:
    """Inline test case for a route."""

    input: dict
    expect: str  # "block" or "allow"
    desc: Optional[str] = None
    contains: Optional[str] = None


@dataclass
class Route:
    """A single routing rule."""

    tool: str
    pattern: str
    message: str
    tests: list[TestCase] = field(default_factory=list)
    source: Optional[str] = None  # File path where route was defined


def load_routes_file(path: Path) -> dict[str, Route]:
    """Load routes from a YAML file.

    Returns empty dict if file doesn't exist or is invalid (fail open).
    """
    if not path.exists():
        return {}

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return {}

    if not data or "routes" not in data:
        return {}

    routes = {}
    for name, route_data in data.get("routes", {}).items():
        tests = []
        for test_data in route_data.get("tests", []):
            tests.append(
                TestCase(
                    input=test_data["input"],
                    expect=test_data["expect"],
                    desc=test_data.get("desc"),
                    contains=test_data.get("contains"),
                )
            )

        routes[name] = Route(
            tool=route_data["tool"],
            pattern=route_data["pattern"],
            message=route_data["message"],
            tests=tests,
            source=str(path),
        )

    return routes


def merge_routes_dicts(
    route_dicts: list[dict[str, Route]], sources: list[str]
) -> dict[str, Route]:
    """Merge multiple route dictionaries, erroring on conflicts.

    Args:
        route_dicts: List of route dictionaries to merge
        sources: List of source file paths (parallel to route_dicts)

    Returns:
        Merged dictionary of routes

    Raises:
        RouteConflictError: If same route name appears in multiple sources
    """
    merged = {}
    route_sources = {}  # Track which source defined each route

    for routes, source in zip(route_dicts, sources):
        for name, route in routes.items():
            if name in merged:
                raise RouteConflictError(
                    f"Route '{name}' defined in multiple sources: "
                    f"'{route_sources[name]}' and '{source}'"
                )
            merged[name] = route
            route.source = source
            route_sources[name] = source

    return merged


def merge_routes(paths: list[Path]) -> dict[str, Route]:
    """Load and merge routes from multiple YAML files.

    Args:
        paths: List of paths to tool-routes.yaml files

    Returns:
        Merged dictionary of routes

    Raises:
        RouteConflictError: If same route name appears in multiple files
    """
    route_dicts = []
    sources = []

    for path in paths:
        routes = load_routes_file(path)
        if routes:
            route_dicts.append(routes)
            sources.append(str(path))

    return merge_routes_dicts(route_dicts, sources)


def discover_plugin_routes(plugins_dir: Path) -> list[Path]:
    """Find all tool-routes.yaml files in plugin directories.

    Args:
        plugins_dir: Path to plugins directory

    Returns:
        List of paths to tool-routes.yaml files
    """
    if not plugins_dir.exists():
        return []

    paths = []

    # Plugin-level routes: plugins/*/hooks/tool-routes.yaml
    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        routes_file = plugin_dir / "hooks" / "tool-routes.yaml"
        if routes_file.exists():
            paths.append(routes_file)

    # Skill-level routes: plugins/*/skills/*/tool-routes.yaml
    for routes_file in plugins_dir.glob("*/skills/*/tool-routes.yaml"):
        paths.append(routes_file)

    return sorted(paths)  # Consistent ordering


def discover_project_routes(project_root: Path) -> Optional[Path]:
    """Find project-local tool-routes.yaml.

    Args:
        project_root: Path to project root

    Returns:
        Path to .claude/tool-routes.yaml if it exists, None otherwise
    """
    routes_file = project_root / ".claude" / "tool-routes.yaml"
    if routes_file.exists():
        return routes_file
    return None


def load_all_routes(plugins_dir: Path, project_root: Path) -> dict[str, Route]:
    """Load and merge routes from all sources.

    Order:
    1. Plugin-contributed routes (from plugins_dir/*/hooks/tool-routes.yaml)
    2. Project-local routes (from project_root/.claude/tool-routes.yaml)

    Args:
        plugins_dir: Path to plugins directory
        project_root: Path to project root

    Returns:
        Merged dictionary of all routes

    Raises:
        RouteConflictError: If same route name appears in multiple sources
    """
    paths = discover_plugin_routes(plugins_dir)

    project_routes = discover_project_routes(project_root)
    if project_routes:
        paths.append(project_routes)

    return merge_routes(paths)

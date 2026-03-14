"""Manifest-driven route discovery using Claude CLI."""

import json
import subprocess
from pathlib import Path


def get_enabled_plugins(project_path: str | None = None) -> list[dict]:
    """Get enabled plugins from Claude's perspective.

    Args:
        project_path: Current project path. If provided, filters local-scoped
                      plugins to only those enabled for this project.

    Returns:
        List of enabled plugin dicts with id, installPath, scope, etc.
    """
    result = subprocess.run(
        ["claude", "plugin", "list", "--json"],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        return []

    try:
        plugins = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    # Filter to enabled plugins
    enabled = []
    for plugin in plugins:
        if not plugin.get("enabled"):
            continue

        scope = plugin.get("scope")
        # Include user/managed scope always
        if scope in ("user", "managed"):
            enabled.append(plugin)
        # Include local scope only if it matches project
        elif scope == "local":
            if project_path is None or plugin.get("projectPath") == project_path:
                enabled.append(plugin)

    # Dedupe by installPath (same plugin can appear multiple times)
    seen = set()
    unique = []
    for plugin in enabled:
        path = plugin.get("installPath")
        if path and path not in seen:
            seen.add(path)
            unique.append(plugin)

    return unique


def discover_routes_from_manifests(plugins: list[dict]) -> list[Path]:
    """Find route files declared in each plugin's routes.json manifest.

    Args:
        plugins: List of plugin dicts with installPath

    Returns:
        List of paths to tool-routes.yaml files that exist
    """
    routes = []

    for plugin in plugins:
        install_path = Path(plugin["installPath"])
        manifest_path = install_path / ".claude-plugin" / "routes.json"

        if not manifest_path.exists():
            continue

        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for route_path in manifest.get("routes", []):
            full_path = install_path / route_path
            if full_path.exists():
                routes.append(full_path)

    return sorted(routes)


def discover_all_routes(project_path: str | None = None) -> list[Path]:
    """Discover all route files from enabled plugins and project-local sources.

    This is the main entry point for route discovery.

    Args:
        project_path: Current project path for filtering local-scoped plugins
                      and finding project-local routes

    Returns:
        List of paths to tool-routes.yaml files
    """
    # Plugin routes
    plugins = get_enabled_plugins(project_path)
    routes = discover_routes_from_manifests(plugins)

    # Project-local routes (.claude/tool-routes.yaml)
    if project_path:
        local_routes = Path(project_path) / ".claude" / "tool-routes.yaml"
        if local_routes.exists():
            routes.append(local_routes)

    return sorted(routes)

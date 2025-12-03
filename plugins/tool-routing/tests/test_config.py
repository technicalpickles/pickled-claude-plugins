
import pytest

from tool_routing.config import (
    Route,
    RouteConflictError,
    discover_plugin_routes,
    discover_project_routes,
    load_routes_file,
    merge_routes,
    merge_routes_dicts,
)


def test_load_routes_file_basic(tmp_path):
    """Load a simple routes file."""
    routes_file = tmp_path / "tool-routes.yaml"
    routes_file.write_text("""
routes:
  test-route:
    tool: WebFetch
    pattern: "example\\\\.com"
    message: "Use something else"
""")

    routes = load_routes_file(routes_file)

    assert len(routes) == 1
    assert "test-route" in routes
    assert routes["test-route"].tool == "WebFetch"
    assert routes["test-route"].pattern == "example\\.com"
    assert routes["test-route"].message == "Use something else"


def test_load_routes_file_not_found(tmp_path):
    """Missing file returns empty dict."""
    routes = load_routes_file(tmp_path / "nonexistent.yaml")
    assert routes == {}


def test_load_routes_file_invalid_yaml(tmp_path):
    """Invalid YAML returns empty dict (fail open)."""
    routes_file = tmp_path / "tool-routes.yaml"
    routes_file.write_text("not: valid: yaml: {{{{")

    routes = load_routes_file(routes_file)
    assert routes == {}


def test_merge_routes_no_conflict(tmp_path):
    """Merge routes from multiple files without conflicts."""
    file1 = tmp_path / "routes1.yaml"
    file1.write_text("""
routes:
  route-a:
    tool: WebFetch
    pattern: "a\\\\.com"
    message: "Use A"
""")

    file2 = tmp_path / "routes2.yaml"
    file2.write_text("""
routes:
  route-b:
    tool: Bash
    pattern: "^command-b"
    message: "Use B"
""")

    merged = merge_routes([file1, file2])

    assert len(merged) == 2
    assert "route-a" in merged
    assert "route-b" in merged


def test_merge_routes_conflict_raises():
    """Duplicate route names raise RouteConflictError."""
    routes1 = {"same-name": Route(tool="WebFetch", pattern="a", message="A")}
    routes2 = {"same-name": Route(tool="Bash", pattern="b", message="B")}

    with pytest.raises(RouteConflictError) as exc_info:
        merge_routes_dicts([routes1, routes2], ["file1.yaml", "file2.yaml"])

    assert "same-name" in str(exc_info.value)
    assert "file1.yaml" in str(exc_info.value)
    assert "file2.yaml" in str(exc_info.value)


def test_discover_routes_from_plugins(tmp_path, monkeypatch):
    """Discover tool-routes.yaml from plugin directories."""
    # Create fake plugin structure
    plugin1 = tmp_path / "plugins" / "plugin-a" / "hooks"
    plugin1.mkdir(parents=True)
    (plugin1 / "tool-routes.yaml").write_text("""
routes:
  from-plugin-a:
    tool: WebFetch
    pattern: "plugin-a"
    message: "From A"
""")

    plugin2 = tmp_path / "plugins" / "plugin-b" / "hooks"
    plugin2.mkdir(parents=True)
    (plugin2 / "tool-routes.yaml").write_text("""
routes:
  from-plugin-b:
    tool: Bash
    pattern: "plugin-b"
    message: "From B"
""")

    # Plugin without routes
    plugin3 = tmp_path / "plugins" / "plugin-c"
    plugin3.mkdir(parents=True)

    paths = discover_plugin_routes(tmp_path / "plugins")

    assert len(paths) == 2
    assert any("plugin-a" in str(p) for p in paths)
    assert any("plugin-b" in str(p) for p in paths)


def test_discover_project_routes(tmp_path):
    """Discover project-local tool-routes.yaml."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "tool-routes.yaml").write_text("""
routes:
  project-route:
    tool: WebFetch
    pattern: "project"
    message: "Project route"
""")

    path = discover_project_routes(tmp_path)

    assert path is not None
    assert ".claude" in str(path)


def test_discover_project_routes_missing(tmp_path):
    """No project routes returns None."""
    path = discover_project_routes(tmp_path)
    assert path is None

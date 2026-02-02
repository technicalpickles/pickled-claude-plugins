import pytest

from tool_routing.config import (
    Route,
    RouteConflictError,
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

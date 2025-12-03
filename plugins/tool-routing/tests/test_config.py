from tool_routing.config import load_routes_file


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

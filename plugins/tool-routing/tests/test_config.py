
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


def test_discover_routes_from_installed_plugins(tmp_path):
    """Discover routes from installed plugin structure with version directories."""
    # Installed structure: plugins/plugin-name/VERSION/hooks/tool-routes.yaml
    plugin1 = tmp_path / "plugins" / "plugin-a" / "1.0.0" / "hooks"
    plugin1.mkdir(parents=True)
    (plugin1 / "tool-routes.yaml").write_text("""
routes:
  from-installed-a:
    tool: WebFetch
    pattern: "installed-a"
    message: "From installed A"
""")

    plugin2 = tmp_path / "plugins" / "plugin-b" / "2.3.4" / "hooks"
    plugin2.mkdir(parents=True)
    (plugin2 / "tool-routes.yaml").write_text("""
routes:
  from-installed-b:
    tool: Bash
    pattern: "installed-b"
    message: "From installed B"
""")

    # Plugin with git hash version
    plugin3 = tmp_path / "plugins" / "plugin-c" / "abc123def" / "hooks"
    plugin3.mkdir(parents=True)
    (plugin3 / "tool-routes.yaml").write_text("""
routes:
  from-installed-c:
    tool: WebFetch
    pattern: "installed-c"
    message: "From installed C"
""")

    paths = discover_plugin_routes(tmp_path / "plugins")

    assert len(paths) == 3
    assert any("plugin-a" in str(p) and "1.0.0" in str(p) for p in paths)
    assert any("plugin-b" in str(p) and "2.3.4" in str(p) for p in paths)
    assert any("plugin-c" in str(p) and "abc123def" in str(p) for p in paths)


def test_discover_routes_mixed_layouts(tmp_path):
    """Discover routes from both development and installed layouts."""
    # Development layout: plugins/plugin-name/hooks/tool-routes.yaml
    dev_plugin = tmp_path / "plugins" / "dev-plugin" / "hooks"
    dev_plugin.mkdir(parents=True)
    (dev_plugin / "tool-routes.yaml").write_text("""
routes:
  dev-route:
    tool: WebFetch
    pattern: "dev"
    message: "From dev"
""")

    # Installed layout: plugins/plugin-name/VERSION/hooks/tool-routes.yaml
    installed_plugin = tmp_path / "plugins" / "installed-plugin" / "1.0.0" / "hooks"
    installed_plugin.mkdir(parents=True)
    (installed_plugin / "tool-routes.yaml").write_text("""
routes:
  installed-route:
    tool: Bash
    pattern: "installed"
    message: "From installed"
""")

    paths = discover_plugin_routes(tmp_path / "plugins")

    assert len(paths) == 2
    assert any("dev-plugin" in str(p) for p in paths)
    assert any("installed-plugin" in str(p) and "1.0.0" in str(p) for p in paths)


def test_discover_skill_routes_installed_layout(tmp_path):
    """Discover skill-level routes from installed plugin structure."""
    # Installed skill routes: plugins/plugin-name/VERSION/skills/skill-name/tool-routes.yaml
    skill_dir = tmp_path / "plugins" / "my-plugin" / "1.0.0" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "tool-routes.yaml").write_text("""
routes:
  skill-route:
    tool: WebFetch
    pattern: "skill"
    message: "From skill"
""")

    paths = discover_plugin_routes(tmp_path / "plugins")

    assert len(paths) == 1
    assert "skills" in str(paths[0])
    assert "my-skill" in str(paths[0])


def test_discover_craftdesk_routes_finds_routes_in_skills_dir(tmp_path):
    """Test that craftdesk-installed skills' routes are discovered."""
    # Create .claude/skills structure
    skills_dir = tmp_path / ".claude" / "skills"
    skill_a = skills_dir / "skill-a" / "hooks"
    skill_b = skills_dir / "skill-b" / "hooks"
    skill_a.mkdir(parents=True)
    skill_b.mkdir(parents=True)

    # Create route files
    (skill_a / "tool-routes.yaml").write_text("routes: []")
    (skill_b / "tool-routes.yaml").write_text("routes: []")

    # Skill without routes
    (skills_dir / "skill-c").mkdir()

    from tool_routing.config import discover_craftdesk_routes
    paths = discover_craftdesk_routes(tmp_path)

    assert len(paths) == 2
    assert skill_a / "tool-routes.yaml" in paths
    assert skill_b / "tool-routes.yaml" in paths


def test_discover_craftdesk_routes_returns_empty_when_no_skills_dir(tmp_path):
    """Test that missing .claude/skills returns empty list."""
    from tool_routing.config import discover_craftdesk_routes
    paths = discover_craftdesk_routes(tmp_path)
    assert paths == []

"""Tests for new manifest-driven route discovery."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def test_get_enabled_plugins_parses_claude_output():
    """get_enabled_plugins parses claude plugin list output."""
    from tool_routing.discovery import get_enabled_plugins

    mock_output = json.dumps([
        {
            "id": "git@marketplace",
            "enabled": True,
            "scope": "user",
            "installPath": "/path/to/git"
        },
        {
            "id": "disabled@marketplace",
            "enabled": False,
            "scope": "user",
            "installPath": "/path/to/disabled"
        }
    ])

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        plugins = get_enabled_plugins()

    assert len(plugins) == 1
    assert plugins[0]["id"] == "git@marketplace"


def test_discover_routes_from_manifests_reads_routes_json(tmp_path):
    """discover_routes_from_manifests reads routes.json from each plugin."""
    from tool_routing.discovery import discover_routes_from_manifests

    # Create mock plugin with routes.json
    plugin_path = tmp_path / "git"
    plugin_path.mkdir()
    (plugin_path / ".claude-plugin").mkdir()
    (plugin_path / ".claude-plugin" / "routes.json").write_text(json.dumps({
        "routes": ["./skills/pr/tool-routes.yaml"]
    }))
    (plugin_path / "skills" / "pr").mkdir(parents=True)
    (plugin_path / "skills" / "pr" / "tool-routes.yaml").write_text("routes: {}")

    plugins = [{"installPath": str(plugin_path)}]
    paths = discover_routes_from_manifests(plugins)

    assert len(paths) == 1
    assert paths[0] == plugin_path / "skills" / "pr" / "tool-routes.yaml"


def test_discover_all_routes_combines_cli_and_manifests(tmp_path):
    """discover_all_routes uses Claude CLI + manifest reading."""
    from tool_routing.discovery import discover_all_routes

    # Create mock plugin
    plugin_path = tmp_path / "test-plugin"
    plugin_path.mkdir()
    (plugin_path / ".claude-plugin").mkdir()
    (plugin_path / ".claude-plugin" / "routes.json").write_text(json.dumps({
        "routes": ["./hooks/tool-routes.yaml"]
    }))
    (plugin_path / "hooks").mkdir()
    (plugin_path / "hooks" / "tool-routes.yaml").write_text("""
routes:
  test-route:
    tool: Bash
    pattern: "test"
    message: "Test message"
""")

    mock_output = json.dumps([{
        "id": "test-plugin@test",
        "enabled": True,
        "scope": "user",
        "installPath": str(plugin_path)
    }])

    with patch("tool_routing.discovery.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        paths = discover_all_routes()

    assert len(paths) == 1
    assert "tool-routes.yaml" in str(paths[0])

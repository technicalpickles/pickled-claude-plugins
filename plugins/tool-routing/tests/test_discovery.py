import os
import subprocess
import sys
from pathlib import Path


def test_discovers_skill_level_routes(tmp_path, monkeypatch):
    """Routes in plugins/*/skills/*/tool-routes.yaml are discovered."""
    # Create skill-level route file
    skill_routes = tmp_path / "plugins" / "test-plugin" / "skills" / "test-skill"
    skill_routes.mkdir(parents=True)
    (skill_routes / "tool-routes.yaml").write_text("""
routes:
  skill-route:
    tool: Bash
    pattern: "skill-pattern"
    message: "Skill route message"
""")

    monkeypatch.setenv("CLAUDE_PLUGINS_DIR", str(tmp_path / "plugins"))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / "tool-routing"))

    from tool_routing.config import discover_plugin_routes, merge_routes
    paths = discover_plugin_routes(tmp_path / "plugins")
    routes = merge_routes(paths)

    assert "skill-route" in routes
    assert routes["skill-route"].tool == "Bash"
    assert "skills/test-skill" in routes["skill-route"].source


def test_cli_merges_multiple_sources(tmp_path):
    """CLI merges routes from plugin and project sources."""
    # Plugin routes
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  plugin-route:
    tool: WebFetch
    pattern: "plugin\\\\.com"
    message: "From plugin"
""")

    # Simulate another plugin's routes
    other_plugin = tmp_path / "other-plugins" / "other" / "hooks"
    other_plugin.mkdir(parents=True)
    (other_plugin / "tool-routes.yaml").write_text("""
routes:
  other-plugin-route:
    tool: Bash
    pattern: "^other-command"
    message: "From other plugin"
""")

    # Project routes
    claude_dir = tmp_path / "project" / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "tool-routes.yaml").write_text("""
routes:
  project-route:
    tool: WebFetch
    pattern: "project\\\\.com"
    message: "From project"
""")

    src_path = Path(__file__).parent.parent / "src"
    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "list"],
        capture_output=True,
        text=True,
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "CLAUDE_PLUGINS_DIR": str(tmp_path / "other-plugins"),
            "CLAUDE_PROJECT_ROOT": str(tmp_path / "project"),
            "PYTHONPATH": str(src_path),
            "PATH": os.environ.get("PATH", ""),
        },
    )

    assert result.returncode == 0
    assert "plugin-route" in result.stdout
    assert "other-plugin-route" in result.stdout
    assert "project-route" in result.stdout

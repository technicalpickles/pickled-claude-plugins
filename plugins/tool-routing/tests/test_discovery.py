import subprocess
import sys


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

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "list"],
        capture_output=True,
        text=True,
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "CLAUDE_PLUGINS_DIR": str(tmp_path / "other-plugins"),
            "CLAUDE_PROJECT_ROOT": str(tmp_path / "project"),
            "PATH": "",
        },
    )

    assert result.returncode == 0
    assert "plugin-route" in result.stdout
    assert "other-plugin-route" in result.stdout
    assert "project-route" in result.stdout

"""Validate plugin structure matches Claude Code's expected format."""

import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


class TestPluginManifest:
    """Validate .claude-plugin/plugin.json exists and has required fields."""

    def test_manifest_exists(self):
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        assert manifest_path.exists(), (
            f"Missing plugin manifest at {manifest_path}"
        )

    def test_manifest_is_valid_json(self):
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        data = json.loads(manifest_path.read_text())
        assert isinstance(data, dict)

    def test_manifest_has_required_fields(self):
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        data = json.loads(manifest_path.read_text())
        assert "name" in data
        assert "description" in data
        assert data["name"] == "actually-lsp"

    def test_manifest_has_no_version_field(self):
        """Versions live in marketplace.json, not plugin.json."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        data = json.loads(manifest_path.read_text())
        assert "version" not in data, (
            "plugin.json must NOT include version (lives in marketplace.json)"
        )


class TestHooksJson:
    """Validate hooks.json exists and has SessionStart registered."""

    def test_hooks_json_exists(self):
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        assert hooks_path.exists()

    def test_hooks_json_is_valid_json(self):
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        assert "hooks" in data

    def test_session_start_hook_registered(self):
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        ss = data["hooks"].get("SessionStart")
        assert ss, "SessionStart hook must be registered"
        assert len(ss) == 1
        cmd = ss[0]["hooks"][0]["command"]
        assert "${CLAUDE_PLUGIN_ROOT}" in cmd
        assert "session-start.sh" in cmd


class TestSkills:
    """Validate skill files exist with required frontmatter.

    Skills are user-invocable via `/<skill-name>`. The skill `name` field
    must be globally unique (Claude Code surfaces skills by their bare
    slug, not by `plugin:name`), so the names here are prefixed with the
    plugin name to avoid colliding with other plugins' `doctor` or
    `ignore` skills. They replace the old `commands/<name>.md` pattern,
    which Claude Code no longer surfaces for plugins.
    """

    def test_doctor_skill_exists(self):
        path = PLUGIN_ROOT / "skills" / "actually-lsp-doctor" / "SKILL.md"
        assert path.exists(), f"Missing skill at {path}"
        content = path.read_text()
        assert "name: actually-lsp-doctor" in content
        assert "description:" in content

    def test_ignore_skill_exists(self):
        path = PLUGIN_ROOT / "skills" / "actually-lsp-ignore" / "SKILL.md"
        assert path.exists(), f"Missing skill at {path}"
        content = path.read_text()
        assert "name: actually-lsp-ignore" in content
        assert "description:" in content

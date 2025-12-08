"""Tests to validate plugin structure matches Claude Code's expected format."""

import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


class TestPluginManifest:
    """Validate .claude-plugin/plugin.json exists and has required fields."""

    def test_manifest_exists(self):
        """Plugin manifest must exist."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        assert manifest_path.exists(), (
            f"Missing plugin manifest at {manifest_path}. "
            "Create .claude-plugin/plugin.json with at least a 'name' field."
        )

    def test_manifest_is_valid_json(self):
        """Plugin manifest must be valid JSON."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            pytest.skip("Manifest doesn't exist (covered by other test)")

        content = manifest_path.read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in plugin.json: {e}")

    def test_manifest_has_required_fields(self):
        """Plugin manifest must have required 'name' field."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            pytest.skip("Manifest doesn't exist (covered by other test)")

        manifest = json.loads(manifest_path.read_text())

        assert "name" in manifest, "Plugin manifest must have 'name' field"
        assert isinstance(manifest["name"], str), "'name' must be a string"
        assert len(manifest["name"]) > 0, "'name' must not be empty"

    def test_manifest_name_matches_directory(self):
        """Plugin name should match directory name for consistency."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            pytest.skip("Manifest doesn't exist (covered by other test)")

        manifest = json.loads(manifest_path.read_text())
        expected_name = PLUGIN_ROOT.name

        assert manifest.get("name") == expected_name, (
            f"Plugin name '{manifest.get('name')}' doesn't match "
            f"directory name '{expected_name}'"
        )

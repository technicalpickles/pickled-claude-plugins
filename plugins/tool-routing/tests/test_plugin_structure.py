"""Tests to validate the plugin structure matches Claude Code's expected format.

These tests ensure the plugin will be correctly loaded by Claude Code,
catching issues like:
- Missing manifest files
- Invalid hooks.json format
- Incorrect field names or types
"""

import json
from pathlib import Path

import pytest

# Path to the plugin root (two levels up from tests/)
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


class TestHooksJson:
    """Validate hooks/hooks.json format matches Claude Code's expected structure.

    Claude Code hooks have a specific format:
    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "ToolName|OtherTool",
            "hooks": [
              {
                "type": "command",
                "command": "..."
              }
            ]
          }
        ]
      }
    }

    Common mistakes:
    - Using "hooks": [...] (array) instead of "hooks": {...} (object keyed by event)
    - Using {"tool_name": "X"} for matcher instead of string pattern
    - Using "type": "preToolUse" instead of "type": "command"
    """

    VALID_HOOK_EVENTS = {
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "Notification",
        "Stop",
        "SubagentStop",
        "SessionStart",
        "SessionEnd",
        "PreCompact",
    }

    VALID_HOOK_TYPES = {"command"}

    def test_hooks_json_exists(self):
        """hooks/hooks.json should exist if plugin provides hooks."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        # This plugin is specifically for hooks, so it must exist
        assert hooks_path.exists(), (
            f"Missing hooks.json at {hooks_path}. "
            "Plugin hooks must be defined in hooks/hooks.json"
        )

    def test_hooks_json_is_valid_json(self):
        """hooks.json must be valid JSON."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        content = hooks_path.read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in hooks.json: {e}")

    def test_hooks_top_level_structure(self):
        """Top-level 'hooks' must be an object keyed by event name, not an array."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())

        assert "hooks" in data, "hooks.json must have a 'hooks' key"

        hooks = data["hooks"]
        assert isinstance(hooks, dict), (
            "hooks must be an object keyed by event name (e.g., 'PreToolUse'), "
            f"not {type(hooks).__name__}. "
            "Wrong: \"hooks\": [...]. "
            "Right: \"hooks\": {\"PreToolUse\": [...]}"
        )

    def test_hooks_event_names_are_valid(self):
        """Hook event names must be valid Claude Code events."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid (covered by other test)")

        for event_name in hooks.keys():
            assert event_name in self.VALID_HOOK_EVENTS, (
                f"Invalid hook event '{event_name}'. "
                f"Valid events: {sorted(self.VALID_HOOK_EVENTS)}"
            )

    def test_hooks_matcher_is_string_pattern(self):
        """Matcher must be a string pattern, not an object."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid (covered by other test)")

        for event_name, event_hooks in hooks.items():
            if not isinstance(event_hooks, list):
                pytest.fail(f"hooks['{event_name}'] must be an array")

            for i, hook_entry in enumerate(event_hooks):
                if "matcher" in hook_entry:
                    matcher = hook_entry["matcher"]
                    assert isinstance(matcher, str), (
                        f"hooks['{event_name}'][{i}].matcher must be a string pattern, "
                        f"not {type(matcher).__name__}. "
                        "Wrong: {\"matcher\": {\"tool_name\": \"WebFetch\"}}. "
                        "Right: {\"matcher\": \"WebFetch\"} or {\"matcher\": \"WebFetch|Bash\"}"
                    )

    def test_hooks_type_is_command(self):
        """Hook type must be 'command', not event names like 'preToolUse'."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid (covered by other test)")

        for event_name, event_hooks in hooks.items():
            if not isinstance(event_hooks, list):
                continue

            for i, hook_entry in enumerate(event_hooks):
                inner_hooks = hook_entry.get("hooks", [])
                if not isinstance(inner_hooks, list):
                    continue

                for j, inner_hook in enumerate(inner_hooks):
                    if "type" in inner_hook:
                        hook_type = inner_hook["type"]
                        assert hook_type in self.VALID_HOOK_TYPES, (
                            f"hooks['{event_name}'][{i}].hooks[{j}].type must be "
                            f"one of {self.VALID_HOOK_TYPES}, not '{hook_type}'. "
                            "Wrong: \"type\": \"preToolUse\". "
                            "Right: \"type\": \"command\""
                        )

    def test_hooks_command_uses_plugin_root_variable(self):
        """Hook commands should use ${CLAUDE_PLUGIN_ROOT} for paths."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid (covered by other test)")

        for event_name, event_hooks in hooks.items():
            if not isinstance(event_hooks, list):
                continue

            for i, hook_entry in enumerate(event_hooks):
                inner_hooks = hook_entry.get("hooks", [])
                if not isinstance(inner_hooks, list):
                    continue

                for j, inner_hook in enumerate(inner_hooks):
                    command = inner_hook.get("command", "")
                    # Check for $CLAUDE_PLUGIN_ROOT without braces
                    if "$CLAUDE_PLUGIN_ROOT" in command and "${CLAUDE_PLUGIN_ROOT}" not in command:
                        pytest.fail(
                            f"hooks['{event_name}'][{i}].hooks[{j}].command uses "
                            "$CLAUDE_PLUGIN_ROOT without braces. "
                            "Use ${CLAUDE_PLUGIN_ROOT} for reliable expansion."
                        )


class TestToolRoutesYaml:
    """Validate hooks/tool-routes.yaml exists and is valid."""

    def test_tool_routes_exists(self):
        """tool-routes.yaml should exist for this plugin."""
        routes_path = PLUGIN_ROOT / "hooks" / "tool-routes.yaml"
        assert routes_path.exists(), (
            f"Missing tool-routes.yaml at {routes_path}. "
            "This plugin needs route definitions."
        )

    def test_tool_routes_has_routes(self):
        """tool-routes.yaml should define at least one route."""
        routes_path = PLUGIN_ROOT / "hooks" / "tool-routes.yaml"
        if not routes_path.exists():
            pytest.skip("tool-routes.yaml doesn't exist")

        import yaml

        data = yaml.safe_load(routes_path.read_text())

        assert data is not None, "tool-routes.yaml is empty"
        assert "routes" in data, "tool-routes.yaml must have 'routes' key"
        assert len(data["routes"]) > 0, "tool-routes.yaml must define at least one route"

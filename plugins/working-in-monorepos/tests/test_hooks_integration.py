"""Integration tests that run hooks like Claude Code does."""

import json
import os
import subprocess
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


class TestSessionStartHook:
    """Integration tests for the SessionStart hook script."""

    def get_hook_script_path(self) -> Path | None:
        """Extract script path from hooks.json."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            return None

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})
        session_start = hooks.get("SessionStart", [])

        if not session_start:
            return None

        for hook_entry in session_start:
            inner_hooks = hook_entry.get("hooks", [])
            for inner_hook in inner_hooks:
                command = inner_hook.get("command", "")
                # Replace ${CLAUDE_PLUGIN_ROOT} with actual path
                if "${CLAUDE_PLUGIN_ROOT}" in command:
                    command = command.replace(
                        "${CLAUDE_PLUGIN_ROOT}",
                        str(PLUGIN_ROOT)
                    )
                if command.endswith(".sh"):
                    return Path(command)

        return None

    def test_hook_script_exists(self):
        """Script referenced in hooks.json must exist."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")

        assert script_path.exists(), (
            f"Hook script does not exist: {script_path}"
        )

    def test_hook_script_is_executable(self):
        """Script must be executable."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist (covered by other test)")

        assert os.access(script_path, os.X_OK), (
            f"Hook script is not executable: {script_path}. "
            f"Run: chmod +x {script_path}"
        )

    def test_hook_script_has_shebang(self):
        """Script must have a valid shebang line."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        content = script_path.read_text()
        first_line = content.split("\n")[0] if content else ""

        assert first_line.startswith("#!"), (
            f"Hook script missing shebang: {script_path}. "
            "First line should be #!/usr/bin/env bash or similar"
        )

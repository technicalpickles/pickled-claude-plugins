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

    def test_hook_handles_stdin_json(self):
        """Hook must handle JSON stdin without errors.

        Claude Code passes session data as JSON on stdin.
        The hook should consume or ignore it, not fail.
        """
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        # Simulate Claude Code's stdin format
        stdin_data = json.dumps({
            "session_id": "test-session-123",
            "cwd": "/tmp/test-project",
            "timestamp": "2025-12-08T12:00:00Z"
        })

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/tmp"  # Run outside git repo
        )

        # Should exit 0 (success) even if it can't detect a monorepo
        assert result.returncode == 0, (
            f"Hook failed with stdin. Exit code: {result.returncode}\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

        # Should not have error messages about parsing stdin
        assert "command not found" not in result.stderr, (
            "Hook is interpreting stdin as commands. "
            "Ensure script consumes stdin with 'cat > /dev/null' or similar."
        )

    def test_hook_succeeds_outside_git_repo(self, tmp_path):
        """Hook should exit cleanly when not in a git repo."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        stdin_data = json.dumps({"session_id": "test"})

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0, (
            f"Hook should exit 0 outside git repo. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_hook_succeeds_in_git_repo_without_monorepo(self, tmp_path):
        """Hook should work in a git repo without .monorepo.json."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        # Create a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        stdin_data = json.dumps({"session_id": "test"})

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0, (
            f"Hook failed in git repo. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_hook_detects_monorepo_config(self, tmp_path):
        """Hook should detect existing .monorepo.json."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        # Create a git repo with .monorepo.json
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        monorepo_config = tmp_path / ".monorepo.json"
        monorepo_config.write_text(json.dumps({
            "subprojects": [
                {"name": "frontend", "path": "frontend"},
                {"name": "backend", "path": "backend"}
            ]
        }))

        stdin_data = json.dumps({"session_id": "test"})

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0, (
            f"Hook failed with .monorepo.json. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

        # Should mention detecting the monorepo
        assert "monorepo" in result.stdout.lower() or "subproject" in result.stdout.lower(), (
            f"Hook should report detecting monorepo. stdout: {result.stdout}"
        )

import json
import os
import subprocess
import sys


def run_cli(subcommand: str, stdin_data: dict) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": "src"}
    return subprocess.run(
        [sys.executable, "-m", "sandbox_first.cli", subcommand],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        env=env,
    )


class TestPreToolUseCLI:
    def test_sandboxed_call_exits_0_no_output(self):
        result = run_cli("pre-tool-use", {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
            "transcript_path": "/nonexistent",
        })
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_unsandboxed_call_exits_0_with_deny_json(self):
        result = run_cli("pre-tool-use", {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hi",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        })
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_invalid_json_exits_0(self):
        """Fail open on bad input."""
        env = {**os.environ, "PYTHONPATH": "src"}
        result = subprocess.run(
            [sys.executable, "-m", "sandbox_first.cli", "pre-tool-use"],
            input="not json",
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0


class TestPostToolUseFailureCLI:
    def test_sandboxed_failure_exits_0_with_context(self):
        result = run_cli("post-tool-use-failure", {
            "tool_name": "Bash",
            "tool_input": {"command": "curl https://x.com"},
            "error": "Operation not permitted",
        })
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "additionalContext" in output["hookSpecificOutput"]

    def test_unsandboxed_failure_exits_0_no_output(self):
        result = run_cli("post-tool-use-failure", {
            "tool_name": "Bash",
            "tool_input": {
                "command": "curl https://x.com",
                "dangerouslyDisableSandbox": True,
            },
            "error": "Connection refused",
        })
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_non_sandbox_error_on_sandboxed_call_exits_0_no_output(self):
        """Regression: sandboxed Bash failure with non-sandbox error stays silent."""
        result = run_cli("post-tool-use-failure", {
            "tool_name": "Bash",
            "tool_input": {"command": "ls plugins/nonexistent/"},
            "error": "ls: cannot access 'plugins/nonexistent/': No such file or directory",
        })
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_unknown_subcommand_exits_0(self):
        result = run_cli("unknown-thing", {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
        })
        assert result.returncode == 0


class TestPreToolUseWithConfig:
    def test_configured_command_allowed(self, tmp_path):
        """CLI allows configured command without prior failure."""
        # Put config at $HOME/.claude/sandbox-first.json
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        user_config = claude_dir / "sandbox-first.json"
        user_config.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        env = {**os.environ, "PYTHONPATH": "src", "HOME": str(tmp_path)}

        result = subprocess.run(
            [sys.executable, "-m", "sandbox_first.cli", "pre-tool-use"],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {
                    "command": "docker build .",
                    "dangerouslyDisableSandbox": True,
                },
                "transcript_path": "/nonexistent",
            }),
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_claude_config_dir_takes_precedence(self, tmp_path):
        """CLAUDE_CONFIG_DIR is preferred over $HOME/.claude/."""
        custom_dir = tmp_path / "custom-config"
        custom_dir.mkdir()
        config = custom_dir / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        env = {
            **os.environ,
            "PYTHONPATH": "src",
            "HOME": str(tmp_path),
            "CLAUDE_CONFIG_DIR": str(custom_dir),
        }

        result = subprocess.run(
            [sys.executable, "-m", "sandbox_first.cli", "pre-tool-use"],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {
                    "command": "docker build .",
                    "dangerouslyDisableSandbox": True,
                },
                "transcript_path": "/nonexistent",
            }),
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_project_config_via_env(self, tmp_path):
        """CLAUDE_PROJECT_DIR config is loaded."""
        project_dir = tmp_path / "myproject"
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir(parents=True)
        config = claude_dir / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        env = {
            **os.environ,
            "PYTHONPATH": "src",
            "HOME": str(tmp_path),
            "CLAUDE_PROJECT_DIR": str(project_dir),
        }

        result = subprocess.run(
            [sys.executable, "-m", "sandbox_first.cli", "pre-tool-use"],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {
                    "command": "docker build .",
                    "dangerouslyDisableSandbox": True,
                },
                "transcript_path": "/nonexistent",
            }),
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

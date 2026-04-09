import json

from sandbox_plugin.checker import check_pre_tool_use, check_post_tool_use_failure


class TestCheckPreToolUse:
    def test_sandboxed_call_returns_none(self):
        """Sandboxed calls pass through."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hello"},
            "transcript_path": "/nonexistent",
        }
        assert check_pre_tool_use(hook_input) is None

    def test_unsandboxed_no_prior_failure_returns_deny(self):
        """Unsandboxed call with no prior sandboxed failure gets denied."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hello",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input)
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "sandbox" in result["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_unsandboxed_with_prior_failure_returns_none(self, tmp_path):
        """Unsandboxed call after a sandboxed failure is allowed."""
        transcript = tmp_path / "transcript.jsonl"
        entries = [
            {
                "message": {
                    "role": "assistant",
                    "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "echo hello"}}],
                }
            },
            {
                "message": {
                    "role": "user",
                    "content": [{"type": "tool_result", "is_error": True, "content": "Operation not permitted"}],
                }
            },
        ]
        transcript.write_text("\n".join(json.dumps(e) for e in entries))

        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hello",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": str(transcript),
        }
        assert check_pre_tool_use(hook_input) is None

    def test_non_bash_tool_returns_none(self):
        """Non-Bash tools pass through."""
        hook_input = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/x"},
            "transcript_path": "/nonexistent",
        }
        assert check_pre_tool_use(hook_input) is None


class TestCheckPostToolUseFailure:
    def test_sandboxed_failure_returns_context(self):
        """Sandboxed Bash failure returns additional context."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "touch /outside"},
            "error": "Exit code 1\ntouch: cannot touch '/outside': Operation not permitted",
        }
        result = check_post_tool_use_failure(hook_input)
        assert result is not None
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "sandbox" in ctx.lower()

    def test_unsandboxed_failure_returns_none(self):
        """Unsandboxed failures aren't sandbox-related, skip."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "touch /outside",
                "dangerouslyDisableSandbox": True,
            },
            "error": "Exit code 1\nsome error",
        }
        assert check_post_tool_use_failure(hook_input) is None

    def test_non_bash_returns_none(self):
        hook_input = {
            "tool_name": "Write",
            "tool_input": {},
            "error": "some error",
        }
        assert check_post_tool_use_failure(hook_input) is None

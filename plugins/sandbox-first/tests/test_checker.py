import json

import pytest

from sandbox_first.checker import check_pre_tool_use, check_post_tool_use_failure


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

    # Regression tests for task 34 (false positive findings): the hook
    # was flagging non-sandbox failures as sandbox-related, pushing the
    # model toward dangerouslyDisableSandbox unnecessarily. These cases
    # were witnessed in real sessions and must NOT be flagged.
    @pytest.mark.parametrize(
        "case,command,error",
        [
            (
                "ls-enoent",
                "ls plugins/nonexistent/",
                "Exit code 2\nls: cannot access 'plugins/nonexistent/': No such file or directory",
            ),
            (
                "git-config-write-warning",
                "git branch -D feature",
                "warning: unable to access '.git/config': some write warning",
            ),
            (
                "git-not-a-repo",
                "git worktree list",
                "fatal: not a git repository: .git/refs/remotes/",
            ),
            (
                "1password-ipc",
                "op-ssh-sign",
                "1Password IPC error: agent not running",
            ),
            (
                "command-not-found",
                "nonexistent-tool --help",
                "bash: nonexistent-tool: command not found",
            ),
            (
                "ruby-exception",
                "ruby script.rb",
                "script.rb:5:in `<main>': undefined method `foo' for nil:NilClass (NoMethodError)",
            ),
            (
                "test-assertion-failure",
                "pytest tests/",
                "AssertionError: expected 3 but got 4",
            ),
        ],
    )
    def test_non_sandbox_errors_return_none(self, case, command, error):
        """Sandboxed Bash failures with non-sandbox-shaped errors stay silent."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "error": error,
        }
        assert check_post_tool_use_failure(hook_input) is None, (
            f"case {case!r} should not be flagged as sandbox-related"
        )

    # Positive cases: errors that ARE sandbox-shaped should still get flagged.
    @pytest.mark.parametrize(
        "case,command,error",
        [
            (
                "fs-operation-not-permitted",
                "touch /outside",
                "touch: cannot touch '/outside': Operation not permitted",
            ),
            (
                "network-connection-refused",
                "curl http://blocked.example.com",
                "curl: (7) Failed to connect to blocked.example.com port 80: Connection refused",
            ),
            (
                "network-could-not-resolve",
                "curl https://blocked.example.com",
                "curl: (6) Could not resolve host: blocked.example.com",
            ),
            (
                "sandbox-exec-deny",
                "touch /etc/foo",
                "sandbox-exec: file-write-create /etc/foo deny",
            ),
            (
                "read-only-fs",
                "touch /usr/foo",
                "touch: /usr/foo: Read-only file system",
            ),
            (
                "mkdir-operation-not-permitted",
                "mkdir .vscode",
                "mkdir: cannot create directory '.vscode': Operation not permitted",
            ),
            (
                "mkdir-smart-quote-variant",
                "mkdir -p /tmp/outside/.git",
                "mkdir: \u2018/tmp/outside/.git\u2019: Operation not permitted",
            ),
            (
                "shell-eval-operation-not-permitted",
                "sh -c 'touch /path/.git/config'",
                "(eval):1: operation not permitted: /private/tmp/sandbox-clone-test/dotfiles-probe/.git/config",
            ),
            (
                "git-single-fatal-leading-dirs",
                "git worktree add ../outside-wt -b probe",
                "Preparing worktree (new branch 'probe')\nfatal: could not create leading directories of '../outside-wt/.git': Operation not permitted",
            ),
            (
                "git-single-fatal-copy-templates",
                "git clone /src /tmp/outside/dest",
                "fatal: cannot copy '/usr/share/git-core/templates/hooks/pre-commit.sample' to '/tmp/outside/dest/.git/hooks/pre-commit.sample': Operation not permitted",
            ),
            (
                "git-error-then-fatal-pair",
                "git clone /src /tmp/outside/dest",
                "error: could not write config file /tmp/outside/dest/.git/config: Operation not permitted\nfatal: could not set 'core.repositoryformatversion' to '0'",
            ),
        ],
    )
    def test_sandbox_shaped_errors_return_context(self, case, command, error):
        """Sandbox-shaped errors on sandboxed calls still get the warning."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "error": error,
        }
        result = check_post_tool_use_failure(hook_input)
        assert result is not None, f"case {case!r} should be flagged"
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "sandbox" in ctx.lower()

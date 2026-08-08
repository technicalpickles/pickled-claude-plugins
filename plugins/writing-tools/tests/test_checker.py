"""Tests for the em-dash checker."""

from writing_tools.checker import check_tool_call
from writing_tools.config import Config

EMDASH = "—"

SLACK_TOOL = "mcp__slackgustoofficialmcp__slack_send_message"


def cfg(mcp_tools=None, bash_commands=None):
    """Build a config-loader callable for a given Config."""
    config = Config(mcp_tools=mcp_tools or [], bash_commands=bash_commands or [])
    return lambda: config


def test_configured_mcp_tool_with_emdash_blocks():
    call = {
        "tool_name": SLACK_TOOL,
        "tool_input": {"text": f"hey {EMDASH} check this"},
    }
    result = check_tool_call(call, cfg(mcp_tools=[SLACK_TOOL]))
    assert result.blocked is True
    assert result.reason


def test_configured_mcp_tool_without_emdash_allows():
    call = {
        "tool_name": SLACK_TOOL,
        "tool_input": {"text": "hey, check this"},
    }
    result = check_tool_call(call, cfg(mcp_tools=[SLACK_TOOL]))
    assert result.blocked is False


def test_unconfigured_mcp_tool_with_emdash_allows():
    call = {
        "tool_name": "mcp__other__send",
        "tool_input": {"text": f"hey {EMDASH} there"},
    }
    result = check_tool_call(call, cfg(mcp_tools=[SLACK_TOOL]))
    assert result.blocked is False


def test_gh_pr_create_with_emdash_in_command_blocks():
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f'gh pr create --title "Fix {EMDASH} thing"'},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr create"]))
    assert result.blocked is True


def test_gh_pr_create_body_file_with_emdash_blocks(tmp_path):
    body = tmp_path / "body.md"
    body.write_text(f"This PR does a thing {EMDASH} and another thing.")
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f"gh pr create --title clean --body-file {body}"},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr create"]))
    assert result.blocked is True


def test_gh_pr_create_body_file_clean_allows(tmp_path):
    body = tmp_path / "body.md"
    body.write_text("This PR does a thing, and another thing.")
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f"gh pr create --title clean --body-file {body}"},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr create"]))
    assert result.blocked is False


def test_gh_pr_create_body_file_equals_form_blocks(tmp_path):
    body = tmp_path / "body.md"
    body.write_text(f"body with {EMDASH} dash")
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f"gh pr create --body-file={body}"},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr create"]))
    assert result.blocked is True


def test_non_gh_bash_with_emdash_allows():
    """My own cleanup commands must never be blocked."""
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f'grep "{EMDASH}" foo.md'},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr create"]))
    assert result.blocked is False


def test_perl_emdash_substitution_allows():
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f"perl -pi -e 's/{EMDASH}/: /g' notes.md"},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr create"]))
    assert result.blocked is False


def test_prefix_quoted_inside_argument_does_not_match():
    """A gated prefix appearing inside a quoted arg is not a real invocation."""
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f'grep "gh pr create" log.txt {EMDASH}x'},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr create"]))
    assert result.blocked is False


def test_gated_command_after_separator_matches():
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": f'cd repo && gh pr comment --body "wait {EMDASH} no"'},
    }
    result = check_tool_call(call, cfg(bash_commands=["gh pr comment"]))
    assert result.blocked is True


def test_empty_config_allows_everything():
    """Inert default: nothing opted in, nothing blocked."""
    call = {
        "tool_name": SLACK_TOOL,
        "tool_input": {"text": f"hey {EMDASH} there"},
    }
    result = check_tool_call(call, cfg())
    assert result.blocked is False


def test_write_tool_left_alone():
    call = {
        "tool_name": "Write",
        "tool_input": {"file_path": "/tmp/x.md", "content": f"doc with {EMDASH} dash"},
    }
    result = check_tool_call(call, cfg(mcp_tools=[SLACK_TOOL], bash_commands=["gh pr create"]))
    assert result.blocked is False


def test_emdash_escaped_in_json_still_detected():
    """ensure_ascii=False keeps the literal char, so nested dict values match."""
    call = {
        "tool_name": SLACK_TOOL,
        "tool_input": {"blocks": [{"type": "section", "text": f"nested {EMDASH} dash"}]},
    }
    result = check_tool_call(call, cfg(mcp_tools=[SLACK_TOOL]))
    assert result.blocked is True

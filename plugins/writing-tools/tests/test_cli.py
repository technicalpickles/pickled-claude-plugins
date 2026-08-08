"""End-to-end tests for the CLI hook entry point (subprocess)."""

import json
import subprocess
import sys
from pathlib import Path

EMDASH = "—"
SLACK_TOOL = "mcp__slackgustoofficialmcp__slack_send_message"


def run_check(payload: dict, cli_env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "writing_tools", "check"],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        env=cli_env,
    )


def write_config(cli_env: dict, contents: str) -> None:
    Path(cli_env["EMDASH_OUTBOUND_CONFIG"]).write_text(contents)


def test_blocks_configured_slack_send(cli_env):
    write_config(cli_env, f"mcpTools:\n  - {SLACK_TOOL}\n")
    payload = {"tool_name": SLACK_TOOL, "tool_input": {"text": f"hi {EMDASH} there"}}
    result = run_check(payload, cli_env)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"


def test_allows_clean_slack_send(cli_env):
    write_config(cli_env, f"mcpTools:\n  - {SLACK_TOOL}\n")
    payload = {"tool_name": SLACK_TOOL, "tool_input": {"text": "hi there"}}
    result = run_check(payload, cli_env)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_allows_when_config_empty(cli_env):
    write_config(cli_env, "mcpTools: []\nbashCommands: []\n")
    payload = {"tool_name": SLACK_TOOL, "tool_input": {"text": f"hi {EMDASH} there"}}
    result = run_check(payload, cli_env)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_blocks_gh_pr_create(cli_env):
    write_config(cli_env, "bashCommands:\n  - gh pr create\n")
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": f'gh pr create --title "x {EMDASH} y"'},
    }
    result = run_check(payload, cli_env)
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_allows_grep_cleanup(cli_env):
    write_config(cli_env, "bashCommands:\n  - gh pr create\n")
    payload = {"tool_name": "Bash", "tool_input": {"command": f'grep "{EMDASH}" f.md'}}
    result = run_check(payload, cli_env)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_malformed_stdin_fails_open(cli_env):
    result = subprocess.run(
        [sys.executable, "-m", "writing_tools", "check"],
        input="not json{{{",
        capture_output=True,
        text=True,
        env=cli_env,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""

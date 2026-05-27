"""Integration tests for the SessionStart hook script."""

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "session-start.sh"


def run_hook(project_dir, plugin_list_output='[]'):
    """Invoke session-start.sh with a fake CLAUDE_PROJECT_DIR and a fake `claude` command."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["CLAUDE_SESSION_ID"] = "test-session-id"
    env["ACTUALLY_LSP_SKIP_BINARY_CHECK"] = "1"

    # Stub `claude plugin list --json` via a fake bin dir on PATH
    fake_bin = project_dir / "_fake_bin"
    fake_bin.mkdir(exist_ok=True)
    fake_claude = fake_bin / "claude"
    fake_claude.write_text(
        f'#!/usr/bin/env bash\nif [[ "$1" == "plugin" && "$2" == "list" ]]; then\n  echo \'{plugin_list_output}\'\nfi\n'
    )
    fake_claude.chmod(0o755)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(HOOK)],
        input="{}",
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def test_hook_exists():
    assert HOOK.exists()


def test_hook_is_executable():
    assert os.access(HOOK, os.X_OK)


def test_hook_silent_when_no_ecosystem(tmp_path):
    """Empty project: no nudge, no activation context."""
    stdout, stderr, rc = run_hook(tmp_path)
    assert rc == 0
    assert stdout.strip() == ""


def test_hook_nudges_when_no_lsp_plugin(tmp_path):
    """TypeScript project with no LSP plugin installed: emit a nudge."""
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export const x = 1;")
    stdout, stderr, rc = run_hook(tmp_path, plugin_list_output='[]')
    assert rc == 0
    assert "typescript-lsp@claude-plugins-official" in stdout
    assert "/actually-lsp:doctor" in stdout


def test_hook_emits_activation_context_when_ready(tmp_path):
    """TypeScript project with LSP plugin + node_modules: emit activation context."""
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export const x = 1;")
    (tmp_path / "node_modules").mkdir()
    plugin_list = json.dumps([
        {"id": "typescript-lsp@claude-plugins-official", "enabled": True}
    ])
    stdout, stderr, rc = run_hook(tmp_path, plugin_list_output=plugin_list)
    assert rc == 0
    # Activation context contains the deferred-tool explanation
    assert "ToolSearch" in stdout
    assert "select:LSP" in stdout

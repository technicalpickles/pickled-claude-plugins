"""Structural invariants for the sandbox-advisor plugin."""
import json
import os
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent


def test_manifest_valid():
    manifest = json.loads(
        (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text()
    )
    assert manifest["name"] == "sandbox-advisor"
    assert manifest["description"]


def test_hooks_json_registers_posttooluse_failure_on_bash():
    hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text())
    entries = hooks["hooks"]["PostToolUseFailure"]
    assert entries, "expected a PostToolUseFailure entry"
    entry = entries[0]
    assert entry["matcher"] == "Bash"
    command = entry["hooks"][0]["command"]
    assert "advise.py" in command


def test_hook_script_exists_and_is_executable():
    script = PLUGIN_ROOT / "hooks" / "advise.py"
    assert script.exists(), f"missing hook script: {script}"
    assert os.access(script, os.X_OK), (
        f"hook not executable: run chmod +x {script}"
    )


def test_hook_script_has_shebang():
    script = PLUGIN_ROOT / "hooks" / "advise.py"
    first_line = script.read_text().splitlines()[0]
    assert first_line.startswith("#!"), "hook script needs a shebang"

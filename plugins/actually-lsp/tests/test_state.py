"""Verify state.sh's project state file read/write."""

import json
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
STATE_SH = PLUGIN_ROOT / "lib" / "state.sh"


def run_state(script_body, project_dir):
    """Source state.sh and run a script body. Return stdout, returncode."""
    full = f"source {STATE_SH} && PROJECT_DIR='{project_dir}' && {script_body}"
    result = subprocess.run(
        ["bash", "-c", full],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.returncode


def test_state_sh_exists():
    assert STATE_SH.exists()


def test_write_state_creates_file(tmp_path):
    output, rc = run_state(
        'write_state typescript ready false "$(date -u +%Y-%m-%dT%H:%M:%SZ)" 0 abc123 null',
        tmp_path,
    )
    assert rc == 0
    state_file = tmp_path / ".claude" / "actually-lsp.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["version"] == 1
    assert data["ecosystems"]["typescript"]["state"] == "ready"
    assert data["ecosystems"]["typescript"]["dismissed"] is False


def test_read_state_returns_empty_when_missing(tmp_path):
    output, rc = run_state("read_state typescript state", tmp_path)
    assert rc == 0
    assert output == ""


def test_read_state_returns_value(tmp_path):
    state_dir = tmp_path / ".claude"
    state_dir.mkdir()
    (state_dir / "actually-lsp.json").write_text(json.dumps({
        "version": 1,
        "ecosystems": {
            "typescript": {"state": "ready", "dismissed": False}
        }
    }))
    output, rc = run_state("read_state typescript state", tmp_path)
    assert rc == 0
    assert output == "ready"

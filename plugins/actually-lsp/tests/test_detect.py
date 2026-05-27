"""Verify detect.sh's detect_ecosystems function."""

import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
DETECT_SH = PLUGIN_ROOT / "lib" / "detect.sh"


def run_detect(project_dir):
    """Source ecosystems.sh and detect.sh, run detect_ecosystems, return stdout.

    Runs under `set -eo pipefail` to match hooks/session-start.sh semantics, so
    pipeline-related bugs surface at the unit layer instead of only in
    end-to-end hook tests.
    """
    script = (
        f"set -eo pipefail; "
        f"source {PLUGIN_ROOT}/lib/ecosystems.sh && "
        f"source {DETECT_SH} && "
        f"detect_ecosystems '{project_dir}'"
    )
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.returncode


def test_detect_sh_exists():
    assert DETECT_SH.exists()


def test_detect_returns_nothing_for_empty_dir(tmp_path):
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert output == ""


def test_detect_finds_typescript(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export const x = 1;")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    lines = output.split("\n")
    ts_lines = [l for l in lines if l.startswith("typescript|")]
    assert len(ts_lines) == 1


def _seed_large_ts_tree(root):
    """Seed a fixture whose .ts paths overflow the OS pipe buffer (~64KB).

    The regression here only fires once `find`'s accumulated output exceeds
    the pipe buffer, so the second write blocks → SIGPIPE once `head -1`
    closes its read end. We need:
    - .ts files within `find -maxdepth 4` (counted from root)
    - enough total output bytes to exceed the buffer (~64KB)
    """
    (root / "package.json").write_text("{}")
    for d in range(50):
        sub = root / f"dir{d}"
        sub.mkdir()
        for i in range(50):
            (sub / f"file_with_a_reasonably_long_name_{i}.ts").write_text("")


def test_detect_finds_typescript_in_large_tree(tmp_path):
    """Regression: a large .ts tree under pipefail tripped SIGPIPE.

    The old `find ... | head -1 | grep -q .` pattern caused `find` to receive
    SIGPIPE once `head` closed its pipe, which under `set -eo pipefail`
    flipped the existence check to false and silently dropped TypeScript
    detection in any real-world project (monorepos, anything with node_modules).
    """
    _seed_large_ts_tree(tmp_path)
    output, rc = run_detect(tmp_path)
    assert rc == 0, f"detect_ecosystems exited {rc}; output={output!r}"
    assert any(l.startswith("typescript|") for l in output.split("\n")), (
        f"typescript was dropped; output was {output!r}"
    )


def test_detect_skips_typescript_without_ts_files(tmp_path):
    """package.json without any .ts files is not a TypeScript project."""
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.js").write_text("module.exports = {};")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert "typescript|" not in output


def test_detect_finds_rust(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert any(l.startswith("rust|") for l in output.split("\n"))


def test_detect_finds_ruby(tmp_path):
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert any(l.startswith("ruby|") for l in output.split("\n"))


def test_detect_polyglot(tmp_path):
    """Project with all three markers: all three should be detected."""
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export {};")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    lines = output.split("\n")
    assert any(l.startswith("rust|") for l in lines)
    assert any(l.startswith("ruby|") for l in lines)
    assert any(l.startswith("typescript|") for l in lines)

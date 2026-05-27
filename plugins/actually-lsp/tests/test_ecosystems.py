"""Verify ecosystems.sh exposes the per-ecosystem data table."""

import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
ECOSYSTEMS_SH = PLUGIN_ROOT / "lib" / "ecosystems.sh"


def test_ecosystems_sh_exists():
    assert ECOSYSTEMS_SH.exists()


def test_ecosystems_sh_defines_typescript():
    """Sourcing ecosystems.sh should expose a 'typescript' row in $ecosystems."""
    result = subprocess.run(
        ["bash", "-c", f"source {ECOSYSTEMS_SH} && printf '%s\\n' \"${{ecosystems[@]}}\""],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split("\n")
    typescript_rows = [l for l in lines if l.startswith("typescript|")]
    assert len(typescript_rows) == 1
    fields = typescript_rows[0].split("|")
    assert fields[1] == "package.json"
    assert fields[2] == "typescript-lsp@claude-plugins-official"
    assert fields[3] == "typescript-language-server"


def test_ecosystems_sh_defines_rust():
    result = subprocess.run(
        ["bash", "-c", f"source {ECOSYSTEMS_SH} && printf '%s\\n' \"${{ecosystems[@]}}\""],
        capture_output=True, text=True, check=True,
    )
    rust_rows = [l for l in result.stdout.strip().split("\n") if l.startswith("rust|")]
    assert len(rust_rows) == 1
    fields = rust_rows[0].split("|")
    assert fields[1] == "Cargo.toml"
    assert fields[2] == "rust-analyzer-lsp@claude-plugins-official"
    assert fields[3] == "rust-analyzer"


def test_ecosystems_sh_defines_ruby():
    result = subprocess.run(
        ["bash", "-c", f"source {ECOSYSTEMS_SH} && printf '%s\\n' \"${{ecosystems[@]}}\""],
        capture_output=True, text=True, check=True,
    )
    ruby_rows = [l for l in result.stdout.strip().split("\n") if l.startswith("ruby|")]
    assert len(ruby_rows) == 1
    fields = ruby_rows[0].split("|")
    assert fields[1] == "Gemfile"
    assert fields[2] == "ruby-lsp@claude-plugins-official"
    assert fields[3] == "ruby-lsp"

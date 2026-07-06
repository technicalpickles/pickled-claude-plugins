"""Tests for config loading and discovery."""

import os

from writing_tools.config import Config, find_config_path, load_config, load_config_file


def test_missing_file_is_inert(tmp_path):
    config = load_config_file(tmp_path / "nope.yaml")
    assert config.is_empty()


def test_empty_lists_is_inert(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("mcpTools: []\nbashCommands: []\n")
    config = load_config_file(path)
    assert config.is_empty()


def test_loads_lists(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text(
        "mcpTools:\n  - mcp__slack__send\nbashCommands:\n  - gh pr create\n"
    )
    config = load_config_file(path)
    assert config.mcp_tools == ["mcp__slack__send"]
    assert config.bash_commands == ["gh pr create"]
    assert not config.is_empty()


def test_absent_keys_default_empty(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("# just a comment\n")
    config = load_config_file(path)
    assert config.is_empty()


def test_malformed_yaml_fails_open(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("mcpTools: [unterminated\n")
    config = load_config_file(path)
    assert config.is_empty()


def test_scalar_where_list_expected_fails_open(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("mcpTools: nope\nbashCommands: 5\n")
    config = load_config_file(path)
    assert config.is_empty()


def test_explicit_env_override_wins(tmp_path, monkeypatch):
    path = tmp_path / "explicit.yaml"
    path.write_text("mcpTools:\n  - mcp__x__y\n")
    monkeypatch.setenv("EMDASH_OUTBOUND_CONFIG", str(path))
    assert find_config_path() == path
    assert load_config().mcp_tools == ["mcp__x__y"]


def test_shipped_default_is_fallback_and_inert(monkeypatch):
    """With no overrides, discovery falls back to the shipped inert config."""
    monkeypatch.delenv("EMDASH_OUTBOUND_CONFIG", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    # Point HOME somewhere without a config so we fall through to shipped.
    monkeypatch.setenv("HOME", os.path.join(os.sep, "nonexistent-writing-tools-home"))
    path = find_config_path()
    assert path is not None
    assert path.name == "emdash-outbound.yaml"
    assert load_config_file(path).is_empty()


def test_config_dataclass_is_empty():
    assert Config().is_empty()
    assert not Config(mcp_tools=["x"]).is_empty()
    assert not Config(bash_commands=["y"]).is_empty()

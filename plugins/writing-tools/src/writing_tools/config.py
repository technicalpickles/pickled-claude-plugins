"""Configuration loading for em-dash outbound enforcement.

The config names which tools send content authored as me, so em-dashes get
blocked only in those. Everything else is left alone. The config is discovered
from the first of several locations that exists, so personal targeting can live
outside the versioned plugin (see the discovery order in ``find_config_path``).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Config:
    """Which tools/commands to enforce em-dash blocking on."""

    mcp_tools: list[str] = field(default_factory=list)
    bash_commands: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """True when nothing is opted in, so the hook is a no-op (inert)."""
        return not self.mcp_tools and not self.bash_commands


def _shipped_config_path() -> Path:
    """The plugin's own inert default config (empty lists).

    Located relative to this file: src/writing_tools/config.py ->
    <plugin_root>/hooks/emdash-outbound.yaml.
    """
    return Path(__file__).resolve().parent.parent.parent / "hooks" / "emdash-outbound.yaml"


def find_config_path() -> Optional[Path]:
    """Locate the config file, first found wins.

    Discovery order:
      1. ``$EMDASH_OUTBOUND_CONFIG`` (env override, used by tests)
      2. ``${CLAUDE_PROJECT_DIR}/.claude/emdash-outbound.yaml``
      3. ``$HOME/.claude/emdash-outbound.yaml``
      4. the plugin's shipped ``hooks/emdash-outbound.yaml`` (inert default)
    """
    candidates: list[Path] = []

    explicit = os.environ.get("EMDASH_OUTBOUND_CONFIG", "")
    if explicit:
        candidates.append(Path(explicit))

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        candidates.append(Path(project_dir) / ".claude" / "emdash-outbound.yaml")

    home = os.environ.get("HOME", "")
    if home:
        candidates.append(Path(home) / ".claude" / "emdash-outbound.yaml")

    candidates.append(_shipped_config_path())

    for path in candidates:
        if path.exists():
            return path
    return None


def load_config() -> Config:
    """Load the enforcement config (fail open to inert on any problem)."""
    path = find_config_path()
    if path is None:
        return Config()
    return load_config_file(path)


def load_config_file(path: Path) -> Config:
    """Load a config from a specific YAML file.

    Returns an empty (inert) Config if the file is missing or unparseable
    (fail open).
    """
    if not path.exists():
        return Config()

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        return Config()

    if not isinstance(data, dict):
        return Config()

    mcp_tools = data.get("mcpTools") or []
    bash_commands = data.get("bashCommands") or []

    # Guard against a scalar or malformed value where a list is expected.
    if not isinstance(mcp_tools, list):
        mcp_tools = []
    if not isinstance(bash_commands, list):
        bash_commands = []

    return Config(
        mcp_tools=[str(t) for t in mcp_tools],
        bash_commands=[str(c) for c in bash_commands],
    )

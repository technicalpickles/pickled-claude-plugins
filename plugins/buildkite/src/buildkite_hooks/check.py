"""PreToolUse hook that enforces buildkite tool preferences.

Reads config from ~/.config/pickled-claude-plugins/buildkite.yml (user)
or config/defaults.yml (plugin fallback). Intercepts specific bk CLI
subcommands and blocks or warns based on the strict setting.
"""

import json
import os
import re
import sys
from pathlib import Path

import yaml


def load_config():
    """Load config from user location, falling back to plugin defaults."""
    user_config = Path.home() / ".config" / "pickled-claude-plugins" / "buildkite.yml"
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    plugin_config = Path(plugin_root) / "config" / "defaults.yml" if plugin_root else None

    for path in [user_config, plugin_config]:
        if path and path.is_file():
            with open(path) as f:
                return yaml.safe_load(f)

    return None


def check_intercept(command, config):
    """Check if command matches any intercept pattern."""
    for entry in config.get("intercept", []):
        if re.search(entry["pattern"], command):
            return True
    return False


def build_message(command, config):
    """Build the block/warn message."""
    prefs = config.get("tool_preference", ["bktide", "mcp", "bk"])
    pref_str = " > ".join(prefs)
    preferred = prefs[0]

    return (
        f"Your buildkite tool preference is: {pref_str}\n"
        f"\n"
        f"The command `{command}` was intercepted. Your preferred tool is {preferred}.\n"
        f"Use `npx bktide@latest snapshot <buildkite-url>` for build investigation,\n"
        f"or `npx bktide@latest --help` for other commands.\n"
        f"\n"
        f"To allow bk commands, set `strict: false` in "
        f"~/.config/pickled-claude-plugins/buildkite.yml"
    )


def main():
    hook_input = json.loads(sys.stdin.read())

    command = hook_input.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    config = load_config()
    if not config:
        sys.exit(0)

    if not check_intercept(command, config):
        sys.exit(0)

    msg = build_message(command, config)
    strict = config.get("strict", True)

    print(msg, file=sys.stderr)
    sys.exit(2 if strict else 0)


if __name__ == "__main__":
    main()

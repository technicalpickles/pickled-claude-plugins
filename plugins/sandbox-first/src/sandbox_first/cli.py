"""CLI entry point for sandbox-first plugin hooks."""

import json
import os
import sys

from sandbox_first.checker import check_pre_tool_use, check_post_tool_use_failure
from sandbox_first.config import load_merged_skip_list

CONFIG_FILENAME = "sandbox-first.json"


def _resolve_config_paths() -> tuple[str, str]:
    """Resolve user and project config file paths from environment."""
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if not config_dir:
        config_dir = os.path.join(os.path.expanduser("~"), ".claude")
    user_config = os.path.join(config_dir, CONFIG_FILENAME)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    project_config = os.path.join(project_dir, ".claude", CONFIG_FILENAME) if project_dir else ""

    return user_config, project_config


def main():
    if len(sys.argv) < 2:
        print("Usage: sandbox-first <pre-tool-use|post-tool-use-failure>", file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Fail open: if we can't parse input, allow the tool call
        sys.exit(0)

    if subcommand == "pre-tool-use":
        user_config, project_config = _resolve_config_paths()
        skip_list = load_merged_skip_list(user_config, project_config)
        result = check_pre_tool_use(hook_input, skip_list=skip_list)
    elif subcommand == "post-tool-use-failure":
        result = check_post_tool_use_failure(hook_input)
    else:
        sys.exit(0)

    if result is not None:
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()

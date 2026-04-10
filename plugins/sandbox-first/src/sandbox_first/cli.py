"""CLI entry point for sandbox-first plugin hooks."""

import json
import sys

from sandbox_first.checker import check_pre_tool_use, check_post_tool_use_failure


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
        result = check_pre_tool_use(hook_input)
    elif subcommand == "post-tool-use-failure":
        result = check_post_tool_use_failure(hook_input)
    else:
        sys.exit(0)

    if result is not None:
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()

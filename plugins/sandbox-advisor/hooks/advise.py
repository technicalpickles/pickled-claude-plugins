#!/usr/bin/env python3
"""PostToolUseFailure:Bash hook (sandbox-advisor). See README.md."""
import sys


def main() -> None:
    # Stub: consume stdin and stay silent. Real logic lands in later tasks.
    try:
        sys.stdin.read()
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()

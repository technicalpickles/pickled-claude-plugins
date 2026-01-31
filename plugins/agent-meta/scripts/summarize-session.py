#!/usr/bin/env python3
"""Summarize a Claude session into key events.

TODO: Implement session summarization
- Extract key events: tool calls, decisions, outcomes
- Identify files touched
- Summarize pain points and patterns
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Summarize a Claude session into key events.",
        epilog="Only files within ~/.claude/projects are allowed.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        metavar="PATH",
        help="JSONL file(s) or directory(ies) to scan",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (one object per line)",
    )
    args = parser.parse_args()

    print("summarize-session: Not yet implemented", file=sys.stderr)
    print("TODO: Summarize session into key events", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()

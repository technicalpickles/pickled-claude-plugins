#!/usr/bin/env python3
"""Replay real failed Bash calls through the advisor, without running it live.

Input: JSONL, one failed sandboxed Bash call per line:
    {"command": "...", "error": "...", "cwd": "...", "unsandboxed": false}

Output: how many calls each mode would have fired on, and with --show MODE,
the calls behind one mode, so you can check the advice would have been right.
See the README for one way to export these from session transcripts.

    python3 tools/replay.py failures.jsonl
    python3 tools/replay.py failures.jsonl --show git-cwd-scope
"""
import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "advise", Path(__file__).parent.parent / "hooks" / "advise.py"
)
advise = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(advise)


def _first_line(text: str, width: int = 100) -> str:
    for line in text.splitlines():
        low = line.lower()
        if any(k in low for k in ("not permitted", "fatal", "error", "denied")):
            return line.strip()[:width]
    return text.strip()[:width]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", nargs="?", help="JSONL file (default: stdin)")
    ap.add_argument("--show", metavar="MODE", help="print the calls for one mode")
    args = ap.parse_args()

    stream = open(args.input) if args.input else sys.stdin
    counts = collections.Counter()
    total = 0
    for line in stream:
        if not line.strip():
            continue
        row = json.loads(line)
        total += 1
        payload = {
            "tool_name": "Bash",
            "cwd": row.get("cwd") or "",
            "tool_input": {
                "command": row.get("command") or "",
                "dangerouslyDisableSandbox": bool(row.get("unsandboxed")),
            },
            "tool_response": {"stderr": row.get("error") or ""},
        }
        mode = advise.decide_mode(payload)
        if not mode:
            continue
        counts[mode] += 1
        if args.show == mode:
            cmd = payload["tool_input"]["command"].replace("\n", " ")[:60]
            print(f"{cmd} | {_first_line(row.get('error') or '')}")

    if args.show:
        print()
    print(f"{total} failed calls, advice on {sum(counts.values())}")
    for mode, n in counts.most_common():
        print(f"  {mode:22} {n}")


if __name__ == "__main__":
    main()

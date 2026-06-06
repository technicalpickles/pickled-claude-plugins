#!/usr/bin/env python3
"""PostToolUseFailure:Bash hook (sandbox-advisor). See README.md."""
import re
import sys

# Per-mode error fingerprints, matched case-insensitively against the raw
# payload text. git-write is deliberately broad: the same sandbox deny surfaces
# as the index.lock message, a blocked-path "Operation not permitted", OR the
# downstream "Could not reset index file" with no EPERM line visible. srb and
# ps-top stay narrow because their failures are distinctive.
_MODE_FINGERPRINTS = {
    "git-write": (
        "operation not permitted",
        "index.lock",
        "could not reset index file",
        ".claude/agents",
        ".claude/commands",
        ".vscode/",
        ".gitmodules",
    ),
    "srb": (
        "operation not permitted",
        "mdb_error",
        "failed to create database",
    ),
    "ps-top": (
        "operation not permitted",
        "os error 1",
    ),
}


def matches_mode_fingerprints(text: str, mode: str) -> bool:
    """True if the failure output carries a fingerprint for this mode."""
    if not text:
        return False
    low = text.lower()
    return any(fp in low for fp in _MODE_FINGERPRINTS.get(mode, ()))


def main() -> None:
    # Stub: consume stdin and stay silent. Real logic lands in later tasks.
    try:
        sys.stdin.read()
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()

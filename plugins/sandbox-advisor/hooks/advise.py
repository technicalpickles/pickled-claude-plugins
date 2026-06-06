#!/usr/bin/env python3
"""PostToolUseFailure:Bash hook (sandbox-advisor). See README.md."""
import json
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


# git subcommands that write (worktree/index/refs). Read-only forms
# (log/show/diff/status/...) are intentionally absent so they classify as None.
_GIT_WRITE_SUBCOMMANDS = {
    "add", "commit", "rebase", "merge", "cherry-pick", "revert", "rm", "mv",
    "restore", "reset", "pull", "fetch", "push", "am", "apply", "clean",
    "checkout", "switch", "clone", "init", "stash", "worktree", "branch", "tag",
}

_SRB_RE = re.compile(r"^(bundle\s+exec\s+)?(\./)?(bin/)?srb(\s|$)")
_PS_TOP_RE = re.compile(r"^(rtk\s+)?(/usr/bin/|/bin/)?(ps|top)(\s|$)")
_ENV_PREFIX_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*=\S*\s+)+")


def _strip_leading_cd_and_env(command: str) -> str:
    """Reduce `cd <path> && FOO=bar <cmd>` to `<cmd>`.

    Only a single leading `cd ... &&` is stripped (the dominant real shape);
    further chaining is left intact so the segment we inspect is the real one.
    """
    seg = command.strip()
    cd_match = re.match(r"^cd\s+\S+\s*&&\s*(.*)$", seg, re.DOTALL)
    if cd_match:
        seg = cd_match.group(1).strip()
    seg = _ENV_PREFIX_RE.sub("", seg)
    return seg.strip()


def _is_git_write(seg: str) -> bool:
    toks = seg.split()
    if not toks or toks[0] != "git":
        return False
    # Skip git global options to find the subcommand.
    i = 1
    while i < len(toks):
        t = toks[i]
        if t in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
            continue
        if t.startswith("-"):
            i += 1
            continue
        break
    sub = toks[i] if i < len(toks) else ""
    return sub in _GIT_WRITE_SUBCOMMANDS


def classify_command(command: str):
    """Return 'git-write', 'srb', 'ps-top', or None."""
    seg = _strip_leading_cd_and_env(command)
    if _SRB_RE.match(seg):
        return "srb"
    if _PS_TOP_RE.match(seg):
        return "ps-top"
    if _is_git_write(seg):
        return "git-write"
    return None


# Advisory, not directive. We acknowledge the command is a KNOWN sandbox
# failure mode and that this is likely (not certainly) why it failed, then
# offer the fix. This honesty is what makes the broad git fingerprints safe:
# we never assert "definitely the sandbox," we say "known to fail this way."
_ADVICE = {
    "git-write": (
        "Heads up: git writes inside pt worktrees are KNOWN to fail under the "
        "Claude Code command sandbox (the blocked .claude/.vscode/.gitmodules "
        "paths and .git/worktrees/.../index.lock, which allowWrite cannot "
        "override). If that's why this failed, re-run with "
        "dangerouslyDisableSandbox: true."
    ),
    "srb": (
        "Heads up: srb (sorbet) is KNOWN to fail under the Claude Code command "
        "sandbox -- it caches in LMDB, which uses SysV semaphores the sandbox "
        "denies (semctl/semop EPERM); the cache dir is already writable so "
        "allowWrite cannot fix it. If that's why this failed, re-run with "
        "dangerouslyDisableSandbox: true."
    ),
    "ps-top": (
        "Heads up: ps/top are KNOWN to fail under the Claude Code command "
        "sandbox -- they are setuid-root binaries and the sandbox denies "
        "executing setuid/setgid binaries. They are read-only and safe "
        "unsandboxed. If that's why this failed, re-run with "
        "dangerouslyDisableSandbox: true."
    ),
}


def _error_text(payload: dict) -> str:
    """Serialize the payload EXCEPT tool_input, so fingerprints match the
    failure output regardless of which field carries it, without
    false-matching the command text (which lives in tool_input)."""
    rest = {k: v for k, v in payload.items() if k != "tool_input"}
    return json.dumps(rest, default=str)


def decide_advice(payload: dict):
    """Return advisory text to inject, or None to stay silent."""
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not command:
        return None
    # Loop guard: if it already ran unsandboxed, "re-run unsandboxed" is wrong.
    if tool_input.get("dangerouslyDisableSandbox"):
        return None
    mode = classify_command(command)
    if mode is None:
        return None
    # Require one of THIS mode's fingerprints in the failure payload, so an
    # srb type-error or a non-sandbox git error does not trigger advice.
    if not matches_mode_fingerprints(_error_text(payload), mode):
        return None
    return _ADVICE[mode]


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Malformed stdin -> fail open, surface the raw failure unchanged.
        sys.exit(0)
    reason = None
    try:
        reason = decide_advice(payload)
    except Exception:
        sys.exit(0)
    if reason:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": reason,
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()

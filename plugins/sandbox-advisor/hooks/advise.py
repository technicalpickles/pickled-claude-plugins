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
    "git-ssh": (
        # SSH (port 22) egress is blocked outright by the sandbox network
        # allowlist, which only permits HTTPS to specific hosts -- not the
        # ssh-agent socket, which is a separate (and already-open) surface.
        # Deliberately excludes the generic "operation not permitted"
        # fingerprint: the `gh` matcher below is broad (any gh subcommand),
        # and that string is common enough in unrelated gh failures to
        # false-positive.
        "port 22",
        "could not read from remote repository",
        "authentication method negotiation failed",
        "connection closed by unknown port",
        "failed to run git: exit status",
    ),
    "keychain-write": (
        # macOS Keychain WRITES go through a Security.framework call the
        # sandbox denies outright; READS are unaffected (confirmed
        # empirically: `security find-generic-password` and `gh auth status`
        # both succeed against an existing item). Narrow matcher below makes
        # the generic "operation not permitted" fingerprint safe here.
        "seckeychainitemcreatefromcontent",
        "operation not permitted",
    ),
}


def matches_mode_fingerprints(text: str, mode: str) -> bool:
    """True if the failure output carries a fingerprint for this mode."""
    if not text:
        return False
    low = text.lower()
    return any(fp in low for fp in _MODE_FINGERPRINTS.get(mode, ()))


# git subcommands that write locally (worktree/index/refs), MINUS the ones
# that talk to a remote -- those go through _GIT_NETWORK_SUBCOMMANDS instead,
# since their sandbox failure mode (SSH port 22 egress) is unrelated to the
# blocked-path denies this mode covers. Read-only forms (log/show/diff/
# status/...) are intentionally absent so they classify as None.
_GIT_WRITE_SUBCOMMANDS = {
    "add", "commit", "rebase", "merge", "cherry-pick", "revert", "rm", "mv",
    "restore", "reset", "am", "apply", "clean",
    "checkout", "switch", "init", "stash", "worktree", "branch", "tag",
}

# git subcommands that talk to a remote -- fail under the sandbox because raw
# SSH (port 22) egress is blocked, not because of a blocked write path.
_GIT_NETWORK_SUBCOMMANDS = {"push", "fetch", "pull", "clone", "ls-remote"}

_SRB_RE = re.compile(r"^(bundle\s+exec\s+)?(\./)?(bin/)?srb(\s|$)")
_PS_TOP_RE = re.compile(r"^(rtk\s+)?(/usr/bin/|/bin/)?(ps|top)(\s|$)")
# Deliberately broad: matches ANY gh subcommand, not just the ones that shell
# out to git. Only `pr checkout`/`co`/`sw` and `repo sync` actually inherit
# the current repo's remote protocol (and so hit this bug when that remote is
# SSH); `repo clone`/`gist clone`/`repo fork --clone`/`extension install` use
# gh's own `git_protocol` config instead, independent of any local remote.
# The rest of gh is pure REST/GraphQL over HTTPS and never touches this path.
# Fingerprint gating in decide_advice() is what keeps the broad match safe.
_GH_RE = re.compile(r"^gh(\s|$)")
# gh subcommands that write credentials to the macOS Keychain. Checked before
# _GH_RE so these take "keychain-write" instead of falling into "git-ssh".
_GH_AUTH_WRITE_RE = re.compile(
    r"^gh\s+auth\s+(login|refresh|logout|setup-git)(\s|$)"
)
# `security` subcommands that write/delete keychain items (vs. find-*, which
# only reads and is unaffected).
_SECURITY_WRITE_RE = re.compile(
    r"^security\s+(add|delete)-(generic|internet)-password(\s|$)"
)
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


def _git_subcommand(seg: str):
    """Return the git subcommand token, or None if `seg` isn't a `git ...` call."""
    toks = seg.split()
    if not toks or toks[0] != "git":
        return None
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
    return toks[i] if i < len(toks) else ""


def classify_command(command: str):
    """Return 'git-write', 'git-ssh', 'keychain-write', 'srb', 'ps-top', or None."""
    seg = _strip_leading_cd_and_env(command)
    if _SRB_RE.match(seg):
        return "srb"
    if _PS_TOP_RE.match(seg):
        return "ps-top"
    if _GH_AUTH_WRITE_RE.match(seg) or _SECURITY_WRITE_RE.match(seg):
        return "keychain-write"
    sub = _git_subcommand(seg)
    if sub in _GIT_NETWORK_SUBCOMMANDS or _GH_RE.match(seg):
        return "git-ssh"
    if sub in _GIT_WRITE_SUBCOMMANDS:
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
    "git-ssh": (
        "Heads up: git operations over SSH (push, fetch, pull, clone, "
        "ls-remote), or `gh pr checkout`/`gh repo sync` against a repo whose "
        "remote is an SSH URL, are KNOWN to fail under the Claude Code "
        "command sandbox -- the network sandbox only allows HTTPS to "
        "specific allowlisted hosts, so raw SSH on port 22 is blocked "
        "outright. This is NOT the ssh-agent socket, which is already open. "
        "If that's why this failed, re-run with dangerouslyDisableSandbox: "
        "true, or fix it durably by switching the remote to HTTPS: `git "
        "remote set-url origin https://github.com/OWNER/REPO.git` (and, if "
        "cloning/forking fresh via gh, `gh config set -h github.com "
        "git_protocol https`)."
    ),
    "keychain-write": (
        "Heads up: writing to the macOS Keychain (`gh auth login`/`refresh`/"
        "`logout`/`setup-git`, or `security add-*-password`/`delete-*-"
        "password`) is KNOWN to fail under the Claude Code command sandbox "
        "-- Keychain reads are fine (gh reading an already-stored token "
        "works), but the write call is denied outright. If that's why this "
        "failed, re-run with dangerouslyDisableSandbox: true. There's no "
        "sandbox setting that fixes this durably; the practical workaround "
        "is to run the auth/write step once outside the sandbox -- reads "
        "of the resulting credential work fine sandboxed afterward."
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

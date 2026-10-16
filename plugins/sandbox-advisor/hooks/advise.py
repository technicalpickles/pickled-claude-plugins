#!/usr/bin/env python3
"""PostToolUseFailure:Bash hook (sandbox-advisor). See README.md."""
import json
import os
import re
import sys

# Distinctive enough to identify without the command: a sorbet LMDB abort
# looks the same however many wrappers deep sorbet ran.
_ERROR_ONLY_FINGERPRINTS = {
    "srb": (
        "mdb_error",
        "maybecreatekeyvaluestore",
    ),
    "bun-tmpdir": (
        "bun is unable to write files to tempdir",
    ),
    "gem-spec-cache": (
        ".cache/gem/specs",
    ),
    "keychain-write": (
        "seckeychainitemcreatefromcontent",
        "writing destination keychain",
        "keychain is accessible and writable",
    ),
}

# The command picks the mode; one of these confirms it was the sandbox.
_MODE_FINGERPRINTS = {
    # Not bare "index.lock": `File exists` on it is a concurrent git, not the sandbox.
    "git-write": (
        "operation not permitted",
        "could not reset index file",
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
        # Deliberately excludes the generic "operation not permitted"
        # fingerprint: the `gh` matcher below is broad (any gh subcommand),
        # and that string is common enough in unrelated gh failures to
        # false-positive.
        "port 22",
        "ssh_dispatch_run_fatal",
        "could not read from remote repository",
        "authentication method negotiation failed",
        "connection closed by unknown port",
        "failed to run git: exit status",
    ),
    "keychain-write": (
        # Generic EPERM is safe here: the command matcher is narrow.
        "seckeychainitemcreatefromcontent",
        "operation not permitted",
    ),
}

# Checked in this order: a worktree-delete error can name a .git path too.
_GIT_WORKTREE_DELETE_FPS = ("failed to delete '",)
_GIT_PATH_DENY_FPS = (
    ".claude/agents",
    ".claude/commands",
    ".vscode/",
    ".idea/",
    ".gitmodules",
    ".mcp.json",
    ".git/hooks",
    ".git/config",
    "could not lock config file",
    "could not write config file",
    "could not reset index file",
    # Shell rc basenames are denied at any depth.
    ".gitconfig'",
    ".zshrc'",
    ".zprofile'",
    ".bashrc'",
    ".profile'",
)
_GIT_SCOPE_FPS = (
    "index.lock",
    "cannot lock ref",
    "unable to create temporary file",
    "unable to unlink old",
)


def matches_mode_fingerprints(text: str, mode: str) -> bool:
    """True if the failure output carries a fingerprint for this mode."""
    if not text:
        return False
    low = text.lower()
    return any(fp in low for fp in _MODE_FINGERPRINTS.get(mode, ()))


def error_only_mode(text: str):
    if not text:
        return None
    low = text.lower()
    for mode, fps in _ERROR_ONLY_FINGERPRINTS.items():
        if any(fp in low for fp in fps):
            return mode
    return None


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

_GIT_NETWORK_SUBCOMMANDS = {"push", "fetch", "pull", "clone", "ls-remote"}

_SRB_RE = re.compile(r"^(bundle\s+exec\s+)?(\./)?(bin/)?srb(\s|$)")
_PS_TOP_RE = re.compile(r"^(rtk\s+)?(/usr/bin/|/bin/)?(ps|top)(\s|$)")
# Deliberately broad: matches ANY gh subcommand, not just the ones that shell
# out to git. Only `pr checkout`/`co`/`sw` and `repo sync` actually inherit
# the current repo's remote protocol; the rest of gh is pure REST/GraphQL.
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
# worktrunk wraps `git worktree add`/`remove`, so it hits the same denies.
_WT_WRITE_RE = re.compile(r"^wt\s+(remove|switch)(\s|$)")
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
    if _WT_WRITE_RE.match(seg):
        return "git-write"
    sub = _git_subcommand(seg)
    if sub in _GIT_NETWORK_SUBCOMMANDS or _GH_RE.match(seg):
        return "git-ssh"
    if sub in _GIT_WRITE_SUBCOMMANDS:
        return "git-write"
    return None


_ABS_PATH_RE = re.compile(r"""(/[^\s'":]+)""")
_CMD_TARGET_RE = re.compile(r"""(?:^|&&|;)\s*(?:cd|git\s+-C)\s+(['"]?)([^\s'";&]+)\1""")


def _under(path: str, root: str) -> bool:
    path = os.path.normpath(path)
    root = os.path.normpath(root)
    return path == root or path.startswith(root.rstrip("/") + "/")


def _targets_outside_cwd(command: str, error_text: str, cwd: str) -> bool:
    # Write access is anchored to the session cwd; a shell `cd` doesn't move it.
    if not cwd:
        return False
    home = os.path.expanduser("~")
    candidates = []
    for p in _ABS_PATH_RE.findall(error_text):
        if ".git" in p or p.endswith(".lock"):
            candidates.append(p)
    for _, p in _CMD_TARGET_RE.findall(command):
        p = p.replace("$HOME", home)
        p = os.path.expanduser(p)
        if os.path.isabs(p):
            candidates.append(p)
    return any(not _under(p, cwd) for p in candidates)


def classify_git_write(command: str, error_text: str, cwd: str) -> str:
    low = error_text.lower()
    if any(fp in low for fp in _GIT_WORKTREE_DELETE_FPS):
        return "git-worktree-delete"
    if any(fp in low for fp in _GIT_PATH_DENY_FPS):
        return "git-path-deny"
    if any(fp in low for fp in _GIT_SCOPE_FPS) and _targets_outside_cwd(
        command, error_text, cwd
    ):
        return "git-cwd-scope"
    return "git-write"


# Advisory: "KNOWN to fail" + "if that's why", never "definitely the sandbox".
# Unsandboxing is named only for modes with no in-sandbox fix.
_ADVICE = {
    "git-path-deny": (
        "Heads up: this git write touched a path the Claude Code command "
        "sandbox ALWAYS denies, regardless of allowWrite (.git/config, "
        ".git/hooks/*, .claude/agents/*, .claude/commands/*, .mcp.json, "
        ".vscode/*, .idea/*, .gitmodules). No setting lifts these. If that's "
        "why this failed, re-run this exact command with "
        "dangerouslyDisableSandbox: true. If it was a worktree create "
        "(`wt switch --create`, `git worktree add -b`) that died partway, the "
        "branch already exists: retry without `--create`/`-b`."
    ),
    "git-cwd-scope": (
        "Heads up: this git write targets a repo outside the session's "
        "working directory. The Claude Code sandbox anchors write access to "
        "the directory the session started in (or last entered with "
        "EnterWorktree), and a shell `cd` or `git -C` doesn't move it. Fix: "
        "EnterWorktree(path: <that repo's worktree>) and re-run sandboxed. "
        "Only if EnterWorktree isn't possible there, re-run with "
        "dangerouslyDisableSandbox: true."
    ),
    "git-worktree-delete": (
        "Heads up: removing a worktree directory is KNOWN to fail under the "
        "Claude Code command sandbox, often after git has already "
        "unregistered it (so `git worktree list` no longer shows it). Re-run "
        "with dangerouslyDisableSandbox: true. If the directory still "
        "survives, delete it with `/bin/rm -rf <path>`: plain `rm` is often "
        "aliased to a trash tool that fails for unrelated reasons."
    ),
    "git-write": (
        "Heads up: this git write hit an `Operation not permitted`, which is "
        "usually the Claude Code command sandbox. Identify the case before "
        "unsandboxing: if the repo is outside the session's working "
        "directory, EnterWorktree(path: <repo>) first; if the error names a "
        "path the sandbox always denies (.git/hooks, .git/config, "
        ".claude/agents, .mcp.json, ...), re-run with "
        "dangerouslyDisableSandbox: true."
    ),
    "srb": (
        "Heads up: srb (sorbet) is KNOWN to fail under the Claude Code command "
        "sandbox -- it opens an LMDB key-value store, and LMDB's SysV "
        "semaphores (semctl/semop) are denied. This happens even with no "
        "cache dir and with a writable one, so allowWrite cannot fix it. If "
        "that's why this failed, re-run with dangerouslyDisableSandbox: true."
    ),
    "ps-top": (
        "Heads up: ps/top are KNOWN to fail under the Claude Code command "
        "sandbox -- they are setuid-root binaries and the sandbox denies "
        "executing setuid/setgid binaries. They are read-only and safe "
        "unsandboxed. If that's why this failed, re-run with "
        "dangerouslyDisableSandbox: true."
    ),
    "git-ssh": (
        "Heads up: git over SSH (push, fetch, pull, clone, ls-remote, or "
        "`gh pr checkout`/`gh repo sync` against an SSH remote) is KNOWN to "
        "fail under the Claude Code command sandbox when nothing tunnels it: "
        "raw TCP to port 22 is blocked. If your setup routes agent SSH "
        "through a local relay (an ssh ProxyCommand to an allowlisted "
        "localhost proxy), this usually means the relay is down: check it "
        "first (`ssh -T git@github.com`, `ssh -G github.com | grep -i "
        "proxycommand`) and restart it rather than unsandboxing. With no "
        "relay, re-run with dangerouslyDisableSandbox: true. Don't switch "
        "the remote to HTTPS to get around this: that pushes with a "
        "different credential than the SSH key, silently changing who "
        "authenticates."
    ),
    "keychain-write": (
        "Heads up: writing to the macOS Keychain (`gh auth login`/`refresh`/"
        "`logout`/`setup-git`, `security add-*-password`/`delete-*-"
        "password`, or a tool that stores a credential, like `cenv create` "
        "or `fnox set`) is KNOWN to fail under the Claude Code command "
        "sandbox. Keychain reads work sandboxed; writes are denied outright. "
        "Re-run just the write step with dangerouslyDisableSandbox: true; "
        "later reads of that credential work sandboxed. Note `security "
        "delete-generic-password` can print success and still exit 161 "
        "sandboxed: the item is NOT deleted."
    ),
    "bun-tmpdir": (
        "Heads up: bun is KNOWN to fail under the Claude Code command sandbox "
        "when its default temp dir isn't writable. Fix it in-sandbox: re-run "
        "with BUN_TMPDIR=\"$TMPDIR\" set (e.g. `BUN_TMPDIR=\"$TMPDIR\" "
        "<command>`). No need to unsandbox."
    ),
    "gem-spec-cache": (
        "Heads up: RubyGems is KNOWN to fail under the Claude Code command "
        "sandbox writing its spec cache (~/.cache/gem/specs). Fix it "
        "in-sandbox: re-run with GEM_SPEC_CACHE=\"$TMPDIR/gemspecs\" set. "
        "No need to unsandbox."
    ),
}


def _error_text(payload: dict) -> str:
    """Serialize the payload EXCEPT tool_input, so fingerprints match the
    failure output regardless of which field carries it, without
    false-matching the command text (which lives in tool_input)."""
    rest = {k: v for k, v in payload.items() if k not in ("tool_input", "cwd")}
    return json.dumps(rest, default=str)


def decide_mode(payload: dict):
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not command:
        return None
    # Loop guard: if it already ran unsandboxed, "re-run unsandboxed" is wrong.
    if tool_input.get("dangerouslyDisableSandbox"):
        return None
    text = _error_text(payload)
    mode = error_only_mode(text)
    if mode:
        return mode
    mode = classify_command(command)
    if mode is None:
        return None
    # Require one of THIS mode's fingerprints in the failure payload, so an
    # srb type-error or a non-sandbox git error does not trigger advice.
    if not matches_mode_fingerprints(text, mode):
        return None
    if mode == "git-write":
        return classify_git_write(command, text, payload.get("cwd") or "")
    return mode


def decide_advice(payload: dict):
    """Return advisory text to inject, or None to stay silent."""
    mode = decide_mode(payload)
    return _ADVICE[mode] if mode else None


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

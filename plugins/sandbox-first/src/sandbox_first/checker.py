"""Hook decision logic for sandbox enforcement."""

from sandbox_first.transcript import find_recent_sandboxed_failure

LOOKBACK = 10

DENY_MESSAGE = (
    "This command was called with dangerouslyDisableSandbox but there is no recent "
    "sandboxed failure in this session. Try running the command sandboxed first. "
    "If it fails due to a sandbox restriction (network, filesystem), then retry "
    "with dangerouslyDisableSandbox and explain what restriction was hit."
)

FAILURE_CONTEXT = (
    "This command failed and may have been blocked by the sandbox. Before retrying "
    "with dangerouslyDisableSandbox, consider whether the sandbox configuration "
    "should be updated instead:\n"
    "- Network issues: add the host to sandbox.network.allowedHosts in ~/.claude/settings.json\n"
    "- Filesystem issues: add the path to sandbox.filesystem.allowWrite in ~/.claude/settings.json\n"
    "- If the sandbox config should be updated, suggest the specific change to the user.\n"
    "- If this is a one-off need, you may retry with dangerouslyDisableSandbox "
    "and explain what restriction was hit."
)

# Error substrings (case-insensitive) that strongly suggest a sandbox-caused
# failure. This is intentionally a conservative allow-list: we only add the
# sandbox-warning context when the error clearly matches one of these
# signatures. Everything else (command-not-found, ENOENT, git warnings, test
# assertion failures, application exceptions, etc.) stays silent.
#
# Covered EPERM shapes (empirical — from sandbox test sessions):
#   - tool-prefixed:   touch: cannot touch 'path': Operation not permitted
#                      mkdir: cannot create directory 'path': Operation not permitted
#                      mkdir: \u2018path\u2019: Operation not permitted  (smart-quote variant)
#   - shell-eval:      (eval):1: operation not permitted: /path
#   - git single-fatal: fatal: could not create leading directories of '.git': Operation not permitted
#                       fatal: cannot copy 'src' to 'dst': Operation not permitted
#   - git error+fatal: error: could not write config file <path>: Operation not permitted
#                      fatal: could not set 'core.repositoryformatversion' to '0'
#                      (second fatal line is paired with the first; matched together)
#
# NOT covered by design:
#   - cascading ENOENT: a blocked sandbox mkdir causes a *subsequent* command to emit
#     "No such file or directory" without any EPERM. Matching "no such file or directory"
#     would catch real ENOENT errors (missing files, bad paths) as false positives, so
#     this case requires transcript-level context to detect safely.
#
# macOS Mach port / XPC denials:
#   bootstrap_check_in is the launchd API multi-process macOS apps call to register
#   a service with the bootstrap server. When seatbelt denies this, the process
#   crashes with a message like:
#     Check failed: kr == KERN_SUCCESS. bootstrap_check_in
#     org.chromium.Chromium.MachPortRendezvousServer.<pid>: Permission denied (1100)
#   Observed when Playwright launches headless Chromium inside Claude Code's bash
#   sandbox. The same signature covers other multi-process macOS tools (Electron,
#   Puppeteer, etc.). bootstrap_check_in is distinctive enough to match on alone.
SANDBOX_ERROR_SIGNATURES = (
    "operation not permitted",
    "sandbox-exec",
    "read-only file system",
    "connection refused",
    "could not resolve host",
    "couldn't resolve host",
    "network is unreachable",
    "failed to connect",
    "bootstrap_check_in",
)


def _looks_like_sandbox_error(error: str) -> bool:
    """True if the error text matches a known sandbox-failure signature."""
    if not error:
        return False
    lowered = error.lower()
    return any(sig in lowered for sig in SANDBOX_ERROR_SIGNATURES)


def command_matches_skip_list(command: str, skip_list: list[str]) -> bool:
    """True if command matches any entry in the skip list (word-boundary prefix match).

    An entry matches if the command (after stripping leading whitespace) equals
    the entry exactly, or starts with the entry followed by whitespace.
    """
    cmd = command.lstrip()
    for entry in skip_list:
        if cmd == entry or (cmd.startswith(entry) and cmd[len(entry):len(entry) + 1].isspace()):
            return True
    return False


def check_pre_tool_use(hook_input: dict) -> dict | None:
    """Check a PreToolUse Bash call. Returns JSON output dict or None to allow."""
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    if not tool_input.get("dangerouslyDisableSandbox"):
        return None

    # dangerouslyDisableSandbox is set. Check transcript for recent sandboxed failure.
    transcript_path = hook_input.get("transcript_path", "")
    if find_recent_sandboxed_failure(transcript_path, lookback=LOOKBACK):
        return None  # Allow: there was a recent sandboxed failure

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": DENY_MESSAGE,
        }
    }


def check_post_tool_use_failure(hook_input: dict) -> dict | None:
    """Check a PostToolUseFailure Bash call. Returns JSON output dict or None."""
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    if tool_input.get("dangerouslyDisableSandbox"):
        return None  # Already unsandboxed, not a sandbox issue

    error = hook_input.get("error", "")
    if not _looks_like_sandbox_error(error):
        return None  # Error doesn't look sandbox-shaped, stay silent

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": FAILURE_CONTEXT,
        }
    }

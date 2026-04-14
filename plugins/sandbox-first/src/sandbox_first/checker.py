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

PARTIAL_SUCCESS_CONTEXT = (
    "This command exited successfully but its stderr contains a sandbox-shaped "
    "denial, which often indicates a silent partial failure (e.g. `git worktree "
    "remove` deleting the worktree but failing to update `.git/config`; a clone "
    "completing but skipping template files). Before continuing:\n"
    "- Verify the intended side effects actually happened (inspect the filesystem, "
    "re-read config, re-list state).\n"
    "- If state is inconsistent, either fix the sandbox config so the denied write "
    "succeeds next time (e.g. sandbox.filesystem.allowWrite in ~/.claude/settings.json) "
    "or retry the whole operation with dangerouslyDisableSandbox.\n"
    "- If the stderr is genuinely harmless (a warning that does not affect outcome), "
    "note that explicitly so the user knows it was considered."
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
# Silent partial failures (exit=0 with sandbox-shaped stderr) — empirical:
#   - git worktree remove:  "error: could not write config file .git/config:
#                           Operation not permitted" (exit 0, worktree deleted
#                           but config not updated — stale metadata).
#   - git worktree add:     "error: could not read IPC response" (exit 0, git
#                           fsmonitor's unix-socket probe denied; worktree is
#                           created fine but the noise is sandbox-shaped).
#   The "could not read ipc response" substring is distinct from 1Password's
#   "1Password IPC error" false positive — git's phrasing is more specific.
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
    "could not read ipc response",
)


def _looks_like_sandbox_error(error: str) -> bool:
    """True if the error text matches a known sandbox-failure signature."""
    if not error:
        return False
    lowered = error.lower()
    return any(sig in lowered for sig in SANDBOX_ERROR_SIGNATURES)


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


def _extract_stderr(hook_input: dict) -> str:
    """Best-effort stderr extraction from a PostToolUse Bash payload.

    The canonical shape for Bash is `tool_response.stderr`. A couple of
    historical variants appear in the wild (top-level `stderr`, or a
    string-valued `tool_response` carrying a full transcript), so we probe
    a few locations and concatenate anything textual we find. Keeps us
    resilient to harness changes without needing schema updates.
    """
    chunks: list[str] = []
    response = hook_input.get("tool_response")
    if isinstance(response, dict):
        for key in ("stderr", "stdout"):
            value = response.get(key)
            if isinstance(value, str) and value:
                chunks.append(value)
    elif isinstance(response, str) and response:
        chunks.append(response)
    top_stderr = hook_input.get("stderr")
    if isinstance(top_stderr, str) and top_stderr:
        chunks.append(top_stderr)
    return "\n".join(chunks)


def check_post_tool_use(hook_input: dict) -> dict | None:
    """Check a PostToolUse Bash call (success path). Returns JSON output dict or None.

    Fires when a Bash command exited successfully but its stderr contains a
    sandbox-shaped signature, which typically means a silent partial failure
    (command reported success, sandbox quietly blocked a side effect).
    """
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    if tool_input.get("dangerouslyDisableSandbox"):
        return None  # Already unsandboxed, not a sandbox issue

    stderr = _extract_stderr(hook_input)
    if not _looks_like_sandbox_error(stderr):
        return None

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": PARTIAL_SUCCESS_CONTEXT,
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

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

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": FAILURE_CONTEXT,
        }
    }

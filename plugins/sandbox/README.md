# Sandbox Plugin

Promotes sandbox-first execution in Claude Code by intercepting unnecessary unsandboxed Bash calls and surfacing sandbox failure guidance.

## What It Does

**PreToolUse hook:** When Claude tries to run a Bash command with `dangerouslyDisableSandbox: true`, the hook checks the session transcript for a recent sandboxed failure. If none is found, it denies the call with a message to try sandboxed first. If a recent sandboxed failure exists, it allows the retry.

**PostToolUseFailure hook:** When a sandboxed Bash command fails, the hook injects context suggesting the user check their sandbox configuration (`sandbox.network.allowedHosts`, `sandbox.filesystem.allowWrite` in `~/.claude/settings.json`).

**Skill (sandbox-first):** Behavioral guidance that teaches Claude to prefer sandboxed execution, diagnose sandbox restrictions, and suggest config fixes before retrying unsandboxed.

## Configuration

The lookback window (how many transcript entries to scan for prior failures) defaults to 10. This covers roughly 5 tool call round-trips.

## Testing

```bash
uv run --directory plugins/sandbox pytest -v
```

## How It Works

1. Claude calls Bash with `dangerouslyDisableSandbox: true`
2. PreToolUse hook fires, reads `transcript_path` from hook input
3. Scans the last N entries of the JSONL transcript for a sandboxed Bash `tool_use` followed by an error `tool_result`
4. If found: allows the unsandboxed call (legitimate retry)
5. If not found: denies with guidance to try sandboxed first

## Known Limitations

- PostToolUseFailure fires on all sandboxed Bash failures, not just sandbox restrictions. A regular syntax error would also trigger the "check sandbox config" message.
- The lookback window is hardcoded. If Claude does extensive work between a sandbox failure and the unsandboxed retry, it may fall outside the window.
- No smart error pattern matching yet. Phase 2 would map specific errors to specific config suggestions.

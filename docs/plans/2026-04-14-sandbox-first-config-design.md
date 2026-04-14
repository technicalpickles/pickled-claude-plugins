# Sandbox-First: Skip Failure Requirement Config

**Date:** 2026-04-14
**Status:** Draft
**Plugin:** sandbox-first

## Problem

The sandbox-first plugin enforces that every `dangerouslyDisableSandbox: true` call must be preceded by a recent sandboxed failure. This is good for safety, but some commands (e.g. `docker`, `colima ssh`, `bk`) are known to always fail in the sandbox. Forcing a fail-then-retry cycle for these commands is pure friction with no safety benefit.

## Goal

Allow users to configure commands that are known to fail in the sandbox, so the plugin skips the "require a prior sandboxed failure" check for those commands. The sandbox itself is always used for everything else. This config only relaxes the enforcement hook, never bypasses the sandbox.

## Design

### Config File

Two locations, following Claude Code's layering convention:

- **User-level:** `$CLAUDE_CONFIG_DIR/sandbox-first.json` (falls back to `~/.claude/sandbox-first.json` if `CLAUDE_CONFIG_DIR` is not set)
- **Project-level:** `<project>/.claude/sandbox-first.json`

```json
{
  "skip_failure_requirement": [
    "docker",
    "colima ssh",
    "bk"
  ]
}
```

### Matching

Word-boundary prefix matching against the bash command string (`tool_input.command`). A config entry matches if the command starts with the entry followed by whitespace or end-of-string.

Examples with entry `"docker"`:
- `docker build .` -- matches (`docker` + space)
- `docker` -- matches (`docker` + end-of-string)
- `dockerize app` -- does NOT match (no word boundary)

Examples with entry `"colima ssh"`:
- `colima ssh myhost` -- matches
- `colima status` -- does NOT match

The command string is stripped of leading whitespace before matching. Config entries are matched as-is (no normalization beyond stripping).

### Merge Behavior

Union of user-level and project-level lists. If either file lists a prefix, it's in effect. No override/deny mechanism needed for v1.

### Config Resolution

The hook receives these env vars and hook input fields:

| Source | How to get |
|--------|-----------|
| User config | `$CLAUDE_CONFIG_DIR/sandbox-first.json`, falling back to `~/.claude/sandbox-first.json` if `CLAUDE_CONFIG_DIR` is not set |
| Project config | `$CLAUDE_PROJECT_DIR/.claude/sandbox-first.json` |

Both paths are optional. Missing files are silently ignored. Config is re-read from disk on every hook invocation (no caching). Hook calls are low-frequency enough that this is fine.

### Changed Behavior

**`check_pre_tool_use()` becomes:**

```
if not Bash tool: pass through
if not dangerouslyDisableSandbox: pass through

# dangerouslyDisableSandbox is set
if command matches skip_failure_requirement: ALLOW (return None)
if recent sandboxed failure in transcript: ALLOW (return None)
DENY (existing behavior)
```

The config check is inserted before the transcript check. If the command matches, we skip the transcript scan entirely.

**Nothing else changes:**
- Sandboxed commands are never blocked by this config
- `check_post_tool_use_failure()` is unaffected
- The transcript-based enforcement remains the fallback for non-configured commands

### Skill Update

Add a brief note to `SKILL.md` mentioning that some commands may be pre-configured to skip the failure requirement. The skill cannot proactively read config files, so keep it descriptive rather than instructional. Claude will learn from the hook's behavior (allow without deny) that configured commands don't need the sandboxed-first step.

```markdown
## Configured Exceptions

Some commands are known to always fail in the sandbox (e.g. `docker`, `colima ssh`).
These can be configured in `~/.claude/sandbox-first.json` or `.claude/sandbox-first.json`
under the `skip_failure_requirement` key. The enforcement hook will allow
`dangerouslyDisableSandbox: true` for these commands without requiring a prior
sandboxed failure.
```

### Schema Validation

The config loader is lenient:
- Missing file: silently ignored (empty list)
- Malformed JSON: silently ignored (empty list)
- Missing `skip_failure_requirement` key: empty list
- `skip_failure_requirement` is not an array: treated as empty list
- Array contains non-string values: non-strings are filtered out
- Extra keys in the JSON object: ignored

## File Changes

| File | Change |
|------|--------|
| `src/sandbox_first/checker.py` | Add `load_config()`, `command_matches_skip_list()`, integrate into `check_pre_tool_use()` |
| `src/sandbox_first/cli.py` | Pass config paths (from env vars) to checker |
| `skills/sandbox-first/SKILL.md` | Add section about known unsandboxed commands config |
| `tests/test_checker.py` | Config loading, prefix matching, merge, missing files, interaction with transcript fallback |
| `README.md` | Document the config file format and locations |

## What This Does NOT Do

- Does not block sandboxed attempts for configured commands (considered and rejected: makes sandbox failures harder to debug)
- Does not add regex matching (prefix is sufficient, matches Claude Code's permission model)
- Does not add an override/deny mechanism (union is enough for v1)
- Does not affect `check_post_tool_use_failure()` (sandbox error guidance is still useful even for configured commands, in case the config becomes stale)

## Testing Plan

1. **Config loading:** Read from both paths, handle missing files, handle malformed JSON
2. **Prefix matching:** Exact command name, command with args, word boundary enforcement (`docker` does not match `dockerize`), partial prefix (no match on `dock` for `docker`), leading whitespace handling
3. **Merge:** Both files present, only user, only project, neither
4. **Integration with existing logic:** Configured command skips transcript check, non-configured command still requires transcript failure
5. **Fail-open:** Invalid config (wrong type, missing key, malformed JSON) results in an empty skip-list, so existing transcript-based enforcement still applies. The hook never crashes due to bad config.

## Open Questions

None. Ready for implementation.

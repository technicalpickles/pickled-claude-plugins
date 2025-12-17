# Retrospective: Plugin Installation Consistency Investigation

**Date:** 2025-12-17
**Duration:** ~1 hour
**Participants:** Claude + Josh

## Goal

Perform a consistency check on how tool-routing works across different installation methods, specifically understanding:
1. How Claude Code invokes plugin hooks
2. Copy vs symlink behavior for plugin installation
3. Differences between git marketplace vs local directory marketplace
4. Environment variables available to hooks

## Key Discoveries

### 1. Plugin Installation Creates Copies, Not Symlinks

Claude Code copies plugins to `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/` rather than symlinking. This means:
- Changes to source require reinstall to take effect (for git marketplaces)
- Each version is isolated
- Orphaned versions are marked with `.orphaned_at` timestamp file

### 2. Directory-Source Marketplaces Behave Differently

For marketplaces with `"source": "directory"` (pointing to local filesystem):
- **Still creates cache copies** - contrary to initial hypothesis
- Cache is created at `{marketplace}/{plugin}/{version}/`
- `installed_plugins.json` may show stale commit SHA as version
- Changes to source directory are NOT reflected until reinstall

### 3. Environment Variables in Hooks

| Variable | Global Hooks | Plugin Hooks |
|----------|--------------|--------------|
| `CLAUDE_PLUGIN_ROOT` | NOT SET | Set to cache path |
| `CLAUDE_PROJECT_DIR` | Set | Set |
| `CLAUDE_CODE_ENTRYPOINT` | Set | Set |
| `CLAUDE_CODE_SSE_PORT` | Set | Set |

**Critical finding:** `CLAUDE_PLUGIN_ROOT` is ONLY set for plugin hooks (defined in plugin's `hooks/hooks.json`), not for global hooks (in `~/.claude/settings.json`).

### 4. Hook Stdin Payload Structure

```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/session.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default|plan|acceptEdits|bypassPermissions",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash|WebFetch|Read|etc",
  "tool_input": { /* tool-specific parameters */ },
  "tool_use_id": "toolu_bdrk_xxx"
}
```

### 5. Versioned Layout Detection Works

The `derive_plugins_dir()` function correctly handles versioned cache layouts:
- Input: `~/.claude/plugins/cache/marketplace/plugin/1.0.0/`
- Output: `~/.claude/plugins/cache/marketplace/` (grandparent)
- Enables cross-plugin route discovery from cache

## Bugs Found and Fixed

### Bug 1: Orphaned Cache State

**Symptom:** `installed_plugins.json` pointed to non-existent directory (`e6beadc27be4/`)

**Cause:** Previous install created cache at commit SHA, later orphaned but JSON not updated

**Fix:**
1. Delete orphaned cache directory
2. Uninstall and reinstall plugin
3. Restart Claude Code

### Bug 2: Outdated Cached Code

**Symptom:** Cached `cli.py` lacked `derive_plugins_dir()` function

**Cause:** Cache was stale copy from before feature was added

**Fix:** Reinstall plugin to get fresh copy with updated code

### Bug 3: Plugin Not Enabled After Reinstall

**Symptom:** After uninstall/reinstall, tool-routing hooks weren't running

**Cause:** Plugin wasn't in `enabledPlugins` in settings.json

**Fix:** Manually add to enabledPlugins or use `/plugin install` again

## Testing Methodology

### Debug Hook Approach

Created a global debug hook to capture stdin and environment variables:

```bash
#!/bin/bash
LOG_FILE="~/.claude/hooks/debug.log"
STDIN_PAYLOAD=$(cat)
{
  echo "TIMESTAMP: $(date)"
  env | grep '^CLAUDE_'
  echo "$STDIN_PAYLOAD" | python3 -m json.tool
} >> "$LOG_FILE"
exit 0
```

**Limitation:** Global hooks don't receive `CLAUDE_PLUGIN_ROOT`, so we also modified the plugin hook to log its environment.

### Verification Commands

```bash
# Check route discovery from cache
CLAUDE_PLUGIN_ROOT="~/.claude/plugins/cache/.../tool-routing/1.0.0" \
  uv run tool-routing list

# Run inline tests
CLAUDE_PLUGIN_ROOT="..." uv run tool-routing test

# Check installed plugins
jq '.plugins["tool-routing@marketplace"]' ~/.claude/plugins/installed_plugins.json
```

## Documentation Created

1. `docs/tests/installation-scenarios.md` - Test scenarios for different install methods
2. `docs/tests/baseline-results.md` - Actual test results with pre/post fix status

## Lessons Learned

1. **Always verify cache exists** - `installed_plugins.json` path may be stale
2. **Directory-source marketplaces still use cache** - Not a symlink/direct reference
3. **Plugin reinstall may not re-enable** - Check `enabledPlugins` after reinstall
4. **Global vs plugin hooks have different env** - `CLAUDE_PLUGIN_ROOT` only in plugin hooks
5. **Debug with logging in the actual hook** - Global debug hook can't see plugin-specific env vars

## Recommendations

### For Plugin Authors

1. Always use `${CLAUDE_PLUGIN_ROOT}` in hook commands, never hardcoded paths
2. Use `derive_plugins_dir()` pattern to support both flat and versioned layouts
3. Consider setting `CLAUDE_PLUGINS_DIR` explicitly as fallback for robustness
4. Document expected environment variables in plugin README

### For Claude Code Team

1. Consider cleaning up stale entries in `installed_plugins.json` on startup
2. Add `CLAUDE_PLUGIN_ROOT` to global hooks for consistency
3. Document cache behavior for directory-source marketplaces
4. Consider auto-enabling plugins after reinstall

## Files Changed

- `~/.claude/plugins/cache/technicalpickles-marketplace/tool-routing/1.0.0/` - Fresh cache created
- `~/.claude/settings.json` - Temporarily added debug hook, then removed
- `plugins/tool-routing/docs/tests/` - New test documentation

## Follow-up Items

- [ ] Consider adding integration test that verifies cross-plugin route discovery
- [ ] Update baseline-results.md with final confirmed values
- [ ] Consider PR to superpowers-marketplace documenting these findings

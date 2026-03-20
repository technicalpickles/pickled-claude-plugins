# Known Claude Code Bugs Affecting Plugins

Bugs in Claude Code that affect plugin development and behavior. These are tracked upstream but worth knowing about when debugging plugin issues.

## 64KB Pipe Truncation

**Issue:** [#36685](https://github.com/anthropics/claude-code/issues/36685), [#31408](https://github.com/anthropics/claude-code/issues/31408) (closed/locked)

`claude plugin list --json` silently truncates at 64KB when captured via subprocess pipe. File redirect produces the full output. With enough plugins installed (~235 across projects), the JSON exceeds 64KB and gets cut off mid-object, producing invalid JSON.

**Impact:** Any code that shells out to `claude plugin list --json` and reads stdout via pipe gets broken silently. This broke tool-routing's route discovery (no routes found, hooks never block).

**Workaround:** Use file-based capture instead of pipe:

```python
# Broken: truncates at 64KB
result = subprocess.run(["claude", "plugin", "list", "--json"],
                        capture_output=True, text=True)
json.loads(result.stdout)  # JSONDecodeError

# Works: file redirect captures full output
with open(tmp_path, "w") as f:
    subprocess.run(["claude", "plugin", "list", "--json"], stdout=f)
json.loads(Path(tmp_path).read_text())  # OK
```

**Root cause (likely):** Node.js stdout flushing. `process.exit()` called before the write buffer (default `highWaterMark`: 64KB) drains to pipe. The constant `65536` appears in multiple places in the codebase (#29088, #35085).

## enabledPlugins Scope Bug

**Issue:** [#27247](https://github.com/anthropics/claude-code/issues/27247)

`enabledPlugins` in settings only works at user scope (`~/.claude/settings.json`). Project (`.claude/settings.json`) and local (`.claude/settings.local.json`) scopes are silently ignored for hook loading.

**Impact:** Plugins installed with `claude plugin install --scope local` (what fitout does) appear in `claude plugin list` but report `enabled: false`. Hooks from these plugins never fire.

**Nuance:** Skills DO load from locally-scoped plugins. Only hooks are affected. So a plugin's skills work fine, but its hooks silently don't.

**Workaround:** Add plugins to `~/.claude/settings.json` enabledPlugins manually:

```json
{
  "enabledPlugins": {
    "tool-routing@pickled-claude-plugins": true,
    "git@pickled-claude-plugins": true
  }
}
```

## Debugging Checklist

When hooks aren't firing, check in this order:

1. **Is the plugin enabled globally?** Check `~/.claude/settings.json` enabledPlugins (not just project/local settings)
2. **Does `claude plugin list --json` produce valid JSON?** Pipe it to `wc -c`. If exactly 65536/65537 bytes, you're hitting the truncation bug.
3. **Did you restart Claude Code?** Hooks are captured at startup.
4. **Is hooks.json formatted correctly?** Run `claude plugin validate <path>` and check the plugin structure tests.

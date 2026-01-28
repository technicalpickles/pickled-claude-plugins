# Baseline Test Results

**Testing Date:** 2025-12-17

This document captures actual test results from investigating tool-routing installation consistency.

---

## Test Environment

- **Machine:** macOS Darwin 24.6.0
- **Claude Code:** Current version
- **Repository:** `/Users/josh.nichols/workspace/pickled-claude-plugins`
- **Marketplace type:** Local directory (`"source": "directory"`)

---

## Scenario 1: Local Development Environment

**Test:** Run tool-routing from local plugin directory

```bash
cd plugins/tool-routing && CLAUDE_PLUGIN_ROOT="$PWD" uv run tool-routing list
```

**Result:** SUCCESS

```
Routes (merged from 5 sources):

bash-cat-heredoc (from: .../plugins/tool-routing/hooks/tool-routes.yaml)
bash-echo-chained (from: .../plugins/tool-routing/hooks/tool-routes.yaml)
bash-echo-redirect (from: .../plugins/tool-routing/hooks/tool-routes.yaml)
tool-routing-manual-test (from: .../plugins/tool-routing/hooks/tool-routes.yaml)
buildkite (from: .../plugins/ci-cd-tools/skills/working-with-buildkite-builds/tool-routes.yaml)
atlassian (from: .../plugins/dev-tools/hooks/tool-routes.yaml)
github-pr (from: .../plugins/git/skills/pull-request/tool-routes.yaml)
git-commit-multiline (from: .../plugins/git/skills/pull-request/tool-routes.yaml)
gh-pr-create-multiline (from: .../plugins/git/skills/pull-request/tool-routes.yaml)
bash-mcp-cli (from: .../plugins/mcpproxy/skills/working-with-mcp/tool-routes.yaml)
bash-mcp-cli (from: .../plugins/mcpproxy/skills/working-with-mcp/tool-routes.yaml)
```

**Analysis:**
- 11 routes from 5 sources discovered correctly
- `derive_plugins_dir()` returns `plugins/` (correct)
- Cross-plugin route discovery works

---

## Scenario 2: Cached Install (Marketplace)

**Test:** Run tool-routing from cached plugin location

```bash
cd ~/.claude/plugins/cache/technicalpickles-marketplace/tool-routing/1.0.0
CLAUDE_PLUGIN_ROOT="$PWD" uv run tool-routing list
```

**Result:** PARTIAL FAILURE

```
Routes (merged from 1 sources):

bash-cat-heredoc (from: .../tool-routing/1.0.0/hooks/tool-routes.yaml)
bash-echo-chained (from: .../tool-routing/1.0.0/hooks/tool-routes.yaml)
bash-echo-redirect (from: .../tool-routing/1.0.0/hooks/tool-routes.yaml)
tool-routing-manual-test (from: .../tool-routing/1.0.0/hooks/tool-routes.yaml)
```

**Analysis:**
- Only 4 routes from 1 source discovered
- `derive_plugins_dir()` logic missing in cached version
- Cached code uses simple `.parent` which returns `tool-routing/` not `marketplace/`
- Cross-plugin route discovery BROKEN

---

## Scenario 3: Orphaned Cache State

**Test:** Check installed_plugins.json vs actual cache

```bash
# Recorded installPath
cat ~/.claude/plugins/installed_plugins.json | grep -A5 tool-routing
```

**Result:** INCONSISTENT

```json
"tool-routing@technicalpickles-marketplace": [
  {
    "installPath": "/Users/josh.nichols/.claude/plugins/cache/technicalpickles-marketplace/tool-routing/e6beadc27be4",
    "version": "e6beadc27be4",
    ...
  }
]
```

**Actual cache:**

```bash
ls ~/.claude/plugins/cache/technicalpickles-marketplace/tool-routing/
# Output: 1.0.0/
```

**Analysis:**
- `installed_plugins.json` references `e6beadc27be4/` (non-existent)
- Cache only contains `1.0.0/` (marked orphaned)
- Claude Code may be failing to load plugin entirely
- Or falling back to orphaned version

---

## Scenario 4: Code Version Comparison

**Test:** Compare local vs cached `cli.py`

**Local version has:**
```python
def derive_plugins_dir(plugin_root: Path) -> Path:
    """Derive plugins directory from plugin root.

    Handles both layouts:
    - Flat: plugins_dir/this-plugin/ -> parent is plugins_dir
    - Versioned: plugins_dir/this-plugin/1.0.0/ -> grandparent is plugins_dir
    """
    # ... smart detection logic
```

**Cached version has:**
```python
def get_all_routes():
    # ...
    plugins_dir_env = os.environ.get("CLAUDE_PLUGINS_DIR", "")
    if plugins_dir_env:
        plugins_dir = Path(plugins_dir_env)
    else:
        # Derive from plugin root: plugin_root/../ is the plugins directory
        plugins_dir = plugin_root.parent  # BUG: Wrong for versioned layout
```

**Analysis:**
- Cached version missing `derive_plugins_dir()` function entirely
- Simple `.parent` logic breaks for versioned cache layout
- This is the root cause of cross-plugin discovery failure

---

## Root Cause Analysis

### Issue 1: Stale Cache

The local directory marketplace creates a copy at install time. Changes to the local repo are NOT reflected in the cache until reinstall.

**Evidence:**
- Local `cli.py` has `derive_plugins_dir()` (lines 32-66)
- Cached `cli.py` lacks this function entirely
- Cache dated Dec 9, local changes made after

### Issue 2: Orphaned Install Path

When a plugin is reinstalled, the old cache directory may be orphaned (marked with `.orphaned_at`) but the JSON may point to a non-existent path.

**Evidence:**
- `installed_plugins.json` → `e6beadc27be4/` (doesn't exist)
- Cache has `1.0.0/` with `.orphaned_at` marker

### Issue 3: Versioned Layout Detection

The cached code assumes flat layout (`plugin_root.parent` = plugins_dir), but the cache uses versioned layout (`marketplace/plugin/version/`).

**Evidence:**
```
Expected: marketplace/tool-routing/1.0.0/ -> derive_plugins_dir() = marketplace/
Actual:   marketplace/tool-routing/1.0.0/ -> .parent = tool-routing/
```

---

## Summary of Failures

| Scenario | Expected | Actual | Root Cause |
|----------|----------|--------|------------|
| Local dev | 5 sources | 5 sources | Works correctly |
| Cached install | 5 sources | 1 source | Missing derive_plugins_dir() |
| Install path | Exists | Missing | Orphaned cache state |
| Code version | Current | Outdated | Cache not updated |

---

## Recommended Fixes

1. **Clean up orphaned cache:**
   ```bash
   rm -rf ~/.claude/plugins/cache/technicalpickles-marketplace/tool-routing/
   ```

2. **Reinstall plugin:**
   ```
   /plugin uninstall tool-routing@technicalpickles-marketplace
   /plugin install tool-routing@technicalpickles-marketplace
   ```

3. **Verify after reinstall:**
   ```bash
   CLAUDE_PLUGIN_ROOT="{new_install_path}" uv run tool-routing list
   # Should show 5+ sources
   ```

4. **Consider setting CLAUDE_PLUGINS_DIR explicitly in hooks.json** as a fallback for robustness.

---

## Testing Status (Post-Fix: 2025-12-17)

| Test | Status | Notes |
|------|--------|-------|
| Local development routes | PASS | 5 sources discovered |
| Cached install routes | N/A | Directory-source marketplaces don't use cache |
| Install path validity | UNCLEAR | `installed_plugins.json` points to non-existent path, but hooks work |
| Code version parity | PASS | Using source directory directly |
| Hook execution | PASS | 32/32 tests pass |
| Cross-plugin discovery | PASS | All 5 sources discovered |

---

## Post-Fix Verification

**Test Run:** 2025-12-17 after plugin reinstall

```bash
CLAUDE_PLUGIN_ROOT="$PWD" CLAUDE_PLUGINS_DIR=".../plugins" uv run tool-routing test
```

**Result:** 32 passed, 0 failed

**Routes discovered from 5 sources:**
1. `tool-routing/hooks/tool-routes.yaml` (4 routes)
2. `ci-cd-tools/skills/working-with-buildkite-builds/tool-routes.yaml` (1 route)
3. `dev-tools/hooks/tool-routes.yaml` (1 route)
4. `git/skills/pull-request/tool-routes.yaml` (5 routes)
5. `mcpproxy/skills/working-with-mcp/tool-routes.yaml` (3 routes)

---

## Key Discovery: Directory-Source Marketplace Behavior

For marketplaces with `"source": "directory"`:

1. **No cache copy created** - Unlike git-based marketplaces
2. **`installed_plugins.json` may have stale data** - Records commit SHA but doesn't create cache directory
3. **Hooks use source directory directly** - `CLAUDE_PLUGIN_ROOT` set to source path
4. **This is actually correct behavior** - Changes to local repo are reflected immediately

**Implication:** For local development with directory-source marketplaces, the `derive_plugins_dir()` function works correctly because:
- `CLAUDE_PLUGIN_ROOT` = `{source_path}/plugins/tool-routing/`
- `derive_plugins_dir()` returns `{source_path}/plugins/`
- Cross-plugin discovery works as expected

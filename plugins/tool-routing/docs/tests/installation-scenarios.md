# Installation Test Scenarios

These scenarios test tool-routing behavior across different installation methods.

## Overview

The tool-routing plugin can be installed via:

1. **Local directory marketplace** - Points to a local git repository
2. **Remote git marketplace** - Cloned from GitHub
3. **Direct local path** - Plugin added from filesystem

Each method affects how `CLAUDE_PLUGIN_ROOT` and route discovery work.

---

## Scenario 1: Local Directory Marketplace Install

**Setup:**

- Marketplace source: `"source": "directory", "path": "/path/to/repo"`
- Plugin location: `plugins/tool-routing/`
- Other plugins: `plugins/git/`, `plugins/ci-cd-tools/`, etc.

**Expected Behavior:**

- `CLAUDE_PLUGIN_ROOT` = marketplace installPath (may be stale if cache orphaned)
- Routes discovered from ALL sibling plugins
- `derive_plugins_dir()` correctly identifies marketplace root

**Test Commands:**

```bash
# List routes - should show 5+ sources
CLAUDE_PLUGIN_ROOT="$PWD/plugins/tool-routing" uv run --project plugins/tool-routing tool-routing list

# Run tests
CLAUDE_PLUGIN_ROOT="$PWD/plugins/tool-routing" uv run --project plugins/tool-routing tool-routing test
```

**Success Criteria:**

- Routes merged from 5+ sources (tool-routing, git, ci-cd-tools, dev-tools, mcpproxy)
- All inline tests pass
- No route conflict errors

---

## Scenario 2: Remote Git Marketplace Install

**Setup:**

- Marketplace source: `"source": "github", "repo": "user/marketplace"`
- Cache location: `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/`
- Version: Semantic version (e.g., `1.0.0`)

**Expected Behavior:**

- Plugin copied to cache (not symlinked)
- `CLAUDE_PLUGIN_ROOT` = cache path
- `derive_plugins_dir()` must handle versioned layout:
  - `{marketplace}/{plugin}/{version}/` -> plugins_dir = `{marketplace}/`

**Test Commands:**

```bash
# From cached location
cd ~/.claude/plugins/cache/{marketplace}/tool-routing/{version}
CLAUDE_PLUGIN_ROOT="$PWD" uv run tool-routing list
```

**Success Criteria:**

- Routes discovered from sibling plugins in same marketplace cache
- Versioned directory layout handled correctly
- `derive_plugins_dir()` returns marketplace root, not plugin directory

**Known Issues:**

- Older versions may lack `derive_plugins_dir()` and use simple `.parent`
- This breaks cross-plugin route discovery in versioned layouts

---

## Scenario 3: Mixed Install Sources

**Setup:**

- Some plugins from remote marketplace (in cache)
- tool-routing from local directory marketplace
- Both should contribute routes

**Expected Behavior:**

- Routes merged from both local and cached plugins
- `CLAUDE_PLUGINS_DIR` env var can override discovery

**Test Commands:**

```bash
# Override plugins dir to include both sources
CLAUDE_PLUGIN_ROOT="$PWD/plugins/tool-routing" \
CLAUDE_PLUGINS_DIR="$HOME/.claude/plugins/cache/my-marketplace" \
uv run --project plugins/tool-routing tool-routing list
```

**Success Criteria:**

- Routes from explicitly set CLAUDE_PLUGINS_DIR are discovered
- No conflicts when same route defined in multiple places (error expected)

---

## Scenario 4: Orphaned Cache State

**Setup:**

- `installed_plugins.json` references non-existent version directory
- Old version marked with `.orphaned_at` file
- Plugin may fail to load or use stale code

**Diagnosis:**

```bash
# Check installed path exists
cat ~/.claude/plugins/installed_plugins.json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['plugins'].get('tool-routing@marketplace', [{}])[0].get('installPath', 'NOT FOUND'))"

# Check if path exists
ls -la /path/from/above

# Check for orphaned markers
find ~/.claude/plugins/cache -name ".orphaned_at"
```

**Expected Failures:**

- Plugin hook fails silently (exit 0, no routes checked)
- Routes not discovered
- Old buggy code executed instead of current version

**Recovery:**

```
/plugin uninstall tool-routing@marketplace
/plugin install tool-routing@marketplace
```

---

## Scenario 5: Version Mismatch

**Setup:**

- Local development has newer code than cached install
- `derive_plugins_dir()` exists locally but not in cache

**Test:**

```bash
# Compare local vs cached versions
diff plugins/tool-routing/src/tool_routing/cli.py \
     ~/.claude/plugins/cache/marketplace/tool-routing/*/src/tool_routing/cli.py
```

**Expected Issues:**

- Cached version may have bugs fixed in local
- Feature parity issues between environments
- Route discovery may work locally but fail when installed

**Success Criteria:**

- After reinstall, cached version matches local
- Both environments discover same routes

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLAUDE_PLUGIN_ROOT` | Plugin's root directory | Set by Claude Code |
| `CLAUDE_PLUGINS_DIR` | Override plugins directory for discovery | Derived from plugin root |
| `CLAUDE_PROJECT_ROOT` | Project root for project-local routes | Current working directory |
| `TOOL_ROUTING_DEBUG` | Enable debug output | false |

---

## Directory Layout Comparison

### Development Layout (Flat)

```
plugins/
├── tool-routing/
│   └── hooks/tool-routes.yaml
├── git/
│   └── skills/pull-request/tool-routes.yaml
└── ci-cd-tools/
    └── skills/working-with-buildkite-builds/tool-routes.yaml
```

`CLAUDE_PLUGIN_ROOT` = `plugins/tool-routing/`
`derive_plugins_dir()` returns `plugins/`

### Installed Layout (Versioned)

```
cache/marketplace/
├── tool-routing/
│   └── 1.0.0/
│       └── hooks/tool-routes.yaml
├── git/
│   └── 1.0.0/
│       └── skills/pull-request/tool-routes.yaml
└── ci-cd-tools/
    └── 1.0.0/
        └── skills/working-with-buildkite-builds/tool-routes.yaml
```

`CLAUDE_PLUGIN_ROOT` = `cache/marketplace/tool-routing/1.0.0/`
`derive_plugins_dir()` should return `cache/marketplace/` (NOT `tool-routing/`)

---

## Testing Checklist

- [ ] Local development: All routes discovered (5+ sources)
- [ ] Cached install: All routes discovered (5+ sources)
- [ ] Orphaned cache: Detected and recovered
- [ ] Version mismatch: Identified and resolved
- [ ] Mixed sources: Routes merged correctly
- [ ] CLAUDE_PLUGINS_DIR override: Works as expected
- [ ] Hook execution: Exit codes correct (0=allow, 2=block)

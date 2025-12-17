# Route Discovery

The tool-routing plugin discovers and merges routes from multiple sources, allowing plugins and projects to contribute their own routing rules.

## Discovery Order

Routes are discovered and merged in this order:

1. **This plugin's routes** - `<plugin_root>/hooks/tool-routes.yaml`
2. **Other plugins' skill-level routes** - `<plugins_dir>/*/skills/*/tool-routes.yaml`
3. **Other plugins' plugin-level routes** - `<plugins_dir>/*/hooks/tool-routes.yaml`
4. **Project-local routes** - `<project_root>/.claude/tool-routes.yaml`

All discovered routes are merged into a single routing table. The order affects which routes are checked first, but any match blocks the call.

## Environment Variables

The plugin uses these environment variables to locate route files:

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLAUDE_PLUGIN_ROOT` | This plugin's directory | Current working directory |
| `CLAUDE_PLUGINS_DIR` | Directory containing all plugins | Derived from plugin root |
| `CLAUDE_PROJECT_ROOT` | Project root for local routes | Current working directory |
| `TOOL_ROUTING_DEBUG` | Enable debug output | (disabled) |

### How Claude Code Sets Environment Variables

**Important:** `CLAUDE_PLUGIN_ROOT` is only set for **plugin hooks** (defined in a plugin's `hooks/hooks.json`), NOT for global hooks (defined in `~/.claude/settings.json`).

When a plugin hook runs:
- `CLAUDE_PLUGIN_ROOT` = Cache path: `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/`
- This is the **cache copy**, not the original source directory

### Directory Layout Detection

The plugin automatically detects whether it's running in:

**Flat layout** (development):
```
plugins/
├── tool-routing/
│   └── hooks/tool-routes.yaml
└── other-plugin/
    └── hooks/tool-routes.yaml
```

**Versioned layout** (installed via marketplace):
```
~/.claude/plugins/cache/marketplace/
├── tool-routing/
│   └── 1.0.0/
│       └── hooks/tool-routes.yaml
└── other-plugin/
    └── 1.0.0/
        └── hooks/tool-routes.yaml
```

The `derive_plugins_dir()` function handles both by checking for sibling plugin directories with version subdirectories.

## Route Sources

### Plugin Routes

Plugins contribute routes by placing a `hooks/tool-routes.yaml` file in their plugin directory:

```
plugins/
├── tool-routing/
│   └── hooks/
│       └── tool-routes.yaml    ← This plugin's routes
├── my-plugin/
│   └── hooks/
│       └── tool-routes.yaml    ← Another plugin's routes
└── other-plugin/
    └── hooks/
        └── tool-routes.yaml    ← Yet another plugin's routes
```

All `hooks/tool-routes.yaml` files found in `$CLAUDE_PLUGINS_DIR/*/` are loaded.

### Skill-Level Routes

Skills can contribute their own routes by placing a `tool-routes.yaml` in the skill directory:

```
plugins/
├── git-workflows/
│   └── skills/
│       └── writing-pull-requests/
│           ├── SKILL.md
│           └── tool-routes.yaml    ← Skill-level routes
```

Skill-level routes are ideal when:
- The route guards or enforces the skill's domain
- The route's message should reference the skill
- The route only makes sense in context of the skill

All `tool-routes.yaml` files found in `$CLAUDE_PLUGINS_DIR/*/skills/*/` are loaded.

### Project Routes

Projects can define local routes in `.claude/tool-routes.yaml`:

```
my-project/
├── .claude/
│   └── tool-routes.yaml    ← Project-specific routes
├── src/
└── ...
```

Project routes let you:
- Block patterns specific to your codebase
- Redirect to project-specific tools or workflows
- Enforce team conventions

### Example Project Routes

```yaml
# .claude/tool-routes.yaml
routes:
  # Block fetching internal docs - use local copies
  internal-docs:
    tool: WebFetch
    pattern: "docs\\.internal\\.mycompany\\.com"
    message: |
      Internal docs are available locally.

      Use: Read("docs/internal/...")
    tests:
      - input:
          tool_name: WebFetch
          tool_input:
            url: "https://docs.internal.mycompany.com/api"
        expect: block

  # Enforce team commit convention
  no-wip-commits:
    tool: Bash
    pattern: "git\\s+commit.*-m\\s+[\"']WIP"
    message: |
      Don't commit with WIP messages.

      Use a descriptive commit message instead.
    tests:
      - input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"WIP: stuff\""
        expect: block
      - input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"Add feature X\""
        expect: allow
```

## Route Merging

### How Merging Works

Routes from all sources are combined into a single dictionary keyed by route name:

```
Source 1: {github-pr: ..., atlassian: ...}
Source 2: {my-route: ...}
Source 3: {project-route: ...}
         ↓
Merged:  {github-pr: ..., atlassian: ..., my-route: ..., project-route: ...}
```

Each route retains a `source` field indicating which file it came from.

### Conflict Detection

If two sources define a route with the same name, the plugin raises a `RouteConflictError`:

```
Configuration error: Route 'github-pr' defined in multiple sources:
  '/path/to/plugins/tool-routing/hooks/tool-routes.yaml' and
  '/path/to/project/.claude/tool-routes.yaml'
```

**To resolve conflicts:**
- Rename one of the routes to be unique
- Remove the duplicate definition

Route names must be globally unique across all sources.

### Fail-Open Behavior

The plugin is designed to fail open - if something goes wrong, tool calls are allowed rather than blocked:

| Scenario | Behavior |
|----------|----------|
| YAML parse error | Route file skipped, other routes still work |
| Missing route file | File skipped silently |
| Invalid regex pattern | Route skipped, logs warning |
| Route conflict error | Error logged, all routes skipped |
| JSON parse error (stdin) | Tool call allowed |

This prevents configuration errors from breaking your workflow.

## Viewing Merged Routes

Use `tool-routing list` to see all routes and their sources:

```bash
cd plugins/tool-routing
uv run tool-routing list
```

Output:

```
Routes (merged from 2 sources):

github-pr (from: /path/to/plugins/tool-routing/hooks/tool-routes.yaml)
  tool: WebFetch
  pattern: github\.com/[^/]+/[^/]+/pull/\d+
  tests: 3

atlassian (from: /path/to/plugins/tool-routing/hooks/tool-routes.yaml)
  tool: WebFetch
  pattern: https?://[^/]*\.atlassian\.net
  tests: 2

project-route (from: /path/to/project/.claude/tool-routes.yaml)
  tool: Bash
  pattern: ...
  tests: 1
```

## Debugging Route Discovery

Enable debug mode to see which routes match:

```bash
export TOOL_ROUTING_DEBUG=1
```

When a route blocks a call, debug output shows:

```
❌ Tool Routing: github-pr
Matched: https://github.com/foo/bar/pull/123
Pattern: github\.com/[^/]+/[^/]+/pull/\d+

Use `gh pr view <number>` for GitHub PRs.
...
```

## Best Practices

### For Plugin Authors

1. **Use descriptive route names** - Prefix with your plugin name if generic: `myplugin-no-curl`
2. **Include comprehensive tests** - Cover both block and allow cases
3. **Write helpful messages** - Explain why and what to do instead
4. **Avoid overly broad patterns** - Be specific to minimize false positives

### For Project Routes

1. **Document your routes** - Add comments explaining team conventions
2. **Keep routes focused** - One concern per route
3. **Test locally first** - Run `tool-routing test` before committing
4. **Coordinate with plugins** - Avoid naming conflicts with installed plugins

## Troubleshooting

### Routes Not Being Discovered

**Symptom:** `tool-routing list` shows fewer sources than expected.

**Common causes:**

1. **Stale plugin cache** - The installed plugin cache may be outdated
   ```bash
   # Check cache version
   ls ~/.claude/plugins/cache/{marketplace}/tool-routing/

   # Fix: Reinstall the plugin
   /plugin uninstall tool-routing@{marketplace}
   /plugin install tool-routing@{marketplace}
   ```

2. **Orphaned cache directory** - `installed_plugins.json` may point to non-existent path
   ```bash
   # Check if install path exists
   jq '.plugins["tool-routing@marketplace"][0].installPath' ~/.claude/plugins/installed_plugins.json
   ls -la /path/from/above

   # Fix: Delete stale cache and reinstall
   rm -rf ~/.claude/plugins/cache/{marketplace}/tool-routing/
   /plugin uninstall tool-routing@{marketplace}
   /plugin install tool-routing@{marketplace}
   ```

3. **Plugin not enabled** - Check settings.json
   ```bash
   jq '.enabledPlugins["tool-routing@marketplace"]' ~/.claude/settings.json
   # Should return: true
   ```

### Hook Not Running

**Symptom:** Tool calls that should be blocked are allowed through.

**Diagnostic steps:**

1. **Verify plugin is installed and enabled**
   ```bash
   jq '.plugins | keys | map(select(contains("tool-routing")))' ~/.claude/plugins/installed_plugins.json
   jq '.enabledPlugins | keys | map(select(contains("tool-routing")))' ~/.claude/settings.json
   ```

2. **Check cache directory exists**
   ```bash
   ls ~/.claude/plugins/cache/{marketplace}/tool-routing/
   ```

3. **Test route discovery manually**
   ```bash
   CLAUDE_PLUGIN_ROOT="~/.claude/plugins/cache/{marketplace}/tool-routing/{version}" \
     uv run --project "$CLAUDE_PLUGIN_ROOT" tool-routing list
   ```

4. **Restart Claude Code** - Hooks are loaded at startup

### Version Mismatch Between Source and Cache

For directory-source marketplaces, the cache is a **copy** made at install time. Changes to the source directory require reinstalling:

```bash
/plugin uninstall tool-routing@{marketplace}
/plugin install tool-routing@{marketplace}
# Then restart Claude Code
```

**Note:** This is different from git-based marketplaces, which also create copies but track versions via git tags.

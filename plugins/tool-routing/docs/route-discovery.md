# Route Discovery

The tool-routing plugin discovers and merges routes from multiple sources using manifest-driven discovery. Each plugin declares its route files in a manifest, and the plugin uses Claude's CLI to find enabled plugins.

## How Discovery Works

Route discovery follows this process:

1. **Query Claude CLI** - Run `claude plugin list --json` to get all enabled plugins
2. **Read manifests** - For each enabled plugin, read `.claude-plugin/routes.json`
3. **Load route files** - Load each declared `tool-routes.yaml` file
4. **Merge routes** - Combine all routes into a single routing table

This approach is reliable because:
- No glob patterns or path guessing
- Respects plugin enabled/disabled state
- Works with any directory layout

## Route Manifest

Plugins declare their route files in `.claude-plugin/routes.json`:

```json
{
  "routes": [
    "./hooks/tool-routes.yaml",
    "./skills/my-skill/tool-routes.yaml"
  ]
}
```

Paths are relative to the plugin root directory.

### Example Structures

**Plugin with hook-level routes:**
```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json
│   └── routes.json       ← {"routes": ["./hooks/tool-routes.yaml"]}
└── hooks/
    └── tool-routes.yaml
```

**Plugin with skill-level routes:**
```
git/
├── .claude-plugin/
│   ├── plugin.json
│   └── routes.json       ← {"routes": ["./skills/pull-request/tool-routes.yaml"]}
└── skills/
    └── pull-request/
        ├── SKILL.md
        └── tool-routes.yaml
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `TOOL_ROUTING_ROUTES` | Explicit route file paths (comma-separated) | (uses discovery) |
| `CLAUDE_PROJECT_ROOT` | Project root for filtering local-scoped plugins | Current directory |
| `TOOL_ROUTING_DEBUG` | Enable debug output | (disabled) |

### Testing with Explicit Routes

For local development and testing, bypass Claude CLI discovery by setting `TOOL_ROUTING_ROUTES`:

```bash
# Single file
TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml" uv run tool-routing list

# Multiple files
TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml,../git/skills/pull-request/tool-routes.yaml" \
  uv run tool-routing list
```

## Route Sources

### Plugin Routes

Plugins contribute routes by:
1. Creating a `tool-routes.yaml` file
2. Declaring it in `.claude-plugin/routes.json`

```yaml
# hooks/tool-routes.yaml
routes:
  github-pr:
    tool: WebFetch
    pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"
    message: |
      Use `gh pr view <number>` for GitHub PRs.
```

### Skill-Level Routes

Skills can contribute routes specific to their domain:

```yaml
# skills/pull-request/tool-routes.yaml
routes:
  pr-fetch-url:
    tool: WebFetch
    pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"
    message: |
      Use the git:pull-request skill instead of fetching PR URLs.
```

Skill-level routes are ideal when:
- The route guards or enforces the skill's domain
- The route's message should reference the skill
- The route only makes sense in context of the skill

## Route Merging

### How Merging Works

Routes from all sources are combined into a single dictionary keyed by route name:

```
Plugin A: {github-pr: ..., atlassian: ...}
Plugin B: {buildkite: ...}
         ↓
Merged:  {github-pr: ..., atlassian: ..., buildkite: ...}
```

Each route retains a `source` field indicating which file it came from.

### Conflict Detection

If two sources define a route with the same name, the plugin raises a `RouteConflictError`:

```
Configuration error: Route 'github-pr' defined in multiple sources:
  '/path/to/plugin-a/hooks/tool-routes.yaml' and
  '/path/to/plugin-b/hooks/tool-routes.yaml'
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
| Claude CLI fails | No routes loaded, all calls allowed |

This prevents configuration errors from breaking your workflow.

## Viewing Merged Routes

Use `tool-routing list` to see all routes and their sources:

```bash
cd plugins/tool-routing
uv run tool-routing list
```

Output:

```
Routes (merged from 3 sources):

github-pr (from: /path/to/tool-routing/hooks/tool-routes.yaml)
  tool: WebFetch
  pattern: github\.com/[^/]+/[^/]+/pull/\d+
  tests: 3

pr-create (from: /path/to/git/skills/pull-request/tool-routes.yaml)
  tool: Bash
  pattern: gh pr create
  tests: 2
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

1. **Add routes.json manifest** - Declare all route files explicitly
2. **Use descriptive route names** - Prefix with your plugin name if generic
3. **Include comprehensive tests** - Cover both block and allow cases
4. **Write helpful messages** - Explain why and what to do instead
5. **Avoid overly broad patterns** - Be specific to minimize false positives

### Adding Routes to a Plugin

1. Create your `tool-routes.yaml` file
2. Create `.claude-plugin/routes.json` if it doesn't exist
3. Add your route file path to the `routes` array
4. Reinstall the plugin to update the cache

## Troubleshooting

### Routes Not Being Discovered

**Symptom:** `tool-routing list` shows fewer sources than expected.

**Common causes:**

1. **Missing routes.json manifest** - Ensure `.claude-plugin/routes.json` exists
   ```bash
   cat ~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/.claude-plugin/routes.json
   ```

2. **Plugin not enabled** - Check with Claude CLI
   ```bash
   claude plugin list --json | jq '.[] | select(.enabled == true) | .id'
   ```

3. **Project path mismatch (local-scoped plugins)** - Local-scoped plugins use **exact path matching**. The plugin's `projectPath` must exactly equal `CLAUDE_PROJECT_ROOT` (or cwd if unset).

   Check the plugin's project path:
   ```bash
   claude plugin list --json | jq '.[] | select(.id | contains("your-plugin")) | {id, enabled, scope, projectPath}'
   ```

   If running from a subdirectory of the scoped project:
   ```bash
   # Won't work - cwd is plugins/tool-routing but plugin is scoped to repo root
   cd plugins/tool-routing
   uv run tool-routing list

   # Works - explicitly set project root
   CLAUDE_PROJECT_ROOT="/path/to/repo" uv run tool-routing list

   # Or run from repo root
   cd /path/to/repo
   uv run --directory plugins/tool-routing tool-routing list
   ```

4. **Stale plugin cache** - Reinstall the plugin
   ```bash
   /plugin uninstall {plugin}@{marketplace}
   /plugin install {plugin}@{marketplace}
   # Then restart Claude Code
   ```

### Hook Not Running

**Symptom:** Tool calls that should be blocked are allowed through.

**Diagnostic steps:**

1. **Test route discovery manually**
   ```bash
   TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml" uv run tool-routing list
   ```

2. **Verify the route pattern matches**
   ```bash
   TOOL_ROUTING_ROUTES="./hooks/tool-routes.yaml" uv run tool-routing test
   ```

3. **Restart Claude Code** - Hooks are loaded at startup

### Version Mismatch Between Source and Cache

Changes to plugin source require reinstalling:

```bash
/plugin uninstall {plugin}@{marketplace}
/plugin install {plugin}@{marketplace}
# Then restart Claude Code
```

The cache is a copy made at install time, not a live reference.

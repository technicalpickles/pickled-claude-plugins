# Claude Code Plugins Monorepo

This repository contains Claude Code plugins for the `technicalpickles-marketplace`.

## Repository Structure

```
plugins/
├── tool-routing/     # Intercepts tool calls and suggests better alternatives
├── git-workflows/    # GitHub PR and commit workflows
├── ci-cd-tools/      # Buildkite and CI/CD integrations
├── dev-tools/        # Developer utilities (mise, scratch areas, etc.)
├── mcpproxy/         # MCP server management
└── working-in-monorepos/  # Monorepo command execution
```

## Development vs Installation

### Local Development

When working in this repo, plugins are at `plugins/{name}/`. Environment:
- Flat layout: `plugins_dir/plugin-name/hooks/`
- Use `CLAUDE_PLUGIN_ROOT="$PWD/plugins/{name}"` for testing

### Installed (via Marketplace)

When installed, plugins are copied to cache. Environment:
- Versioned layout: `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/`
- `CLAUDE_PLUGIN_ROOT` is set automatically by Claude Code

### Key Difference

**Changes to local source require reinstall to take effect:**
```bash
/plugin uninstall {plugin}@technicalpickles-marketplace
/plugin install {plugin}@technicalpickles-marketplace
# Restart Claude Code
```

## Plugin Testing

### Test tool-routing routes

```bash
# From repo root
cd plugins/tool-routing
CLAUDE_PLUGIN_ROOT="$PWD" CLAUDE_PLUGINS_DIR="../" uv run tool-routing test
```

### Verify cross-plugin route discovery

```bash
CLAUDE_PLUGIN_ROOT="$PWD" CLAUDE_PLUGINS_DIR="../" uv run tool-routing list
# Should show routes from multiple plugins
```

## Common Issues

### Plugin hooks not running after code changes

The marketplace uses `"source": "directory"` but still **copies** to cache at install time.

**Fix:** Reinstall and restart Claude Code.

### Routes only discovered from one source

The `derive_plugins_dir()` function may not be finding sibling plugins.

**Check:**
```bash
# Verify all plugins are in cache
ls ~/.claude/plugins/cache/technicalpickles-marketplace/
```

### `installed_plugins.json` points to non-existent path

This can happen with directory-source marketplaces.

**Fix:**
```bash
rm -rf ~/.claude/plugins/cache/technicalpickles-marketplace/{plugin}/
/plugin uninstall {plugin}@technicalpickles-marketplace
/plugin install {plugin}@technicalpickles-marketplace
```

## Environment Variables

| Variable | Set By | Purpose |
|----------|--------|---------|
| `CLAUDE_PLUGIN_ROOT` | Claude Code (plugin hooks only) | Plugin's cache directory |
| `CLAUDE_PLUGINS_DIR` | tool-routing (derived) | Parent directory for cross-plugin discovery |
| `CLAUDE_PROJECT_DIR` | Claude Code | Current project directory |

**Note:** `CLAUDE_PLUGIN_ROOT` is NOT set for global hooks in `~/.claude/settings.json`.

## Documentation

- `plugins/tool-routing/docs/route-discovery.md` - How routes are found and merged
- `plugins/tool-routing/docs/tests/` - Test scenarios and baseline results
- `plugins/tool-routing/docs/retrospectives/` - Investigation notes

## Contributing

1. Make changes to plugin source in `plugins/{name}/`
2. Test locally with appropriate env vars
3. Commit and push
4. Reinstall plugin to update cache

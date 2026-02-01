# Claude Code Plugins Monorepo

This repository contains Claude Code plugins for the `technicalpickles-marketplace`.

## Repository Structure

```
plugins/
├── tool-routing/     # Intercepts tool calls and suggests better alternatives
├── git/              # Git workflow tools (commits, PRs, inbox, checkout, triage)
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

## Plugin Internal Structure

Each plugin follows this structure:

```
plugins/{name}/
├── .claude-plugin/
│   └── plugin.json       # Manifest with name, description (NO version - see Versioning)
├── commands/
│   └── {command}.md      # FLAT files: commands/commit.md (NOT commands/commit/COMMAND.md)
├── skills/
│   └── {skill}/
│       └── SKILL.md      # NESTED: skills/commit/SKILL.md
├── hooks/
│   └── {hook-type}.{ext} # Hook scripts (e.g., PreToolUse.sh)
└── README.md
```

**Critical distinction:**
- **Commands**: Flat files → `commands/{name}.md`
- **Skills**: Nested directories → `skills/{name}/SKILL.md`

Commands are user-invocable wrappers that reference skills. Skills contain the actual workflow logic.

## Versioning

Versions live in `.claude-plugin/marketplace.json` only (not in plugin.json files).

**Commits must use conventional format:** `type(scope): description`

```bash
feat(git): add stash support     # → minor bump
fix(ci-cd-tools): handle timeout # → patch bump
chore: update deps               # → no bump
```

Version bumps happen automatically when PRs are approved.

→ Full details: [`docs/versioning.md`](docs/versioning.md)

## Documentation

- [`docs/versioning.md`](docs/versioning.md) - How plugin versions are managed
- `plugins/tool-routing/docs/route-discovery.md` - How routes are found and merged
- `plugins/tool-routing/docs/tests/` - Test scenarios and baseline results
- `plugins/tool-routing/docs/retrospectives/` - Investigation notes

## Contributing

1. Create a branch from `main`
2. Make changes to plugin source in `plugins/{name}/`
3. Test locally with appropriate env vars
4. Commit using conventional format: `feat(plugin): description`
5. Create PR - CI validates commits and reports required bumps
6. Get PR approved - versions auto-bump
7. Merge

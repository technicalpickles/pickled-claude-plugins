# Claude Code Plugins Monorepo

This repository contains Claude Code plugins for the `pickled-claude-plugins`.

## Repository Structure

```
plugins/
└── {name}/   # One directory per local plugin. Canonical list: README.md "## Plugins" (generated).
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
/plugin uninstall {plugin}@pickled-claude-plugins
/plugin install {plugin}@pickled-claude-plugins
# Restart Claude Code
```

## Plugin Testing

### Test tool-routing routes

```bash
# From repo root - CLAUDE_PROJECT_ROOT must match where plugin is scoped
CLAUDE_PROJECT_ROOT="$PWD" uv run --directory plugins/tool-routing tool-routing test
```

### Verify cross-plugin route discovery

```bash
# From repo root
CLAUDE_PROJECT_ROOT="$PWD" uv run --directory plugins/tool-routing tool-routing list
# Shows routes from enabled plugins with routes.json manifests
```

**Important:** The tool-routing plugin uses manifest-driven discovery via `claude plugin list --json`. Local-scoped plugins are only discovered when `CLAUDE_PROJECT_ROOT` (or cwd) **exactly matches** the plugin's `projectPath`.

## Common Issues

### Plugin hooks not running after code changes

The marketplace uses `"source": "directory"` but still **copies** to cache at install time.

**Fix:** Reinstall and restart Claude Code.

### Routes only discovered from one source

Discovery uses `claude plugin list --json` and filters by enabled status and project path.

**Check:**
```bash
# See which plugins are enabled and their project paths
claude plugin list --json | jq '.[] | select(.enabled) | {id, scope, projectPath}'

# Verify routes.json exists in cache
ls ~/.claude/plugins/cache/pickled-claude-plugins/*/latest/.claude-plugin/routes.json
```

**Common cause:** Running from a subdirectory (e.g., `plugins/tool-routing/`) when plugins are scoped to the repo root. Local-scoped plugins require exact `projectPath` match.

### `installed_plugins.json` points to non-existent path

This can happen with directory-source marketplaces.

**Fix:**
```bash
rm -rf ~/.claude/plugins/cache/pickled-claude-plugins/{plugin}/
/plugin uninstall {plugin}@pickled-claude-plugins
/plugin install {plugin}@pickled-claude-plugins
```

## Environment Variables

| Variable | Set By | Purpose |
|----------|--------|---------|
| `CLAUDE_PLUGIN_ROOT` | Claude Code (plugin hooks only) | Plugin's cache directory |
| `CLAUDE_PROJECT_ROOT` | tool-routing CLI | Project root for filtering local-scoped plugins |
| `TOOL_ROUTING_ROUTES` | Manual (testing) | Explicit route file paths, bypasses discovery |
| `TOOL_ROUTING_DEBUG` | Manual | Enable debug output for route matching |

**Note:** `CLAUDE_PLUGIN_ROOT` is NOT set for global hooks in `~/.claude/settings.json`.

## Plugin Internal Structure

Each plugin follows this structure:

```
plugins/{name}/
├── .claude-plugin/
│   └── plugin.json       # Manifest with name, description (NO version - see Versioning)
├── skills/
│   └── {skill}/
│       └── SKILL.md      # NESTED: skills/commit/SKILL.md
├── hooks/
│   └── {hook-type}.{ext} # Hook scripts (e.g., PreToolUse.sh)
└── README.md
```

**User-invocable actions go in `skills/{name}/SKILL.md`.** Claude Code surfaces skills for `/plugin:skill` invocation; plugin `commands/{name}.md` files are not surfaced and should not be used. If you find `commands/` directories in existing plugins, they are dead code: convert to skills. The `description:` field in SKILL.md frontmatter is what triggers the skill, so write it as a "use when X" sentence.

## Versioning

Versions live in `.claude-plugin/marketplace.json` only (not in plugin.json files).

**Commits must use conventional format:** `type(scope): description`

```bash
feat(git): add stash support     # → minor bump
fix(ci-cd-tools): handle timeout # → patch bump
chore: update deps               # → no bump
```

### Commit Scope Rules

Scope must match `[a-z0-9-]+` (lowercase letters, numbers, hyphens only).

**`feat`, `fix`, and `perf` REQUIRE a scope** (they change a specific plugin). The scope is a plugin name, or `repo` for repo-wide changes. `chore`, `ci`, `docs`, `style`, `test`, `refactor`, `build`, and `revert` may omit the scope. Enforced by `scripts/check-commit-scope.sh`.

**Valid scopes:**
- `feat(git): ...` - single plugin name
- `fix(ci-cd-tools): ...` - plugin with hyphens
- `feat(repo): ...` - repo-wide change that isn't plugin-specific (tooling, CI, scripts)
- `docs: ...` / `chore: ...` - no scope (non-functional types may omit it)

**Invalid scopes:**
- `fix: ...` - bare `feat`/`fix`/`perf` without a scope is rejected (use `fix(repo): ...`)
- `fix(ci-cd-tools,dev-tools): ...` - commas not allowed
- `fix(CI-CD): ...` - uppercase not allowed

For changes touching multiple plugins, either:
1. Use the `repo` scope: `fix(repo): use markdown links in skills`
2. Make separate commits per plugin

**Bump versions in your PR.** Run `./scripts/bump-version.sh --auto` to apply the bumps that conventional commits imply, then commit the result as `chore(plugin): bump version to X.Y.Z`. The Version Check workflow blocks merge until pending bumps are applied.

→ Full details: [`docs/versioning.md`](docs/versioning.md)

The root README's `## Plugins` table is generated from `marketplace.json` by
`scripts/generate-plugin-table.sh`. Adding, removing, or re-describing a plugin means
regenerating it (`./scripts/generate-plugin-table.sh`, or `bump-version.sh --auto`).
The `plugin-list-check.yml` workflow blocks merge until the committed table matches.

## Documentation

- [`docs/versioning.md`](docs/versioning.md) - How plugin versions are managed
- `plugins/tool-routing/docs/route-discovery.md` - How routes are found and merged
- `plugins/tool-routing/docs/tests/` - Test scenarios and baseline results
- `plugins/tool-routing/docs/retrospectives/` - Investigation notes

## Skill Authoring

### Referencing Files in Skills

In SKILL.md files, use standard markdown links to reference other files:

```markdown
# Correct - standard markdown link
See [references/index.md](references/index.md) for complete list.

# Wrong - @ imports only work in CLAUDE.md, not SKILL.md
See `@references/index.md` for complete list.
```

The `@path/to/file` import syntax is a CLAUDE.md-specific feature. In SKILL.md files, Claude reads linked files on demand using progressive disclosure.

## Contributing

1. Create a branch from `main`
2. Make changes to plugin source in `plugins/{name}/`
3. Test locally with appropriate env vars
4. Commit using conventional format: `feat(plugin): description`
5. Run `./scripts/bump-version.sh --auto` (also regenerates the README plugin table) and commit as `chore(plugin): bump version to X.Y.Z`
6. Create PR - CI validates commits and that pending bumps are applied
7. Merge once green and approved

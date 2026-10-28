# Claude Code Plugins Monorepo

This repository contains Claude Code plugins for the `pickled-claude-plugins`.

## Repository Structure

```
plugins/
└── {name}/   # One directory per local plugin. Canonical list: README.md "## Plugins" (generated).
```

## Development vs Installation

Installed plugins are copied to `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/`, so **changes to local source take effect only after a reinstall and a Claude Code restart**:
```bash
/plugin uninstall {plugin}@pickled-claude-plugins
/plugin install {plugin}@pickled-claude-plugins
```
To run a hook against local source, set `CLAUDE_PLUGIN_ROOT="$PWD/plugins/{name}"` (Claude Code sets it automatically for installed plugins).

If `installed_plugins.json` points at a path that doesn't exist (seen with directory-source marketplaces), `rm -rf ~/.claude/plugins/cache/pickled-claude-plugins/{plugin}/` and reinstall.

Changing a `routes.json` or `tool-routes.yaml`? Test it with the tool-routing CLI: [`plugins/tool-routing/docs/route-discovery.md`](plugins/tool-routing/docs/route-discovery.md) covers `tool-routing test`/`list`, `CLAUDE_PROJECT_ROOT`, and why local-scoped plugins need an exact `projectPath` match.

## Shell scripts must run on bash 3.2

macOS ships `/bin/bash` 3.2, and `#!/usr/bin/env bash` can resolve to it even with a newer Homebrew bash installed. So no `declare -A`, `mapfile`, `${var,,}`, `|&`, etc. — use parallel indexed arrays or a delimited string instead of associative arrays. `./scripts/check-bash-compat.sh` flags these (CI and the hk pre-commit hook run it); test locally with `/bin/bash path/to/script`. It can't catch `"${arr[@]}"` on an empty array under `set -u`, which also errors on bash < 4.4.

## Environment Variables

`CLAUDE_PLUGIN_ROOT` (the plugin's cache directory) is set for plugin hooks only, NOT for global hooks in `~/.claude/settings.json`.

**Hooks/plugins reading user-level config must honor `CLAUDE_CONFIG_DIR`.** It's undocumented (not in Claude Code's env-vars/settings docs as of 2026-07) but honored in practice, and it *replaces* `~/.claude` rather than adding to it; it accepts a single dir or a `:`/`,`-separated list to search in order. Resolve as `$CLAUDE_CONFIG_DIR` (split on `[:,]`) or `[$HOME/.claude]`; don't hardcode `$HOME/.claude`, or config lookup silently breaks the day a user relocates their config dir. See `plugins/writing-tools/src/writing_tools/config.py`'s `_user_config_dirs()` for a working implementation (PR #102).

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

**User-invocable actions go in `skills/{name}/SKILL.md`.** Plugin `commands/{name}.md` files still show up as slash commands, but new work goes in skills, and an existing command gets converted when you next change it. The `description:` field in SKILL.md frontmatter is what triggers the skill, so write it as a "use when X" sentence.

### Naming Gotchas

- **Skill names are globally unique across all installed plugins** (Claude Code surfaces skills by their bare `name:` slug, not `plugin:name`). Two plugins shipping a skill called `doctor` collide. Prefix the directory and `name:` field with the plugin name: `plugins/actually-lsp/skills/actually-lsp-doctor/SKILL.md` with `name: actually-lsp-doctor`, not `skills/doctor/SKILL.md` with `name: doctor`. Some existing plugins (agent-meta) ship generic-named skills and got away with it only because the names happened to be unique; don't rely on that for new plugins.
- **Don't ship a `commands/{name}.md` with the same name as a `skills/{name}/SKILL.md`.** A same-name collision suppresses the SKILL.md content injection that normally follows a Skill tool invocation, forcing the model to grep/read the file manually or hallucinate its contents. If a skill already exists at `skills/{name}/`, either give any slash-command wrapper a different name or drop it entirely: direct Skill invocation via keyword match or `/plugin:skill-name` is sufficient. Slash-command wrappers pointing at skills are a legacy pattern from before skills were directly slash-callable.

## claude.ai Skills

Ports of Claude Code skills to claude.ai Skills (the chat product's format, uploaded as a zip by hand) live at `plugins/{name}/claude-ai-skills/{skill}/`. They are **not** plugin skills: no `plugin.json` or marketplace entry, not in the README table. Commits touching one still use the plugin's name as scope, so they still bump that plugin's version; that's expected.

Details, the build script, and the porting checklist: [`docs/claude-ai-skill-porting.md`](docs/claude-ai-skill-porting.md)

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
- `fix(plugin): ...` / `chore(plugin): ...` - literal `plugin` is not a scope; use the actual plugin name (e.g. `chore(actually-lsp): ...`)

For changes touching multiple plugins, either:
1. Use the `repo` scope: `fix(repo): use markdown links in skills`
2. Make separate commits per plugin

**Bump versions in your PR.** Run `./scripts/bump-version.sh --auto` to apply the bumps that conventional commits imply, then commit the result as `chore({plugin}): bump version to X.Y.Z` — `{plugin}` is the actual plugin name being bumped (e.g. `chore(actually-lsp): bump version to 0.7.1`), not the literal word `plugin`. The Version Check workflow blocks merge until pending bumps are applied.

→ Full details: [`docs/versioning.md`](docs/versioning.md)

The root README's `## Plugins` table is generated from `marketplace.json` by
`scripts/generate-plugin-table.sh`. Adding, removing, or re-describing a plugin means
regenerating it (`./scripts/generate-plugin-table.sh`, or `bump-version.sh --auto`).
The `plugin-list-check.yml` workflow blocks merge until the committed table matches.

## Documentation

- [`docs/versioning.md`](docs/versioning.md) - How plugin versions are managed
- [`docs/claude-ai-skill-porting.md`](docs/claude-ai-skill-porting.md) - How claude.ai Skills (a separate product from Claude Code plugins) are structured and built
- [`plugins/tool-routing/docs/route-discovery.md`](plugins/tool-routing/docs/route-discovery.md) - How routes are found and merged

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

### Description Tuning Has a Structural Ceiling

A skill's description controls whether Claude invokes it, but for some skills no amount of description tuning closes the gap: skills wrapping a CLI Claude already knows (`gh`, `kubectl`, `git`, `npm`), and even some skills wrapping nothing built-in, can sit at or near 0% recall on eval sets regardless of description quality. Claude defaults to handling the query with its own tools rather than reaching for the skill.

If recall stays low across description revisions with no precision regression, the gap is structural, not a description bug. Cheapest fix first:

1. **Name the skill in always-loaded context.** Measured 2026-08-14 on `second-brain:capture` (a novel workflow, not a wrapped CLI): with a pointer section in CLAUDE.md naming the skill, 70-100% recall; with that section removed and nothing else changed, 0/10, zero triggers, on direct prompts. The description may contribute close to nothing; the pointer can be the whole mechanism. For a plugin, put the pointer in the scaffolded CLAUDE.md template so it ships with the plugin rather than being hand-written per project. Caveat: the pointer only catches intents it names explicitly.
2. **Hook-based intercept** (e.g. `PreToolUse` on the CLI command the skill wraps), reach for this only after the pointer, since it's new surface to maintain.
3. **Real-use data.** Eval prompts may not match how users actually phrase requests; ship and watch.
4. **Stop tuning the description** past this point; diminishing or zero returns.

See `plugins/buildkite/skills/investigating-builds/evals/README.md` for the eval-loop mechanics this is layered on top of.

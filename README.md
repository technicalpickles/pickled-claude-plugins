# Pickled Claude Plugins

Personal plugin marketplace for Claude Code with curated skills, commands, and hooks organized by domain.

## Repository Structure

```
pickled-claude-plugins/
├── .claude-plugin/
│   ├── plugin.json           # Root marketplace metadata
│   └── marketplace.json      # Plugin registry
├── plugins/
│   ├── working-in-monorepos/ # Monorepo navigation and tooling
│   ├── git/                  # Git workflow tools
│   ├── ci-cd-tools/          # CI/CD pipeline tools
│   ├── dev-tools/            # Developer productivity utilities
│   ├── second-brain/         # Obsidian vault integration
│   └── tool-routing/         # Tool call interception and routing
└── docs/
```

## Installation

### Add the Marketplace

```bash
/plugin marketplace add technicalpickles/pickled-claude-plugins
```

### Install a Plugin

```bash
/plugin install <plugin-name>@pickled-claude-plugins
```

For example:

```bash
/plugin install git@pickled-claude-plugins
/plugin install dev-tools@pickled-claude-plugins
```

See individual plugin READMEs for details on what each plugin provides.

## Plugins

### working-in-monorepos

Navigate and execute commands in monorepo subprojects with proper directory handling.

**Features:**
- Auto-detection of monorepo structure via SessionStart hook
- `/monorepo-init` command for manual configuration
- Subproject type detection (Node, Ruby, Go, Python, Rust, Java)

**Skills:** working-in-monorepos

### git

Git workflow tools: commits, PRs, review inbox, checkout, and work triage.

**Skills:** commit, pull-request, inbox, checkout, triage

### ci-cd-tools

CI/CD pipeline tools and integrations.

**Skills:** buildkite-status

### debugging-tools

Tools for debugging and troubleshooting applications.

**Skills:** scope, mcpproxy-debug

### dev-tools

Developer productivity tools and utilities.

**Skills:** working-in-scratch-areas

### second-brain

Knowledge management for Obsidian vaults. Capture insights from conversations, process voice transcriptions, and connect repos to your vault.

**Commands:** setup, insight, distill-conversation, process-daily, link-project

**Skills:** obsidian (with PARA, Zettelkasten, note-patterns references)

See [second-brain/README.md](plugins/second-brain/README.md) for full documentation.

### tool-routing

Intercepts tool calls and suggests better alternatives.

**Commands:** validate

See [tool-routing/README.md](plugins/tool-routing/README.md) for full documentation.

## Usage

### Using Skills

Skills are available in Claude Code via the Skill tool:

```
Use the technicalpickles:working-in-monorepos skill
```

Or reference them in custom skills:

```markdown
@technicalpickles:buildkite-status for checking CI status
```

### Using Commands

Slash commands are available directly:

```
/monorepo-init
```

### Using Hooks

Hooks run automatically on configured events (like SessionStart for monorepo detection).

## Development

To modify plugins:

1. Edit files in `plugins/` within this repository
2. Reinstall the plugin to pick up changes:
   ```bash
   /plugin uninstall <plugin>@pickled-claude-plugins
   /plugin install <plugin>@pickled-claude-plugins
   ```
3. Restart Claude Code
4. Commit and push to share across machines

### Plugin Structure

Each plugin follows this layout:

```
plugins/{plugin-name}/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── {skill-name}/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       └── examples/
├── commands/          # Optional
│   └── {command}.md
└── hooks/             # Optional
    ├── hooks.json
    └── scripts/
```

## Version History

- **1.0.0** (2025-11-13): Restructured as plugin marketplace with 5 domain-organized plugins
- **0.1.0** (2025-11-12): Initial release with standalone skills

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Josh Nichols ([@technicalpickles](https://github.com/technicalpickles))

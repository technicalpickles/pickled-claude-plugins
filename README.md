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
│   ├── git-workflows/        # Git workflow best practices
│   ├── ci-cd-tools/          # CI/CD pipeline tools
│   ├── debugging-tools/      # Debugging and troubleshooting
│   └── dev-tools/            # Developer productivity utilities
└── docs/
```

## Installation

### Automatic (via technicalpickles/dotfiles)

If you use [technicalpickles/dotfiles](https://github.com/technicalpickles/dotfiles), the marketplace is installed automatically via `install.sh`.

### Manual Installation

```bash
git clone https://github.com/technicalpickles/claude-skills ~/.claude/plugins/technicalpickles
```

The marketplace structure allows Claude Code to discover all plugins within the repository.

## Plugins

### working-in-monorepos

Navigate and execute commands in monorepo subprojects with proper directory handling.

**Features:**
- Auto-detection of monorepo structure via SessionStart hook
- `/monorepo-init` command for manual configuration
- Subproject type detection (Node, Ruby, Go, Python, Rust, Java)

**Skills:** working-in-monorepos

### git-workflows

Git workflow best practices and pull request management.

**Skills:** git-preferences-and-practices, gh-pr

### ci-cd-tools

CI/CD pipeline tools and integrations.

**Skills:** buildkite-status

### debugging-tools

Tools for debugging and troubleshooting applications.

**Skills:** scope, mcpproxy-debug

### dev-tools

Developer productivity tools and utilities.

**Skills:** working-in-scratch-areas

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

To modify plugins and skills:

1. Edit files in `~/workspace/claude-skills/plugins/`
2. Changes are immediately available to Claude (if installed via symlink)
3. Commit and push to share across machines

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

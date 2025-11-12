# technicalpickles Claude Skills

Personal collection of Claude Code skills for development workflows, CI/CD, and productivity.

## Installation

### Automatic (via technicalpickles/dotfiles)

If you use [technicalpickles/dotfiles](https://github.com/technicalpickles/dotfiles), the plugin is installed automatically via `install.sh`.

### Manual Installation

```bash
git clone https://github.com/technicalpickles/claude-skills ~/.claude/plugins/technicalpickles
```

## Skills Included

### General Development

- **working-in-monorepos**: Navigate and execute commands in monorepo subprojects with proper directory handling
- **working-in-scratch-areas**: Manage temporary work in persistent `.scratch` areas with organization patterns
- **git-preferences-and-practices**: Personal Git workflow preferences and best practices

### CI/CD & Infrastructure

- **buildkite-status**: Buildkite CI/CD workflow helpers for checking build status and debugging failures
- **scope**: Scope environment management tool helpers for debugging and configuration
- **mcpproxy-debug**: MCPProxy debugging and configuration helpers

### GitHub Workflows

- **gh-pr**: GitHub pull request creation and management workflows

## Usage

Skills are available in Claude Code via the Skill tool:

```
Use the technicalpickles:working-in-monorepos skill
```

Or reference them in custom skills:

```markdown
@technicalpickles:buildkite-status for checking CI status
```

## Development

To modify skills:

1. Edit files in `~/workspace/claude-skills/skills/`
2. Changes are immediately available to Claude (if installed via symlink)
3. Commit and push to share across machines

## Version History

- **1.0.0** (2025-11-12): Initial release with all personal skills

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Josh Nichols ([@technicalpickles](https://github.com/technicalpickles))

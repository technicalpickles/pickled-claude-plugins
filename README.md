# Pickled Claude Plugins

Personal plugin marketplace for Claude Code with curated skills, commands, and hooks organized by domain.

## Repository Structure

```
pickled-claude-plugins/
├── .claude-plugin/
│   ├── plugin.json           # Root marketplace metadata
│   └── marketplace.json      # Plugin registry (source of truth for the Plugins list)
├── plugins/
│   └── <plugin-name>/        # One directory per local plugin (see Plugins below)
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

<!-- BEGIN GENERATED PLUGINS (run scripts/generate-plugin-table.sh) -->
| Plugin | Description | Skills |
|--------|-------------|--------|
| [actually-lsp](plugins/actually-lsp) | Closes the LSP activation gap end-to-end (detection, setup, activation, failure diagnosis) for Rust, TypeScript, and Ruby projects | actually-lsp-doctor, actually-lsp-ignore |
| [agent-meta](plugins/agent-meta) | Meta-development tools for agentic workflows | park, snapshot, unpark |
| [buildkite](plugins/buildkite) | Buildkite CI tools: build investigation, pipeline development, and tool preference enforcement | developing-pipelines, investigating-builds |
| [ci-cd-tools](plugins/ci-cd-tools) | CI/CD pipeline tools and integrations | fixing-ci |
| [cq](https://github.com/technicalpickles/cq) | Query past Claude Code sessions via the cq CLI (SQL over session transcripts) | [see repo](https://github.com/technicalpickles/cq) |
| [dev-tools](plugins/dev-tools) | Developer productivity tools and utilities | colima, designing-clis, finding-api-docs, hk, working-in-scratch-areas, working-with-mise, working-with-scope |
| [git](plugins/git) | Git workflow tools: commits, PRs, review inbox, checkout, and work triage | checkout, commit, inbox, pull-feedback, pull-request, push, triage, update |
| [github-actions](plugins/github-actions) | GitHub Actions CI tools: investigate failing runs via gh + a structured snapshot helper | investigating-runs |
| [mcpproxy](plugins/mcpproxy) | MCP server management and integration tools | working-with-mcp |
| [petri-dish](https://github.com/technicalpickles/petri-dish) | Author Claude Code experiments (petri-dish cultures) with disciplined schema, baselines, and multi-run averaging | [see repo](https://github.com/technicalpickles/petri-dish) |
| [sandbox-advisor](plugins/sandbox-advisor) | Turns Claude Code sandbox EPERMs into crisp re-run-unsandboxed guidance | – |
| [second-brain](plugins/second-brain) | Knowledge management for Obsidian vaults and structured markdown repositories | connect, distill-rules, enrich, ingest, link-daily, obsidian, process-inbox, route |
| [stay-on-target](plugins/stay-on-target) | Focused development mode - clarify, plan, verify, detect drift | – |
| [taskwarrior](plugins/taskwarrior) | Token-dense recipes for taskwarrior CLI: dense listings, single-field lookups, batched exports, full-text search | taskwarrior |
| [tool-routing](plugins/tool-routing) | Route tool calls to better alternatives (e.g., gh CLI instead of WebFetch for GitHub PRs) | – |
| [working-in-monorepos](plugins/working-in-monorepos) | Navigate and execute commands in monorepo subprojects | working-in-monorepos |
| [writing-tools](plugins/writing-tools) | Skills for structuring and formatting prose so it reads well | writing-for-scannability |
<!-- END GENERATED PLUGINS -->

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

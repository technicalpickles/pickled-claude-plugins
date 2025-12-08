# Plugin Restructure with Skill-Level Routes

**Date:** 2025-12-05
**Status:** Draft

## Summary

Restructure plugins around clearer domains and colocate routes with the skills they support. This enables skills to define routes that guard their domain or enforce their conventions.

## Problems

1. **dev-tools is a catch-all** - unrelated skills landed there (MCPProxy tools, CLI design, scratch areas, API discovery)
2. **Blurred boundaries** - mcpproxy-debug in debugging-tools, using-mcpproxy-tools in dev-tools
3. **New things don't fit** - unclear which plugin owns a new skill
4. **Routes feel misplaced** - Buildkite routes live in tool-routing, not ci-cd-tools

## Design

### Route Discovery Hierarchy

Routes discovered from most specific to least specific:

```
1. plugins/*/skills/*/tool-routes.yaml   # skill-level (NEW)
2. plugins/*/hooks/tool-routes.yaml      # plugin-level
3. .claude/tool-routes.yaml              # project-level
```

| Location | Purpose | Example |
|----------|---------|---------|
| Skill-level | Routes that guard or enforce a specific skill | PR routes in writing-pull-requests/ |
| Plugin-level | Routes shared across skills, no single owner | atlassian route in dev-tools |
| tool-routing | Generic routes, no skill relationship | bash-cat-heredoc |
| Project-level | Team/repo-specific conventions | no-wip-commits |

### Plugin Structure

**After restructure (5 plugins, down from 6):**

```
plugins/
├── tool-routing/
│   └── hooks/
│       └── tool-routes.yaml        # generic routes only
│
├── git-workflows/
│   └── skills/
│       ├── writing-pull-requests/
│       │   ├── SKILL.md
│       │   └── tool-routes.yaml    # github-pr, git-commit-multiline, gh-pr-create-multiline
│       └── writing-git-commits/
│
├── ci-cd-tools/
│   └── skills/
│       ├── monitoring-buildkite-builds/
│       │   ├── SKILL.md
│       │   └── tool-routes.yaml    # buildkite route
│       └── developing-buildkite-pipelines/
│
├── mcpproxy/                       # NEW: consolidated
│   └── skills/
│       └── working-with-mcp/
│           ├── SKILL.md            # merged debug + usage
│           └── tool-routes.yaml    # bash-mcp-cli, bash-mcp-tool
│
├── dev-tools/
│   ├── hooks/
│   │   └── tool-routes.yaml        # atlassian route
│   └── skills/
│       ├── working-in-scratch-areas/
│       ├── finding-api-docs/
│       ├── designing-clis/
│       └── working-with-scope/     # moved from debugging-tools
│
└── working-in-monorepos/           # unchanged
```

### Skill Renames

| Current | New |
|---------|-----|
| gh-pr | writing-pull-requests |
| git-preferences-and-practices | writing-git-commits |
| buildkite-status | monitoring-buildkite-builds |
| scope | working-with-scope |
| mcpproxy-debug + using-mcpproxy-tools | working-with-mcp |
| api-documentation-discovery | finding-api-docs |

Unchanged: developing-buildkite-pipelines, designing-clis, working-in-scratch-areas, working-in-monorepos

### Naming Conventions

Two patterns for skill names:

| Pattern | Use when | Examples |
|---------|----------|----------|
| `working-with-X` | Tool/service domain, multiple actions | working-with-mcp, working-with-scope |
| `verb-ing-noun` | Specific task/workflow | writing-pull-requests, finding-api-docs |

### Route Distribution

**Move to skill-level:**

| Route | New Location |
|-------|--------------|
| github-pr | git-workflows/skills/writing-pull-requests/ |
| git-commit-multiline | git-workflows/skills/writing-pull-requests/ |
| gh-pr-create-multiline | git-workflows/skills/writing-pull-requests/ |
| buildkite | ci-cd-tools/skills/monitoring-buildkite-builds/ |
| bash-mcp-cli | mcpproxy/skills/working-with-mcp/ |
| bash-mcp-tool | mcpproxy/skills/working-with-mcp/ |

**Move to plugin-level:**

| Route | New Location |
|-------|--------------|
| atlassian | dev-tools/hooks/ |

**Stay in tool-routing:**

- bash-cat-heredoc
- bash-echo-chained
- bash-echo-redirect
- tool-routing-manual-test

## Tool-Routing Changes

Update route discovery to include skill-level routes:

1. Modify `discover_routes()` to glob `*/skills/*/tool-routes.yaml`
2. Update `list` command to show skill-level source paths
3. Update docs (route-discovery.md, writing-routes.md)
4. Add tests for skill-level discovery

No changes to route format, conflict detection, or check/test commands.

## Migration Steps

1. **Update tool-routing** - add skill-level route discovery
2. **Create mcpproxy plugin** - merge mcpproxy-debug and using-mcpproxy-tools
3. **Consolidate dev-tools** - move scope from debugging-tools
4. **Delete debugging-tools**
5. **Rename skills** per naming table
6. **Move routes** to skill and plugin locations
7. **Update marketplace.json** - remove debugging-tools, add mcpproxy

## Future Considerations

- Some generic routes (bash-echo-chained) might migrate to working-in-scratch-areas
- Route `skill` field could auto-recommend skills in block messages (deferred)

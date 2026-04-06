# Buildkite Plugin Design

## Problem

The `working-with-buildkite-builds` skill defines a tool hierarchy (bktide > MCP > bk) that works well when the skill is loaded, but:

1. **Before the skill loads**, the agent defaults to whatever it knows (`bk`, MCP, GitHub).
2. **When bktide fails**, the agent's fallback reasoning bleeds in codebase context ("the project uses bk") rather than following the hierarchy.
3. **The `bk` CLI isn't acknowledged** in the skill hierarchy at all, so it's invisible to the guidance.
4. **The tool preference is hardcoded** in the skill with no way for the user to configure it.

Session evidence from 7 reviewed conversations confirmed the skill works when loaded, but the timing gap and fallback reasoning are real problems.

## Solution

A new `buildkite` Claude Code plugin that:

- Consolidates both buildkite skills from `ci-cd-tools` into one home
- Adds a `PreToolUse` hook that intercepts specific `bk` subcommands before any skill loads
- Reads user preferences from a config file
- Blocks or warns based on strictness setting
- Gives the skill a strong default opinion (bktide) with a note that config can override

## Config File

Location: `~/.config/pickled-claude-plugins/buildkite.yml`

```yaml
tool_preference:
  - bktide
  - mcp
  - bk

strict: true  # true = block non-preferred tools, false = warn

intercept:
  - pattern: "^bk build\\b"
  - pattern: "^bk job log\\b"
  - pattern: "^bk api.*/builds"
```

Patterns are anchored regexes matched against the Bash command. The `\b` word boundary prevents `bk build` from matching `bk build-something`. All intercepted commands redirect to the first entry in `tool_preference`.

The plugin ships with `config/defaults.yml` containing the same content, used as fallback when user config doesn't exist. The user config file is not auto-created on install; users copy or edit from defaults when they want to customize.

## Plugin Structure

```
plugins/buildkite/
  .claude-plugin/
    plugin.json            # Manifest (name, description, NO version)
    routes.json            # Points to tool-routes.yaml
  hooks/
    hooks.json             # Hook config: PreToolUse on Bash, runs script
    check-bk-preference.sh # Script that reads config + checks patterns
  config/
    defaults.yml           # Sensible defaults, used as fallback
  skills/
    working-with-buildkite-builds/
      SKILL.md             # Moved from ci-cd-tools, updated
      references/          # Moved as-is
      scripts/             # Moved as-is
    developing-buildkite-pipelines/
      SKILL.md             # Moved from ci-cd-tools as-is
      references/          # Moved as-is
  tool-routes.yaml         # WebFetch route (moved from ci-cd-tools)
  README.md
```

### hooks/hooks.json

Follows the same pattern as tool-routing:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/check-bk-preference.sh"
          }
        ]
      }
    ]
  }
}
```

### Marketplace Registration

Add to `.claude-plugin/marketplace.json`:

```json
{
  "name": "buildkite",
  "source": "./plugins/buildkite",
  "version": "1.0.0"
}
```

## Hook Behavior

The `hooks/hooks.json` registers a `PreToolUse` hook on `Bash` tool calls. It runs `hooks/check-bk-preference.sh`, which receives the tool input on stdin (JSON with `tool_name` and `tool_input` fields).

### Flow

1. Extract command from tool input
2. Check if it matches any intercept pattern (regex match)
3. If no match: pass through silently (exit 0, no output)
4. If match:
   - Read `tool_preference` to determine what to suggest
   - If `strict: true`: exit with a block message
   - If `strict: false`: print warning, allow execution

### Block Message

The hook reads `tool_preference[0]` to determine what to suggest. The message includes the intercepted command and a generic pointer to the preferred tool (no smart translation):

```
Your buildkite tool preference is: bktide > mcp > bk

The command `bk build view ...` was blocked. Your preferred tool is bktide.
Use `npx bktide@latest snapshot <buildkite-url>` for build investigation,
or `npx bktide@latest --help` for other commands.

To allow bk commands, set `strict: false` in ~/.config/pickled-claude-plugins/buildkite.yml
```

### What Passes Through

- `bk auth status`, `bk config list` (diagnostics, not investigation)
- `bk` references in source code (not Bash tool calls)
- Any command that doesn't match an intercept pattern

## Skill Updates

### working-with-buildkite-builds

Add a "Why bktide snapshot?" section at the top, before the hierarchy:

> **Why bktide snapshot?** One command, one URL, gets you everything: build metadata, annotations, and logs for failed steps, all saved to local files you can grep and re-read without burning API calls. The other tools require you to piece together multiple calls and keep track of job UUIDs vs step IDs.

The tool hierarchy section keeps its opinionated recommendation (bktide first) but adds a note:

> This order can be overridden via `~/.config/pickled-claude-plugins/buildkite.yml`.

### developing-buildkite-pipelines

Moved as-is, no content changes.

## Migration from ci-cd-tools

- Move `ci-cd-tools/skills/working-with-buildkite-builds/` to `buildkite/skills/working-with-buildkite-builds/`
- Move `ci-cd-tools/skills/developing-buildkite-pipelines/` to `buildkite/skills/developing-buildkite-pipelines/`
- Move the WebFetch route from `ci-cd-tools/skills/working-with-buildkite-builds/tool-routes.yaml` to `buildkite/tool-routes.yaml` (top-level, where `routes.json` expects it)
- Update `ci-cd-tools/.claude-plugin/routes.json` to remove the buildkite route reference
- `fix-ci` command stays in ci-cd-tools (it references `working-with-buildkite-builds` by skill name, which still works after the move)
- Any other non-buildkite CI content stays in ci-cd-tools

## Not In Scope

- MCP tool interception (future enhancement)
- Per-project config overrides (future, add when evidence shows need)
- Smart command translation (hook just points at preferred tool, doesn't auto-translate)
- Content changes to developing-buildkite-pipelines skill
- Deprecation of ci-cd-tools (just removing buildkite content from it)

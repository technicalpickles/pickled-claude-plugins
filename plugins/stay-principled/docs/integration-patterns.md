# Integration patterns

`stay-principled:grill` works fine without any integration. Invoke it manually whenever you start design work. These patterns make other skills (typically `superpowers:brainstorming`) suggest grilling first when this project has principles configured.

All three patterns are optional. Pick zero, one, or multiple. They compose; using multiple is harmless because each is idempotent.

## Pattern A: CLAUDE.md prose

Soft, model-driven. A line added to `CLAUDE.md` telling the model to consider grilling first.

**Where:** Append to the `### Principles` subsection in CLAUDE.md's `## Agent skills` block.

**Snippet:**

```markdown
For design conversations or when invoking brainstorming on non-trivial topics, invoke `stay-principled:grill` first if `docs/agents/principles.md` exists.
```

**Pros:** Zero infrastructure. Works anywhere CLAUDE.md is loaded into context.
**Cons:** Model may ignore it. Not deterministic.

## Pattern B: Bundled hook helper

Hard, deterministic. A `settings.json` PreToolUse hook that fires `skill-advice` whenever `superpowers:brainstorming` is invoked, emitting advice as `additionalContext`.

**Where:** Add to one of (precedence is standard Claude Code order):

| Layer | Path | Use |
|---|---|---|
| User | `~/.claude/settings.json` | Universal across all projects |
| Project | `<project>/.claude/settings.json` | Project-specific, checked into git |
| Local | `<project>/.claude/settings.local.json` | Per-machine or per-worktree, gitignored |

**Snippet (user-level example with `--if-file` guard):**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Skill",
        "hooks": [{
          "type": "command",
          "command": "python3 \"$HOME/.claude/plugins/cache/pickled-claude-plugins/stay-principled/0.1.0/scripts/skill-advice.py\" --skill superpowers:brainstorming --if-file docs/agents/principles.md --advice 'Principles configured for this project. Consider stay-principled:grill first to anchor the why before generating options.'"
        }]
      }
    ]
  }
}
```

**Note:** The `0.1.0` segment in the path is the installed plugin version. Update it after upgrading the plugin. (A future enhancement may add a `latest` symlink to the marketplace cache; for now, the version is hardcoded.)

The `--if-file docs/agents/principles.md` guard means this user-level hook fires only in projects that have principles configured. That's the per-project layering achieved through standard mechanisms; no plugin-internal config needed.

**Pros:** Bites every time. Works without other plugins.
**Cons:** Requires user to maintain `settings.json` entries. Path to the helper depends on where the plugin cache lives.

**Helper contract:** see [`helper-contract.md`](helper-contract.md) for full reference.

## Pattern C: tool-routing rule

Hard, deterministic. Uses the existing `tool-routing` plugin's PreToolUse interception rather than a fresh hook.

**Requires:** `tool-routing` plugin installed and enabled.

**Where:** A route file readable by tool-routing. The default file is `plugins/tool-routing/hooks/tool-routes.yaml` (shipped with the plugin); per-project routes can live in `.claude/tool-routes.yaml`.

**Snippet (add to the `routes:` dict):**

```yaml
routes:
  brainstorm-suggests-stay-principled:
    tool: Skill
    pattern: 'superpowers:brainstorming'
    message: "If docs/agents/principles.md exists, consider stay-principled:grill first to anchor the why."
```

**Pros:** Integrates with existing tool-routing config; centralized place to manage all routing rules.
**Cons:** Requires that plugin and its discovery layer.

## Choosing among patterns

- **Just want it to work?** Pattern A. Done in one line.
- **Want determinism?** Pattern B. The model has no choice but to see the advice.
- **Already use tool-routing for everything?** Pattern C. Keeps your routing rules consolidated.
- **Don't care?** Skip all three. Invoke `stay-principled:grill` manually.

# stay-on-target

> "Stay on target!" - Gold Five, A New Hope

A Claude Code plugin that enforces intentional, focused development.

## Philosophy

"Be intentional, don't just dive in."

## Behaviors

1. **Clarify** - Check git state, explore codebase, ask questions before implementing
2. **Plan** - Require human-reviewable plan before coding
3. **Verify** - Establish concrete success criteria (test harness)
4. **Detect Drift** - Flag scope changes mid-conversation

## Installation

```bash
/plugin install stay-on-target@pickled-claude-plugins
```

## Configuration

Configure handoff location in your project's CLAUDE.md:

```markdown
## Handoffs
Location: ~/Vaults/your-vault/handoffs/
```

## Structure

```
stay-on-target/
├── .claude-plugin/plugin.json
├── hooks/hooks.json           # SessionStart hook registration
├── hooks-handlers/
│   └── session-start.sh       # Composes prompt from modules
├── prompts/
│   ├── _base.md               # Core philosophy
│   └── behaviors/
│       ├── 01-git-state.md    # Git/WIP awareness
│       ├── 02-codebase-maturity.md
│       ├── 03-prior-art.md    # Find existing solutions
│       ├── 04-clarify.md      # Ask questions first
│       ├── 05-plan.md         # Always plan
│       ├── 06-verify.md       # Test harness
│       └── 07-drift.md        # Scope drift detection
└── skills/
    └── scope-handoffs/        # Handoff doc generation
```

## Design

See `docs/plans/2026-01-27-stay-on-target-design.md` for full design documentation.

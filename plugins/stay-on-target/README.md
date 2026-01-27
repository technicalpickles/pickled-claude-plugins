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
/plugin install stay-on-target@technicalpickles-marketplace
```

## Configuration

Configure handoff location in your project's CLAUDE.md:

```markdown
## Handoffs
Location: ~/Vaults/your-vault/handoffs/
```

## Design

See `docs/plans/2026-01-27-stay-on-target-design.md` for full design documentation.

# stay-principled

Anchor design conversations to a project's documented principles via depth-first grilling before brainstorming opens. The plugin's job: keep design *principled*, with bite, when it would otherwise drift.

## Why

If your project has a `docs/principles.md` file, you've already done the hard work of articulating *why* decisions land where they do. But principles loaded as upfront context don't necessarily *bite* during design moments. Brainstorming sessions still surface low-level option menus instead of anchoring choices to the principles.

This plugin closes that gap. It applies grill-me's depth-first decision-tree walking with principles as the tree roots, before brainstorming opens. The result: brainstorming starts at the right altitude with most options already constrained or ruled out.

## What's in here

| Component | Purpose |
|---|---|
| `stay-principled:setup` skill | One-shot config scaffolder. Run once per project. |
| `stay-principled:grill` skill | Runtime grilling. Invoke at the start of design work. |
| `scripts/skill-advice.py` | Generic Python helper for PreToolUse hooks. Used by Pattern B integration. Reusable from other plugins. |

## Install

```bash
/plugin install stay-principled@pickled-claude-plugins
```

Restart Claude Code after install (per the marketplace's directory-source caching).

## Quick start

In a project that has principles documented (a `docs/principles.md` or similar markdown file):

1. **Configure once:**

   ```
   /skill stay-principled:setup
   ```

   Walks you through where principles live, format hints, optional domain map, and optional integration patterns. Writes `docs/agents/principles.md` and adds an `### Principles` subsection to your CLAUDE.md.

2. **Use whenever you start design work:**

   ```
   /skill stay-principled:grill
   ```

   Or just say "grill me with principles on this" / "anchor this to the principles" / "stay principled on this" / similar.

## Using without setup

`stay-principled:grill` works without setup if `docs/principles.md` exists at the repo root. Setup adds nuance (domain map, format hints, integration). Skip setup if you just want quick grilling on a one-off project.

## Integration with other skills

The plugin offers three optional ways to make `superpowers:brainstorming` (or any other skill) suggest grilling first:

- **Pattern A:** CLAUDE.md prose. Soft, model-driven.
- **Pattern B:** Bundled hook helper (`skill-advice`). Hard, deterministic.
- **Pattern C:** `tool-routing` rule. Hard, requires that plugin.

See [`docs/integration-patterns.md`](docs/integration-patterns.md) for full templates and tradeoffs.

## Reusing the helper

The `scripts/skill-advice.py` helper is generic, nothing plugin-specific about it. Other plugins can wire it into their own PreToolUse hooks for "when this skill is invoked, suggest also doing X" patterns.

See [`docs/helper-contract.md`](docs/helper-contract.md) for the contract.

## What this plugin does not do (v1)

- Capture-side workflow (post-implementation principle sweeps, principle amendments). The existing manual workflow stays.
- Principles file format validation. The plugin is format-tolerant for markdown.
- Auto-detection of relevant principles in every tool call. Grilling is invoked per design conversation, not as a continuous backseat driver.

## Contributing

This plugin lives in [`pickled-claude-plugins`](https://github.com/technicalpickles/pickled-claude-plugins). PRs welcome.

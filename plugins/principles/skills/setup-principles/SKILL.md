---
name: setup-principles
description: Scaffolds principle-anchoring configuration for a project. Writes docs/agents/principles.md, adds a `### Principles` block to `## Agent skills` in CLAUDE.md or AGENTS.md, and optionally drafts hook integration snippets for settings.json or tool-routing. Run once per project before using grill-with-principles. Re-run only if the principles file layout changes.
disable-model-invocation: true
---

# Setup Principles

Scaffold the per-project configuration that `grill-with-principles` reads. This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm with the user, then write.

## Process

### 1. Explore

Look at the current repo to understand its starting state. Read whatever exists; don't assume:

- `docs/principles.md`, `docs/ops-principles.md`, any sibling `*principles*.md` files at the repo root or under `docs/`
- `docs/agents/principles.md`: existing config; update in place if found
- `CLAUDE.md` (preferred) or `AGENTS.md` at the repo root: does either exist? Is there already an `## Agent skills` section?
- `claude plugin list --json`: is `tool-routing` installed and enabled? (Affects whether Pattern C is offered.)
- `git rev-parse --show-toplevel`: used as the canonical repo root for path resolution; principles inside worktrees still live at the worktree root.

### 2. Present findings and ask

Summarize what's present and what's missing. Then walk the user through the four sections **one at a time**. Present a section, get the user's answer, then move to the next. Don't dump all sections at once.

Assume the user does not know what these terms mean. Each section starts with a short explainer (what it is, why this skill needs it, what changes if they pick differently).

**Section A: Where do principles live?**

> Explainer: The `grill-with-principles` skill needs to know which markdown files contain your principles. Most projects have one (`docs/principles.md`); some split into multiple (e.g. engineering vs ops). The skill reads all of them at session start to build a working set.

Default posture: if any `*principles*.md` files were found during exploration, list them and ask the user to confirm or adjust. Multi-file is fine. If none were found, ask the user where their principles are documented (or if they don't yet exist; in that case, suggest creating `docs/principles.md` and offer to scaffold a starter file before continuing).

**Section B: Format hint.**

> Explainer: This is a free-form description of how the principles are structured in your file. The skill uses this to reason about cross-references, correction cases, and domain-specific sections. The format is not a schema (the skill is format-tolerant) but a description helps it reason better.

Default detection: skim the first 50 lines of the principles file. If it has numbered cross-cutting principles with bold names, "Why:" and "Where:" sections, propose:

> "Numbered cross-cutting principles with **bold name**, statement, Why:, and Where: sections. Domain-specific principles under `## Domain-specific principles`. Cross-references between principles by number. Correction cases embedded in `Where:` sections."

If the format is simpler (bullets, plain headers), describe what you see and let the user adjust.

**Section C: Domain map (optional).**

> Explainer: Some principles only apply to specific subsystems (e.g. PRM, Tasks). The domain map tells the skill which directories trigger which principle subsets, so it can pull in domain-specific principles when the topic is in a named domain.

If the principles file has a `## Domain-specific principles` section (or similar), propose a mapping by reading the section headings and looking for matching directories under `src/` or similar. Otherwise skip this section entirely.

**Section D: Hook integration (optional, opt-in).**

> Explainer: By default, you invoke `grill-with-principles` manually. Hook integration makes other skills (typically `superpowers:brainstorming`) suggest grilling first when this project has principles configured. Three patterns are available; pick zero, one, or multiple.

Present the three patterns. The user can decline all of them; the runtime skill works fine without integration.

- **Pattern A: CLAUDE.md prose.** Soft, model-driven. A line added to CLAUDE.md telling the model to consider grilling first.
- **Pattern B: Hook helper.** Hard, deterministic. A `settings.json` snippet that fires `skill-advice` on every `superpowers:brainstorming` invocation.
- **Pattern C: tool-routing rule.** Hard, deterministic. Only offered if `tool-routing` is installed.

For each chosen pattern, draft the snippet. See the project [`docs/integration-patterns.md`](../../docs/integration-patterns.md) for the templates.

### 3. Draft and confirm

Show the user a draft of:

- The contents of `docs/agents/principles.md`
- The `### Principles` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited
- Pattern A snippet (if chosen): appended to CLAUDE.md as a routing line
- Pattern B snippet (if chosen): printed for paste into `settings.json`. Do not auto-write `settings.json`.
- Pattern C snippet (if chosen): printed for paste into a tool-routing routes file. Do not auto-write.

Let the user edit before writing.

### 4. Write

**Pick the file to edit:**

- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask the user which one to create. Don't pick for them.

Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa). Always edit the one that's already there.

If an `## Agent skills` block already exists, add the `### Principles` subsection in-place. Don't append a duplicate. Don't overwrite user edits to surrounding sections.

The block:

```markdown
## Agent skills

### Principles

[one-line summary of where principles live]. See `docs/agents/principles.md` for format and configuration. The `grill-with-principles` skill reads from these files.
```

Then write `docs/agents/principles.md` using this template, replacing the file's content if it already exists:

```markdown
# Principles configuration

## Files
- [path to first principles file]
- [path to second, if any]

## Format
[user-confirmed format description from Section B]

## Domain map
[domain to directory mappings from Section C, or omit if skipped]

## Skip patterns
[branch-name or path patterns where principle anchoring should be skipped, or omit]
```

Pattern A/B/C snippets: write Pattern A inline into CLAUDE.md (append a routing line at the end of the agent-skills block). Print Pattern B and Pattern C snippets for the user to paste manually.

### 5. Done

Tell the user:

1. Setup is complete.
2. Which files were written.
3. That `grill-with-principles` will now read from `docs/agents/principles.md`.
4. That re-running this skill is only needed if the file layout changes; manual edits to `docs/agents/principles.md` are fine.

If integration patterns were offered, remind the user to paste any Pattern B/C snippets into the appropriate config file.

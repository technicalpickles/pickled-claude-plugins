# Routing Memory Reference

`.routing-memory.md` lives in the vault root. It captures routing corrections and learned patterns, enabling the routing system to improve over time.

## File Format

```yaml
---
auto-route-threshold: 70
---
```

The file has two sections:

### Corrections

Captured automatically when a user overrides a routing suggestion. Each correction records what happened and why.

```markdown
## Corrections

- 2026-03-31: "tmux parsing" routed to "dev environment", corrected to "tool sharpening"
  Reason: tmux is a tool, config/parsing work goes to tool sharpening

- 2026-03-31: "Redis caching insight" routed to "infrastructure", corrected to "backend-patterns"
  Reason: caching strategy is a pattern, not infra concern
```

### Patterns Learned

Distilled from accumulated corrections (via `distill-rules` skill). These are stable routing rules that have proven themselves across multiple corrections.

```markdown
## Patterns Learned

- CLI tool configs, dotfiles, shell customization -> Areas/tool sharpening/
- Messaging patterns (Karafka, Kafka, SQS) -> Resources/kafka-patterns/
- Caching strategies, data access patterns -> Areas/backend-patterns/
```

## Consultation Order

When the `route` skill (or `commands/route.md`) makes a routing decision:

1. **Check corrections first.** Recent corrections override everything. A correction from today beats a CLAUDE.md rule.
2. **Check learned patterns.** These are distilled corrections, more stable than individual entries.
3. **Check vault CLAUDE.md disambiguation rules.** The baseline routing algorithm (see `references/routing.md`).

A correction that contradicts a CLAUDE.md rule wins. The `distill-rules` skill eventually promotes stable corrections into CLAUDE.md rules, at which point the corrections can be archived.

## Capturing Corrections

When the `route` skill suggests a destination and the user picks a different one:

1. Append a new entry to `## Corrections` with date, original suggestion, user's choice, and reason
2. Ask the user: "Why did you pick {destination} over {suggested}?" (one sentence is fine)
3. Record the reason

This happens in both the pipeline `route` skill and the standalone `commands/route.md` command.

## Auto-Route Threshold

The `auto-route-threshold` frontmatter value (0-100) controls graduated autonomy:

- Notes scoring **above** the threshold are auto-routed without prompting
- Notes scoring **below** are marked `pending-review` for human input
- Default: 70 (conservative start)
- Raise it as routing quality improves

## Creating the File

`.routing-memory.md` is created on first use by whichever skill needs it (usually `route`). Initial content:

```markdown
---
auto-route-threshold: 70
---

## Corrections

## Patterns Learned
```

## When to Run `distill-rules`

The `distill-rules` skill reads corrections, finds stable patterns, and proposes CLAUDE.md rule updates. Run it when:

- You've accumulated 10+ corrections
- You notice the same type of correction repeating
- You want to raise the auto-route threshold and want better rules to support it

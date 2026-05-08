# Taskwarrior Token Density — Design

**Date:** 2026-05-08
**Status:** Draft, pending user approval
**Author:** brainstorm with Claude

## Problem

Taskwarrior is the project backlog. Claude invokes `task` heavily on Josh's behalf: ~978 calls in the last 30 days, generating ~1.37M chars of output (~13K tokens/day, ~390K tokens/month).

The cost is concentrated:

| Verb | Calls/mo | Chars/mo | Avg/call | % of cost |
|---|---|---|---|---|
| `list` | 230 | 766K | 3,333 | 56% |
| `info` | 202 | 355K | 1,758 | 26% |
| (other read) | 110 | 119K | — | 9% |
| `add` / `done` / `annotate` / `modify` | 435 | 132K | — | 9% |

`list` + `info` together = 80% of token spend. They're also the verbs where taskwarrior's defaults are loosest: `list` wraps long descriptions across 5+ lines per task, `info` dumps full metadata when usually one field is wanted.

Beyond read overhead, **stored task descriptions are bloated**: 46% of pending tasks have descriptions over 200 chars; 15% over 400. Some are 600-848 chars — paragraphs of context stuffed where titles belong. Every read of these tasks pays the bloat tax.

## Goals

1. Cut listing cost ~5-8× via dense formatting (the biggest single lever).
2. Replace `task <id> info` with `_get` and `export | jq` recipes for known-field lookups.
3. Replace batched `task A info && task B info && ...` (seen at 25K chars/call) with single `task uuid:A,B,C export | jq ...` calls.
4. Establish a soft description-length convention so future task creation doesn't accrue bloat.
5. Do all this with no new tools — taskwarrior already supports everything needed natively.

## Non-goals

- No wrapper binary (RTK-style stdout filter). Taskwarrior emits structured data and supports format control; post-filtering is the wrong layer.
- No retroactive cleanup of the 90 already-bloated descriptions. They'll decay naturally as tasks are completed or edited. (Listed as a possible follow-up, not part of this work.)
- No change to the existing UUID-stable-identifier policy — that's already settled and lives in `~/.claude/rules/taskwarrior.md`.

## Approach

Three changes, all native:

### 1. `.taskrc` — named dense report + verbose suppression

Add a new named report `dense` and make it the default command for bare `task`:

```
# Default to the dense report when running `task` with no arguments.
default.command=dense

# Allow-list which verbose categories print. Notably excludes `override`
# (suppresses "Configuration override rc.foo=bar" echo lines) and `blank`
# (suppresses extra blank lines). Keeps `header` for column labels,
# `new-id` for the post-add task ID, and a few utility categories.
# Full set: affected,blank,context,edit,header,footnote,label,new-id,news,project,special,sync,override,recur
verbose=header,new-id,edit,context,project,special,sync,recur

# Dense report: one-line-per-task, urgency-sorted, pending only.
report.dense.description=Token-dense pending tasks
report.dense.columns=uuid.short,project,tags,due.relative,description.truncated_count
report.dense.labels=ID,Proj,Tag,Due,Desc
report.dense.sort=urgency-
report.dense.filter=status:pending

# Wider default width so descriptions don't multi-line wrap at terminal width.
defaultwidth=200
```

Rationale:
- `uuid.short` (8-char) instead of `id` + `uuid.short` — UUIDs are stable, integer IDs are noise for any task that'll be referenced later.
- `description.truncated_count` shows truncated text + a `(N more)` suffix, instead of wrapping the full text across lines.
- `urgency-` sort because that's what `next` uses; gives the same "what's most important" ordering.
- `status:pending` baked into the report filter — no need to type it every call.
- `verbose=` value chosen to keep a few useful signals (e.g., the `new-id` echo when adding) without the override-noise.

### 2. Plugin skill — `plugins/taskwarrior/skills/taskwarrior/SKILL.md`

A new plugin under this repo with one skill that captures the dense recipes. Description triggers on intent like "query taskwarrior", "task add/list/info", "find a task". Skill content:

- **Listing (most-common case):** `task <filter> dense` — uses the named report.
- **Listing (custom shape):** `task <filter> export | jq -r '.[] | "\(.uuid[0:8]) [\(.project)] \(.tags // [] | join(",")) \(.due // "-")  \(.description[0:80])"'` — produces ~120 chars/task vs ~960 raw.
- **Single-field lookup:** `task <uuid> _get <field>` — e.g., `_get description`, `_get project`. Never `task <uuid> info` for a known field.
- **Multi-task lookup:** `task uuid:A,B,C export | jq -r '.[] | "\(.uuid[0:8])  \(.description[0:120])"'` — never `task A info && task B info && ...` (the antipattern that's been costing 25K/call).
- **Full-text search across annotations:** the existing jq `select(.annotations[]?.description | test("..."))` recipe.
- **Description length convention:** aim for ≤ 100 chars; put long context in `task <uuid> annotate "..."`. Soft rule, applies to new task creation.

### 3. Rule retention — `~/.claude/rules/taskwarrior.md`

The existing rule keeps its current job: trigger conditions, UUID-stability policy, the "tasks vs memory vs parked sessions" decision tree. Add one line pointing at the skill for recipes. Don't move the recipes into the rule itself: rules are always-loaded context, and we don't want recipe text burned into every conversation.

## Plugin structure

Following the repo conventions in `CLAUDE.md`:

```
plugins/taskwarrior/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── taskwarrior/
│       └── SKILL.md
└── README.md
```

Plus an entry added to `.claude-plugin/marketplace.json` so it ships through the marketplace like the other plugins.

## Verification

Success criteria, in order of how strongly each can be verified:

1. **Output-size regression test (executable).** Pick three representative invocations seen in cq history (`task project:pickled-claude-plugins list`, `task <uuid> info`-replacement, batched-info-replacement) and measure char count before vs after. Target: ≥ 5× reduction on the listing recipe; ≥ 4× on multi-task lookup; ≥ 10× on single-field lookup (vs `info`).
2. **Spot-check `.taskrc`.** Run `task` with no args, confirm dense report fires. Run `task <filter>` with various filters, confirm no wrapping at terminal width 200. Run `task add` and `task done` to confirm verbose-suppression doesn't hide useful confirmations.
3. **Skill discovery (executable).** Install the plugin locally, restart Claude Code, prompt with a task-related query, confirm the skill appears in available skills and triggers on relevant intent.
4. **One-week observation (manual).** After landing, re-run the cq queries from the brainstorm in a week. Confirm `list`/`info` totals drop. (Not a gating criterion — recovery from old habits takes time — but a useful follow-up signal.)

## Open questions / follow-ups

- Should we add a `task add`-aware alias or wrapper that warns when a description exceeds 100 chars? Probably not in v1 — the soft convention should be enough; revisit if creation bloat continues.
- The 90 already-bloated descriptions are out of scope. If we want them cleaned up, that's a separate one-shot pass.
- The skill could grow (full-text search variants, project summary recipes, etc.). Start minimal; add idioms when they earn their keep.

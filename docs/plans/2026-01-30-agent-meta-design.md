# agent-meta Plugin Design

**Date:** 2026-01-30
**Status:** Draft

## Overview

Meta-development tools for agentic workflows. Analyze past sessions, manage work continuity, identify improvement opportunities.

## Core Capabilities

| Capability | Mechanism | Description |
|------------|-----------|-------------|
| Session/tool analysis | Scripts | Failures, hooks, routing, summaries |
| Work continuity | Skills | `/park` to save, `/unpark` to resume |
| Skill identification | Scripts | Flag patterns that suggest new skills/hooks |
| Context snapshot | Skills | Summarize current session state |

## Structure

```
plugins/agent-meta/
├── .claude-plugin/plugin.json
├── commands/
│   ├── park.md              # User entry: /park
│   ├── unpark.md            # User entry: /unpark
│   └── snapshot.md          # User entry: /snapshot
├── skills/
│   ├── park/SKILL.md        # Save context for later
│   ├── unpark/SKILL.md      # Resume + validate
│   └── snapshot/SKILL.md    # Inline summary (--save optional)
├── scripts/
│   ├── find-failures.py     # Tool call errors (migrated)
│   ├── trace-hooks.py       # Hook execution trace
│   ├── analyze-routing.py   # Tool routing suggestions
│   ├── summarize-session.py # Session condensation
│   └── identify-skills.py   # Pattern → skill candidates
└── README.md
```

## Commands & Skills

Commands are user-invokable entry points. Skills contain the workflow logic.

### `/park`

Save current work context for later resumption.

**Captures:**
- Git state: branch, worktree, uncommitted changes
- Current task: what we're doing, what's next
- Key decisions: choices made that shouldn't be re-litigated
- Relevant files: what was touched/read
- Resume prompt: suggested prompt to continue

**Output format:**

```markdown
# Parked: [Topic]

**Parked:** [Date/time]
**Branch:** [branch-name]
**Worktree:** [path if applicable]

## Current State
[What's done, what's in progress, any blockers]

## Key Decisions
- [Decision 1]
- [Decision 2]

## Relevant Files
- path/to/file.ts (new|modified|read)
- path/to/other.ts

## Next Steps
1. [Next step]
2. [Next step]

## Resume Prompt
[Suggested prompt to continue this work]
```

### `/unpark`

Resume from a parked handoff.

**Process:**
1. Find handoff doc (prompt if multiple exist)
2. Read and present summary
3. Validate: check git state matches, files still exist, decisions still relevant
4. If valid → proceed with next steps
5. If stale/wrong → update handoff, recommend fresh `/unpark`

### `/snapshot`

Capture current session state without stopping.

**Output:** Inline summary by default.

```
━━━ Session Snapshot ━━━
Started: ~2 hours ago
Focus: [Current focus]

Progress:
✓ [Completed item]
✓ [Completed item]
○ [In progress]

Key decisions:
- [Decision]

Files touched:
- path/to/file.ts

Current thread: [What we're discussing]
```

**Flag:** `--save` writes to handoff location as checkpoint.

## Handoff Location Resolution

1. Project `CLAUDE.md` → `## Handoffs` or `## Parking` → `Location:`
2. User `~/.claude/CLAUDE.md` → same lookup
3. Default: `.parkinglot/` in project root (gitignored)

## Analysis Scripts

All scripts share common patterns:
- Read from `~/.claude/projects/` JSONL session logs
- Human-readable output by default, `--json` for structured
- Can process single files or directories recursively

### `find-failures.py`

Migrated from `session-analyzer`. Finds tool calls that returned errors.

```
$ find-failures.py ~/.claude/projects/my-project/session.jsonl

━━━ Failed Tool Calls ━━━
[timestamp] Bash: npm test
  Error: Command failed with exit code 1

[timestamp] Read: /nonexistent/path.ts
  Error: File not found
```

### `trace-hooks.py`

Traces hook execution through a session.

```
$ trace-hooks ~/.claude/projects/my-project/session.jsonl

━━━ Hook Executions ━━━
  SessionStart: stay-on-target/session-start.sh
    Status: success
    Output: "Focused Development Mode enabled..."

  PreToolUse (Bash): tool-routing/pre-tool-use.sh
    Status: success
    Output: "Suggestion: Use Read instead of cat"
    Effect: Tool call was modified
```

Questions answered: Did hooks fire? In what order? What output? Did they change behavior?

### `analyze-routing.py`

Analyzes tool-routing suggestions and outcomes.

```
$ analyze-routing ~/.claude/projects/my-project/

━━━ Routing Analysis ━━━
Suggestions made: 12
Suggestions followed: 8 (67%)
Suggestions ignored: 4

Ignored suggestions:
  - "Use Grep instead of Bash rg" (3x) → user preference?
  - "Use Read instead of Bash cat" (1x) → multi-file cat
```

Helps tune tool-routing rules based on actual usage.

### `summarize-session.py`

Condenses a session into key events for human review.

```
$ summarize-session ~/.claude/projects/my-project/session.jsonl

━━━ Session Summary ━━━
Duration: ~45 min
Tool calls: 87 (12 failed)
Files touched: src/auth.ts, src/middleware.ts, tests/auth.test.ts

Key events:
  1. Explored codebase for auth patterns
  2. Planned JWT implementation (user approved)
  3. Implemented token generation - 3 iterations
  4. Fixed middleware integration
  5. Tests passing

Decisions made:
  - JWT over session cookies
  - 24h token expiry

Pain points:
  - Wrong directory for test runs (3x)
  - Missed existing utility
```

### `identify-skills.py`

Flags patterns that suggest skill/hook opportunities.

```
$ identify-skills ~/.claude/projects/my-project/

━━━ Skill Candidates ━━━
[HIGH] Repeated failure pattern:
  "Command run in wrong directory" (5 occurrences)
  → Consider: hook to validate cwd before Bash

[MEDIUM] Manual workaround detected:
  User repeatedly asked to "check package.json first"
  → Consider: skill for dependency-aware suggestions

[LOW] Unused tool suggestion:
  Grep suggested but Bash rg used 8x
  → Consider: tuning tool-routing or user preference flag
```

Starts with pattern matching. Future: pass candidates to LLM for deeper analysis.

## Migration

| Plugin | Change |
|--------|--------|
| `session-analyzer` | Deprecated, scripts migrate to `agent-meta` |
| `stay-on-target` | Unchanged, can invoke `/park` when drift option C is chosen |

## Use Cases

### Personal learning
Review script output to understand what went wrong, improve prompting.

### Skill/hook development
Script output informs creating new skills, improving tool-routing rules.

### Training data
Extract examples for fine-tuning or prompt engineering.

### Work continuity
Park work at end of day or when context is full, unpark to resume.

## Future Enhancements

- LLM-powered skill identification (feed session + candidates to Claude)
- Automatic parking suggestions when context window approaches limit
- Integration with Obsidian vault for cross-project handoff tracking

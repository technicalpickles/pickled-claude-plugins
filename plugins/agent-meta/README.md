# agent-meta

Meta-development tools for agentic workflows.

## Philosophy

Working with AI coding agents generates valuable artifacts beyond code: session patterns, failure modes, decision trails. This plugin helps capture and learn from that meta-layer, including understanding the harness itself.

## Skills

| Skill | Description |
|-------|-------------|
| `agent-meta:park` | Save current work context. Two modes: **continuation** (handoff to new session) and **close-out** (record of completed work). |
| `agent-meta:unpark` | Resume work from a parked handoff, or read a wrapped close-out as reference. |
| `agent-meta:snapshot` | Capture current session state (inline or with save). In-flow checkpoint, not a walking-away artifact. |
| `agent-meta:harness-binary-spelunking` | Spelunk the Claude Code CLI binary to extract the system prompt, map UI messages to code paths, decode minified functions, and find undocumented config keys. |

Invoke by asking naturally ("park this session", "wrap this up", "unpark docs/handoffs/foo.md") or with the fully qualified slash form (`/agent-meta:park`).

### Park modes

`park` produces two distinct artifacts:

- **Continuation** (`Parked:` heading, `[topic].md` filename): for handoffs to a new session. The Resume Prompt is the centerpiece: tight, specific, copy-paste ready.
- **Close-out** (`Wrapped:` heading, `[topic]-wrapped.md` filename): for records of completed work. No Resume Prompt; an "Outcome" section in past tense and an optional "Open Threads" list.

Mode is picked at park time from your phrasing ("park to continue" vs "wrap this up"), inferred from the work's state, or asked if ambiguous.

## Scripts

Analysis tools for post-hoc session review:

| Script | Description |
|--------|-------------|
| `find-failures.py` | Find tool calls that errored |
| `trace-hooks.py` | Trace hook execution through a session |
| `analyze-routing.py` | Analyze tool-routing suggestions and outcomes |
| `summarize-session.py` | Condense session to key events |
| `identify-skills.py` | Flag patterns that suggest new skills/hooks |

### Usage

```bash
# From plugin directory
./scripts/find-failures.py ~/.claude/projects/my-project/session.jsonl
./scripts/summarize-session.py ~/.claude/projects/my-project/

# JSON output for programmatic use
./scripts/find-failures.py --json ~/.claude/projects/my-project/
```

## Configuration

Configure handoff location in your CLAUDE.md (project or user level):

```markdown
## Parking
Location: ~/Vaults/my-vault/handoffs/
```

Default location: `.parkinglot/` in project root (gitignored).

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```bash
/plugin install agent-meta@pickled-claude-plugins
```

## See Also

- `stay-on-target` - Focused development mode with drift detection
- `tool-routing` - Tool call suggestions and routing

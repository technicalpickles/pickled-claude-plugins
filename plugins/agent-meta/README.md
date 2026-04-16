# agent-meta

Meta-development tools for agentic workflows.

## Philosophy

Working with AI coding agents generates valuable artifacts beyond code: session patterns, failure modes, decision trails. This plugin helps capture and learn from that meta-layer.

## Skills

| Skill | Description |
|-------|-------------|
| `agent-meta:park` | Save current work context for later resumption |
| `agent-meta:unpark` | Resume work from a parked handoff |
| `agent-meta:snapshot` | Capture current session state (inline or with save) |

Invoke by asking naturally ("park this session", "unpark docs/handoffs/foo.md") or with the fully qualified slash form (`/agent-meta:park`).

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

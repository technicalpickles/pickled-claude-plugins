# agent-meta

Meta-development tools for agentic workflows.

## Philosophy

Working with AI coding agents generates valuable artifacts beyond code: session patterns, failure modes, decision trails. This plugin helps capture and learn from that meta-layer.

## Commands

| Command | Description |
|---------|-------------|
| `/park` | Save current work context for later resumption |
| `/unpark` | Resume work from a parked handoff |
| `/snapshot` | Capture current session state (inline or `--save`) |

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

```bash
/plugin install agent-meta@technicalpickles-marketplace
```

## See Also

- `stay-on-target` - Focused development mode with drift detection
- `tool-routing` - Tool call suggestions and routing

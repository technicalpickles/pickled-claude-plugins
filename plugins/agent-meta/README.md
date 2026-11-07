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

## Commands

| Command | Description |
|---------|-------------|
| `/session-id` | Print the current session ID. Answers instantly, with no model turn, and works mid-turn. |

`/session-id` is a [mod](https://code.claude.com/docs/en/plugins/mods/overview): a function-hooks module at `hooks/register.ts`, loaded alongside the shell hooks in `hooks/hooks.json`. Run its tests with `claude plugin test plugins/agent-meta`.

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

With the `second-brain` plugin installed, parks go to its default vault with no setup (see its README). Without it, `park` and `unpark` use the locations above.

Optionally, also send the parked file to an external destination (e.g. filing it into a second-brain vault) with two plugin settings:

- `destination`: a literal command template, e.g. `npx @techpickles/sb note create --source auto --title "{title}" --content-file {file}`.
- `destination_helper`: a no-arg command whose stdout produces the template dynamically, e.g. `~/.claude/bin/pick-park-destination.sh`. Wins over `destination` if both are set.

Both accept `{file}`, `{title}`, and `{mode}` (`continuation`, `close-out`, or `idle-checkpoint`) placeholders. Neither set means park behaves exactly as it does without one. This is purely additive, never a replacement for the local file.

The older `AGENT_PARK_DESTINATION` and `AGENT_PARK_DESTINATION_HELPER` env vars still work. They are read only when the matching plugin settings are empty, so existing setups keep working and you can move over at your own pace.

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```bash
/plugin install agent-meta@pickled-claude-plugins
```

## See Also

- `stay-on-target` - Focused development mode with drift detection
- `tool-routing` - Tool call suggestions and routing

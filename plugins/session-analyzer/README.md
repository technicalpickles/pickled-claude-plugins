# session-analyzer Plugin

Tools for analyzing Claude Code session logs and tool call failures.

## Scripts

### find-failures.py

Find failed tool calls in Claude session logs.

**Usage:**
```bash
./find-failures.py PATH [PATH ...] [--json]
```

**Features:**
- Scans JSONL session logs in `~/.claude/projects`
- Identifies tool calls that returned errors
- Displays tool name, input parameters, and error messages
- Supports JSON output for programmatic processing
- Tracks request/response UUID chains

**Output includes:**
- File path and session location
- Tool name that failed
- Tool input parameters (formatted by tool type)
- Error content and messages
- Request and response UUIDs for tracing

**Example:**
```bash
# Find all failures in a project
./find-failures.py ~/.claude/projects/my-project/

# Output as JSON for processing
./find-failures.py ~/.claude/projects/my-project/ --json | jq .
```

## Installation

```bash
/plugin install session-analyzer@technicalpickles-marketplace
```

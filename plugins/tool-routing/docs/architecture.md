# Architecture

This document describes the internal architecture of the tool-routing plugin for contributors.

## Overview

The plugin intercepts tool calls via Claude Code's hook system, checks them against configured route patterns, and blocks calls that match while providing helpful alternative suggestions.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Claude Code │────▶│ preToolUse   │────▶│ tool-routing│
│             │     │ hook         │     │ check       │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌───────────────────────────┘
                    ▼
            ┌───────────────┐
            │ Load routes   │
            │ from all      │
            │ sources       │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ Check tool    │
            │ call against  │
            │ patterns      │
            └───────┬───────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│ Exit 0        │       │ Exit 2        │
│ (allow)       │       │ (block)       │
└───────────────┘       └───────────────┘
```

## Module Structure

```
src/tool_routing/
├── __init__.py      # Package metadata (version)
├── __main__.py      # Entry point: calls cli.main()
├── cli.py           # Command-line interface & environment handling
├── config.py        # Route loading, merging, and discovery
├── checker.py       # Pattern matching logic
└── test_runner.py   # Inline test execution
```

### cli.py

Responsibilities:
- Parse command-line arguments (`check`, `test`, `list`)
- Read environment variables (`CLAUDE_PLUGIN_ROOT`, etc.)
- Orchestrate route loading and command execution
- Handle stdin/stdout/stderr for hook communication

Key functions:
- `get_plugin_root()` - Resolve plugin root from environment
- `get_all_routes()` - Load and merge routes from all sources
- `cmd_check()` - Hook entry point
- `cmd_test()` - Run inline tests
- `cmd_list()` - Display merged routes

### config.py

Responsibilities:
- Define data models (`Route`, `TestCase`)
- Load routes from YAML files
- Discover route files across plugins and projects
- Merge routes with conflict detection

Key functions:
- `load_routes_file(path)` - Parse a single YAML file
- `discover_plugin_routes(plugins_dir)` - Find `*/hooks/tool-routes.yaml`
- `discover_project_routes(project_root)` - Find `.claude/tool-routes.yaml`
- `merge_routes_dicts(route_dicts, sources)` - Combine with conflict detection
- `load_all_routes(plugins_dir, project_root)` - Full discovery + merge

Exceptions:
- `RouteConflictError` - Same route name in multiple sources

### checker.py

Responsibilities:
- Map tool names to input fields
- Match patterns against tool input
- Return structured check results

Key components:
- `TOOL_INPUT_FIELDS` - Maps tool name to field (`WebFetch` → `url`, `Bash` → `command`)
- `CheckResult` - Dataclass with blocked status, route name, message, matched value
- `check_tool_call(tool_call, routes)` - Main matching function

Matching behavior:
- Uses `re.search()` (not `re.match()`) - pattern can match anywhere
- Uses `re.IGNORECASE` - case-insensitive matching
- First match wins - returns immediately on match
- Fails open on regex errors - invalid patterns are skipped

### test_runner.py

Responsibilities:
- Execute inline test fixtures
- Format test results for display

Key components:
- `TestResult` - Dataclass for individual test outcomes
- `run_route_tests(routes)` - Execute all tests
- `format_results(results, source)` - Generate human-readable output

## Data Models

### Route

```python
@dataclass
class Route:
    tool: str                    # Tool name to match (WebFetch, Bash)
    pattern: str                 # Regex pattern
    message: str                 # Message shown when blocked
    tests: list[TestCase]        # Inline test fixtures
    source: Optional[str]        # File path where defined
```

### TestCase

```python
@dataclass
class TestCase:
    input: dict                  # Tool call to test
    expect: str                  # "block" or "allow"
    desc: Optional[str]          # Human-readable description
    contains: Optional[str]      # String that must be in message
```

### CheckResult

```python
@dataclass
class CheckResult:
    blocked: bool                # Whether tool call is blocked
    route_name: Optional[str]    # Name of matching route
    message: Optional[str]       # Message to show user
    matched_value: Optional[str] # The value that matched
    pattern: Optional[str]       # The pattern that matched
```

## Design Decisions

### Fail-Open Philosophy

The plugin fails open at every level:

| Failure | Behavior |
|---------|----------|
| Missing route file | Silently skipped |
| YAML parse error | File skipped, continues |
| Invalid regex | Route skipped, continues |
| Route conflict | Error logged, no routes loaded |
| JSON parse error (stdin) | Tool call allowed |
| Unknown tool type | Tool call allowed |

Rationale: A misconfigured routing rule should never prevent legitimate work. Better to allow an undesirable action than to block a necessary one.

### First-Match Semantics

The checker returns on the first matching route rather than collecting all matches:

```python
for route_name, route in routes.items():
    if re.search(route.pattern, value, re.IGNORECASE):
        return CheckResult(blocked=True, ...)  # Return immediately
```

Rationale:
- Simpler mental model (one route blocks, one message shown)
- Better performance (no need to check remaining routes)
- Order is deterministic (sorted paths, dict insertion order)

### Case-Insensitive Matching

All patterns use `re.IGNORECASE`:

```python
re.search(route.pattern, value, re.IGNORECASE)
```

Rationale: URLs and commands shouldn't be blocked differently based on case. `GITHUB.COM` and `github.com` should both match.

### Inline Tests

Tests are embedded in the route YAML rather than separate files:

```yaml
routes:
  github-pr:
    pattern: "..."
    tests:
      - input: {...}
        expect: block
```

Rationale:
- Tests live with the code they test (easy to keep in sync)
- No separate test discovery mechanism needed
- Self-documenting routes (tests show intent)

### Exit Code 2 for Blocked

The `check` command uses exit code `2` (not `1`) for blocked calls:

```python
if result.blocked:
    print(result.message, file=sys.stderr)
    return 2  # Not 1
```

Rationale: Claude Code hooks interpret exit code `2` as "block the tool call." Exit code `1` typically means "error" which would be handled differently.

## Adding New Tool Types

To add support for a new tool type:

1. **Update `TOOL_INPUT_FIELDS` in checker.py:**

```python
TOOL_INPUT_FIELDS = {
    "WebFetch": "url",
    "Bash": "command",
    "NewTool": "field_name",  # Add mapping
}
```

2. **Register the hook in hooks.json:**

```json
{
  "matcher": { "tool_name": "NewTool" },
  "hooks": [{
    "type": "preToolUse",
    "command": "uv run --project $CLAUDE_PLUGIN_ROOT tool-routing check"
  }]
}
```

3. **Add routes in tool-routes.yaml:**

```yaml
routes:
  new-tool-route:
    tool: NewTool
    pattern: "..."
    message: "..."
```

## Testing

### Running Tests

```bash
# Inline route tests
uv run tool-routing test

# Unit tests
uv run pytest
```

### Test Coverage

- `test_config.py` - Route loading, merging, discovery, conflicts
- `test_checker.py` - Pattern matching, tool field mapping
- `test_cli.py` - CLI commands, environment handling

## Dependencies

- **PyYAML** - YAML parsing for route files
- **Python 3.10+** - Type hints, dataclasses

No external runtime dependencies beyond PyYAML.

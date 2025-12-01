# Tool Routing Hook Fixtures

This directory contains test fixtures for the tool routing hook system. Fixtures allow testing without using heredocs (which can trigger the hooks themselves).

## Directory Structure

```
fixtures/
├── webfetch/          # WebFetch tool test cases
│   ├── atlassian-url.json
│   ├── github-pr.json
│   ├── buildkite-build.json
│   └── allowed-url.json
└── bash/              # Bash tool test cases
    ├── mcp-list-tools.json
    ├── mcp-search.json
    ├── cat-heredoc-redirect.json
    ├── echo-chain.json
    └── normal-command.json
```

## Fixture Format

Each fixture is a JSON file with this structure:

```json
{
  "name": "Human-readable test name",
  "tool_call": {
    "tool_name": "ToolName",
    "tool_input": {
      "parameter": "value"
    }
  },
  "expected_exit": 0,
  "assertions": {
    "should_contain": "expected text in output",
    "should_not_contain": "text that should not appear"
  }
}
```

### Fields

- `name` (string, required): Descriptive test name
- `tool_call` (object, required): The tool call data to test
  - `tool_name` (string): Name of the tool (e.g., "WebFetch", "Bash")
  - `tool_input` (object): Tool-specific parameters
- `expected_exit` (number, required): Expected exit code
  - `0`: Tool should be allowed
  - `2`: Tool should be blocked
- `assertions` (object, optional): Output validation
  - `should_contain`: String that must appear in stdout/stderr
  - `should_not_contain`: String that must not appear in output

## Usage

### Automated Testing

Run all fixtures (and legacy inline tests):

```bash
cd plugins/dev-tools
uv run hooks/test_tool_routing.py
```

### Manual Testing

Test a single fixture:

```bash
cd plugins/dev-tools
./hooks/run_fixture.sh hooks/fixtures/webfetch/github-pr.json
```

Test with debug mode:

```bash
./hooks/run_fixture.sh hooks/fixtures/bash/mcp-search.json debug
```

List all available fixtures:

```bash
./hooks/run_fixture.sh
```

## Benefits

1. **No heredoc triggering**: Fixtures pass JSON directly via `subprocess.run()`, avoiding heredocs
2. **Reusable**: Same fixtures work for automated tests and manual verification
3. **Version controlled**: Test cases are explicit data files, easy to review
4. **Easy to add**: Just create a new JSON file in the appropriate directory

## Adding New Fixtures

1. Create a JSON file in the appropriate subdirectory (`webfetch/` or `bash/`)
2. Follow the fixture format above
3. Run the test suite to verify it works
4. Manually test with `run_fixture.sh` if needed

The test runner (`test_tool_routing.py`) automatically discovers all `.json` files in the fixtures directory.

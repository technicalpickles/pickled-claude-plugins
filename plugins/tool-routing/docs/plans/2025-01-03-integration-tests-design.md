# Integration Tests for Tool Routing

## Overview

Add integration testing that verifies tool-routing hooks actually block tool calls at runtime, not just that patterns match.

The existing `tool-routing test` command tests pattern matching in Python. The new `tool-routing integration-test` command enables main agent to spawn subagents that attempt real tool calls, then evaluates whether blocking worked.

## Architecture

```
Main Agent                          Subagent
    │
    ├─► uv run tool-routing integration-test --list
    │   (returns JSON list of test cases)
    │
    ├─► Task tool with prompt:
    │   "Try these tool calls, report what happened"
    │                                    │
    │                                    ├─► WebFetch PR URL → blocked
    │                                    ├─► WebFetch normal URL → allowed
    │                                    └─► returns JSON report
    │
    ├─► Saves report to temp file
    │
    ├─► uv run tool-routing integration-test --evaluate \
    │     --tests /tmp/tests.json --report /tmp/report.json
    │
    └─► Shows pass/fail results to user
```

## CLI Interface

### List Test Cases

```bash
uv run tool-routing integration-test --list
```

Output:
```json
[
  {
    "id": 0,
    "route": "github-pr",
    "desc": "PR URL should block",
    "tool": "WebFetch",
    "input": {"url": "https://github.com/foo/bar/pull/123"},
    "expect": "block",
    "contains": "gh pr view"
  }
]
```

Exit code: 0 (or 1 on error)

### Evaluate Report

```bash
uv run tool-routing integration-test --evaluate \
  --tests /tmp/tests.json \
  --report /tmp/report.json
```

Human-readable output (default):
```
Integration Test Results
========================

/path/to/tool-routes.yaml
  ✓ github-pr: PR URL should block
  ✓ github-pr: repo URL should allow
  ✗ bash-mcp-cli: mcp list-tools should block
      Expected: block, Got: allowed

3 passed, 1 failed
```

JSON output (`--json` flag):
```json
{
  "passed": 3,
  "failed": 1,
  "results": [
    {"id": 0, "route": "github-pr", "desc": "PR URL should block", "passed": true},
    {"id": 2, "route": "bash-mcp-cli", "desc": "mcp list-tools should block", "passed": false, "expected": "block", "actual": "allowed"}
  ]
}
```

Exit code: 0 if all pass, 1 if any fail

## Expected Report Format

Subagent returns JSON array:
```json
[
  {"id": 0, "result": "blocked", "message": "Use `gh pr view`..."},
  {"id": 1, "result": "allowed", "message": null}
]
```

## Subagent Prompt Template

```markdown
INTEGRATION TEST: Tool Routing Verification

You will attempt specific tool calls and report exactly what happens.

IMPORTANT RULES:
- Use EXACTLY the tool and input specified for each test
- Do NOT use alternatives or workarounds if blocked
- Report what happened, do not interpret or fix

For each test, attempt the tool call and record:
- "blocked" if the tool was blocked (you'll see an error message)
- "allowed" if the tool executed (even if it returned an error like 404)

## Tests

Test 0: Use WebFetch with url="https://github.com/foo/bar/pull/123"
Test 1: Use WebFetch with url="https://example.com"
Test 2: Use Bash with command="mcp list-tools"

## Response Format

After attempting ALL tests, respond with a JSON array:

```json
[
  {"id": 0, "result": "blocked", "message": "the block message you saw"},
  {"id": 1, "result": "allowed", "message": null},
  {"id": 2, "result": "blocked", "message": "the block message you saw"}
]
```

Only include the JSON array in your response, nothing else.
```

## Evaluate Logic

1. Match report entries to tests by `id`
2. Compare `result` ("blocked"/"allowed") to `expect` ("block"/"allow")
3. If test has `contains`, verify blocked message includes that string
4. Missing report entries count as failures

## File Changes

### New: `src/tool_routing/integration_runner.py`

- `list_integration_tests(routes) -> list[dict]` - Convert routes to JSON-serializable test cases with sequential IDs
- `evaluate_report(tests, report) -> EvaluateResult` - Compare report to expectations
- `format_evaluate_results(result, json_output) -> str` - Format for display

### Modified: `src/tool_routing/cli.py`

- Add `integration-test` subcommand
- Arguments: `--list`, `--evaluate`, `--tests`, `--report`, `--json`
- `cmd_integration_test(args)` - Route to list or evaluate based on args

### Unchanged

- `tool-routes.yaml` - Reuses existing `tests` array
- `config.py` - Test data structure unchanged
- `test_runner.py` - Existing pattern tests unchanged

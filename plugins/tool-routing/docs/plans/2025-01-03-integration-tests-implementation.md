# Integration Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `integration-test` subcommand that outputs test cases for subagent execution and evaluates results.

**Architecture:** New `integration_runner.py` module with `list_tests()` and `evaluate_report()` functions, called from new CLI subcommand. Reuses existing `TestCase` data from routes.

**Tech Stack:** Python, dataclasses, JSON, argparse

---

### Task 1: Add `list_integration_tests` function

**Files:**
- Create: `src/tool_routing/integration_runner.py`
- Test: `tests/test_integration_runner.py`

**Step 1: Write the failing test**

Create `tests/test_integration_runner.py`:

```python
"""Tests for integration test runner."""

import pytest

from tool_routing.config import Route, TestCase
from tool_routing.integration_runner import list_integration_tests


def test_list_integration_tests_basic():
    """List converts routes to JSON-serializable test cases with IDs."""
    routes = {
        "test-route": Route(
            tool="WebFetch",
            pattern="example\\.com",
            message="Use something else",
            tests=[
                TestCase(
                    input={"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}},
                    expect="block",
                    desc="should block example.com",
                    contains="something else",
                ),
                TestCase(
                    input={"tool_name": "WebFetch", "tool_input": {"url": "https://other.com"}},
                    expect="allow",
                    desc="should allow other.com",
                ),
            ],
            source="/path/to/routes.yaml",
        ),
    }

    result = list_integration_tests(routes)

    assert len(result) == 2
    assert result[0] == {
        "id": 0,
        "route": "test-route",
        "desc": "should block example.com",
        "tool": "WebFetch",
        "input": {"url": "https://example.com"},
        "expect": "block",
        "contains": "something else",
    }
    assert result[1] == {
        "id": 1,
        "route": "test-route",
        "desc": "should allow other.com",
        "tool": "WebFetch",
        "input": {"url": "https://other.com"},
        "expect": "allow",
        "contains": None,
    }


def test_list_integration_tests_empty():
    """List returns empty array for routes with no tests."""
    routes = {
        "no-tests": Route(
            tool="WebFetch",
            pattern="example\\.com",
            message="msg",
            tests=[],
        ),
    }

    result = list_integration_tests(routes)

    assert result == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_integration_runner.py -v`
Expected: FAIL with "No module named 'tool_routing.integration_runner'"

**Step 3: Write minimal implementation**

Create `src/tool_routing/integration_runner.py`:

```python
"""Integration test runner for tool routing."""

from tool_routing.config import Route


def list_integration_tests(routes: dict[str, Route]) -> list[dict]:
    """Convert routes to JSON-serializable test cases with sequential IDs.

    Args:
        routes: Dictionary of routes with inline tests

    Returns:
        List of test case dicts with id, route, desc, tool, input, expect, contains
    """
    tests = []
    test_id = 0

    for route_name, route in routes.items():
        for test in route.tests:
            tests.append({
                "id": test_id,
                "route": route_name,
                "desc": test.desc or f"test {test_id}",
                "tool": test.input.get("tool_name", route.tool),
                "input": test.input.get("tool_input", {}),
                "expect": test.expect,
                "contains": test.contains,
            })
            test_id += 1

    return tests
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_integration_runner.py -v`
Expected: PASS

**Step 5: Commit**

```
git add src/tool_routing/integration_runner.py tests/test_integration_runner.py
git commit -m "feat(tool-routing): add list_integration_tests function"
```

---

### Task 2: Add `evaluate_report` function

**Files:**
- Modify: `src/tool_routing/integration_runner.py`
- Test: `tests/test_integration_runner.py`

**Step 1: Write the failing test**

Add to `tests/test_integration_runner.py`:

```python
from tool_routing.integration_runner import evaluate_report, EvaluateResult


def test_evaluate_report_all_pass():
    """Evaluate returns pass when all results match expectations."""
    tests = [
        {"id": 0, "route": "r1", "desc": "d1", "tool": "WebFetch", "input": {}, "expect": "block", "contains": "msg"},
        {"id": 1, "route": "r2", "desc": "d2", "tool": "WebFetch", "input": {}, "expect": "allow", "contains": None},
    ]
    report = [
        {"id": 0, "result": "blocked", "message": "Use msg instead"},
        {"id": 1, "result": "allowed", "message": None},
    ]

    result = evaluate_report(tests, report)

    assert result.passed == 2
    assert result.failed == 0
    assert len(result.results) == 2
    assert all(r["passed"] for r in result.results)


def test_evaluate_report_with_failures():
    """Evaluate detects mismatches between expected and actual."""
    tests = [
        {"id": 0, "route": "r1", "desc": "d1", "tool": "WebFetch", "input": {}, "expect": "block", "contains": None},
        {"id": 1, "route": "r2", "desc": "d2", "tool": "WebFetch", "input": {}, "expect": "allow", "contains": None},
    ]
    report = [
        {"id": 0, "result": "allowed", "message": None},  # Should have been blocked
        {"id": 1, "result": "allowed", "message": None},  # Correct
    ]

    result = evaluate_report(tests, report)

    assert result.passed == 1
    assert result.failed == 1
    assert result.results[0]["passed"] is False
    assert result.results[0]["expected"] == "block"
    assert result.results[0]["actual"] == "allow"


def test_evaluate_report_contains_check():
    """Evaluate checks contains string in blocked message."""
    tests = [
        {"id": 0, "route": "r1", "desc": "d1", "tool": "WebFetch", "input": {}, "expect": "block", "contains": "gh pr view"},
    ]
    report = [
        {"id": 0, "result": "blocked", "message": "Use something else"},  # Missing expected text
    ]

    result = evaluate_report(tests, report)

    assert result.failed == 1
    assert "contains" in result.results[0].get("error", "")


def test_evaluate_report_missing_result():
    """Evaluate treats missing report entries as failures."""
    tests = [
        {"id": 0, "route": "r1", "desc": "d1", "tool": "WebFetch", "input": {}, "expect": "block", "contains": None},
        {"id": 1, "route": "r2", "desc": "d2", "tool": "WebFetch", "input": {}, "expect": "allow", "contains": None},
    ]
    report = [
        {"id": 0, "result": "blocked", "message": "msg"},
        # id 1 missing
    ]

    result = evaluate_report(tests, report)

    assert result.passed == 1
    assert result.failed == 1
    assert "missing" in result.results[1].get("error", "").lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_integration_runner.py::test_evaluate_report_all_pass -v`
Expected: FAIL with "cannot import name 'evaluate_report'"

**Step 3: Write minimal implementation**

Add to `src/tool_routing/integration_runner.py`:

```python
from dataclasses import dataclass, field


@dataclass
class EvaluateResult:
    """Result of evaluating integration test report."""

    passed: int
    failed: int
    results: list[dict] = field(default_factory=list)


def evaluate_report(tests: list[dict], report: list[dict]) -> EvaluateResult:
    """Compare subagent report to test expectations.

    Args:
        tests: List of test cases from list_integration_tests()
        report: List of results from subagent

    Returns:
        EvaluateResult with pass/fail counts and detailed results
    """
    # Index report by id for lookup
    report_by_id = {r["id"]: r for r in report}

    results = []
    passed = 0
    failed = 0

    for test in tests:
        test_id = test["id"]
        result_entry = {
            "id": test_id,
            "route": test["route"],
            "desc": test["desc"],
        }

        if test_id not in report_by_id:
            result_entry["passed"] = False
            result_entry["error"] = "Missing from report"
            failed += 1
            results.append(result_entry)
            continue

        report_entry = report_by_id[test_id]
        actual = report_entry["result"]
        expected = test["expect"]

        # Normalize: "blocked" -> "block", "allowed" -> "allow"
        actual_normalized = actual.rstrip("ed")

        if actual_normalized != expected:
            result_entry["passed"] = False
            result_entry["expected"] = expected
            result_entry["actual"] = actual_normalized
            failed += 1
        elif test.get("contains") and expected == "block":
            message = report_entry.get("message") or ""
            if test["contains"] not in message:
                result_entry["passed"] = False
                result_entry["error"] = f"Message does not contain '{test['contains']}'"
                failed += 1
            else:
                result_entry["passed"] = True
                passed += 1
        else:
            result_entry["passed"] = True
            passed += 1

        results.append(result_entry)

    return EvaluateResult(passed=passed, failed=failed, results=results)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_integration_runner.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```
git add src/tool_routing/integration_runner.py tests/test_integration_runner.py
git commit -m "feat(tool-routing): add evaluate_report function"
```

---

### Task 3: Add `format_evaluate_results` function

**Files:**
- Modify: `src/tool_routing/integration_runner.py`
- Test: `tests/test_integration_runner.py`

**Step 1: Write the failing test**

Add to `tests/test_integration_runner.py`:

```python
from tool_routing.integration_runner import format_evaluate_results


def test_format_evaluate_results_human():
    """Format produces human-readable output by default."""
    result = EvaluateResult(
        passed=2,
        failed=1,
        results=[
            {"id": 0, "route": "r1", "desc": "d1", "passed": True},
            {"id": 1, "route": "r2", "desc": "d2", "passed": True},
            {"id": 2, "route": "r3", "desc": "d3", "passed": False, "expected": "block", "actual": "allow"},
        ],
    )

    output = format_evaluate_results(result, json_output=False)

    assert "✓ r1: d1" in output
    assert "✓ r2: d2" in output
    assert "✗ r3: d3" in output
    assert "Expected: block, Got: allow" in output
    assert "2 passed, 1 failed" in output


def test_format_evaluate_results_json():
    """Format produces JSON when json_output=True."""
    result = EvaluateResult(
        passed=1,
        failed=0,
        results=[{"id": 0, "route": "r1", "desc": "d1", "passed": True}],
    )

    output = format_evaluate_results(result, json_output=True)

    import json
    parsed = json.loads(output)
    assert parsed["passed"] == 1
    assert parsed["failed"] == 0
    assert len(parsed["results"]) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_integration_runner.py::test_format_evaluate_results_human -v`
Expected: FAIL with "cannot import name 'format_evaluate_results'"

**Step 3: Write minimal implementation**

Add to `src/tool_routing/integration_runner.py`:

```python
import json


def format_evaluate_results(result: EvaluateResult, json_output: bool = False) -> str:
    """Format evaluation results for display.

    Args:
        result: EvaluateResult from evaluate_report()
        json_output: If True, return JSON; otherwise human-readable

    Returns:
        Formatted string
    """
    if json_output:
        return json.dumps({
            "passed": result.passed,
            "failed": result.failed,
            "results": result.results,
        }, indent=2)

    lines = ["Integration Test Results", "=" * 24, ""]

    for r in result.results:
        status = "✓" if r["passed"] else "✗"
        lines.append(f"  {status} {r['route']}: {r['desc']}")
        if not r["passed"]:
            if "expected" in r:
                lines.append(f"      Expected: {r['expected']}, Got: {r['actual']}")
            elif "error" in r:
                lines.append(f"      {r['error']}")

    lines.append("")
    lines.append(f"{result.passed} passed, {result.failed} failed")

    return "\n".join(lines)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_integration_runner.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```
git add src/tool_routing/integration_runner.py tests/test_integration_runner.py
git commit -m "feat(tool-routing): add format_evaluate_results function"
```

---

### Task 4: Add `integration-test --list` CLI subcommand

**Files:**
- Modify: `src/tool_routing/cli.py`
- Test: Manual verification (subprocess tests have pre-existing issues)

**Step 1: Add the subcommand to CLI**

Add imports at top of `src/tool_routing/cli.py`:

```python
from tool_routing.integration_runner import (
    list_integration_tests,
    evaluate_report,
    format_evaluate_results,
)
```

Add command handler after `cmd_list`:

```python
def cmd_integration_test(args: argparse.Namespace) -> int:
    """Run integration test operations."""
    if args.list_tests:
        return cmd_integration_list()
    elif args.evaluate:
        return cmd_integration_evaluate(args)
    else:
        print("Either --list or --evaluate is required", file=sys.stderr)
        return 1


def cmd_integration_list() -> int:
    """List integration tests as JSON."""
    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    if not routes:
        print("[]")
        return 0

    tests = list_integration_tests(routes)
    print(json.dumps(tests, indent=2))
    return 0
```

Add subparser in `main()` after the list subparser:

```python
    # integration-test subcommand
    integration_parser = subparsers.add_parser(
        "integration-test",
        help="Integration testing via subagents",
    )
    integration_parser.add_argument(
        "--list",
        dest="list_tests",
        action="store_true",
        help="List test cases as JSON",
    )
    integration_parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate subagent report",
    )
    integration_parser.add_argument(
        "--tests",
        type=str,
        help="Path to tests JSON file (for --evaluate)",
    )
    integration_parser.add_argument(
        "--report",
        type=str,
        help="Path to report JSON file (for --evaluate)",
    )
    integration_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output results as JSON",
    )
    integration_parser.set_defaults(func=cmd_integration_test)
```

**Step 2: Verify manually**

Run: `uv run tool-routing integration-test --list | head -20`
Expected: JSON array of test cases

**Step 3: Commit**

```
git add src/tool_routing/cli.py
git commit -m "feat(tool-routing): add integration-test --list command"
```

---

### Task 5: Add `integration-test --evaluate` CLI subcommand

**Files:**
- Modify: `src/tool_routing/cli.py`

**Step 1: Add the evaluate handler**

Add after `cmd_integration_list` in `src/tool_routing/cli.py`:

```python
def cmd_integration_evaluate(args: argparse.Namespace) -> int:
    """Evaluate integration test report."""
    if not args.tests or not args.report:
        print("--tests and --report are required with --evaluate", file=sys.stderr)
        return 1

    # Load tests file
    try:
        with open(args.tests) as f:
            tests = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading tests file: {e}", file=sys.stderr)
        return 1

    # Load report file
    try:
        with open(args.report) as f:
            report = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading report file: {e}", file=sys.stderr)
        return 1

    result = evaluate_report(tests, report)
    print(format_evaluate_results(result, json_output=args.json_output))

    return 0 if result.failed == 0 else 1
```

**Step 2: Create test fixtures and verify manually**

```bash
# Create test files
uv run tool-routing integration-test --list > /tmp/tests.json

# Create a mock report (simulate subagent output)
cat > /tmp/report.json << 'EOF'
[
  {"id": 0, "result": "blocked", "message": "Use `gh pr view`"},
  {"id": 1, "result": "allowed", "message": null}
]
EOF

# Run evaluate
uv run tool-routing integration-test --evaluate --tests /tmp/tests.json --report /tmp/report.json
```

Expected: Human-readable output showing pass/fail for each test

**Step 3: Commit**

```
git add src/tool_routing/cli.py
git commit -m "feat(tool-routing): add integration-test --evaluate command"
```

---

### Task 6: Run full test suite and verify

**Step 1: Run all unit tests**

Run: `uv run pytest tests/test_integration_runner.py tests/test_checker.py tests/test_config.py tests/test_plugin_structure.py -v`
Expected: All tests pass

**Step 2: Run inline route tests**

Run: `uv run tool-routing test`
Expected: All route tests pass

**Step 3: Manual integration test of new commands**

```bash
# List tests
uv run tool-routing integration-test --list | jq 'length'
# Expected: Number matching total tests in tool-routes.yaml

# Create mock passing report
uv run tool-routing integration-test --list > /tmp/tests.json
# Manually create report.json with correct results, then:
uv run tool-routing integration-test --evaluate --tests /tmp/tests.json --report /tmp/report.json --json | jq .
```

**Step 4: Commit any fixes if needed**

---

### Task 7: Update /validate command documentation

**Files:**
- Modify: `.claude-plugin/commands/validate.md`

**Step 1: Add integration test section**

Add to the end of `.claude-plugin/commands/validate.md`:

```markdown
## Step 5: Run Integration Tests (Optional)

For full verification that hooks block at runtime:

1. Get test cases:
   ```bash
   uv run tool-routing integration-test --list > /tmp/integration-tests.json
   ```

2. Spawn a subagent to execute the tests (see design doc for prompt template)

3. Save subagent's JSON report to `/tmp/integration-report.json`

4. Evaluate:
   ```bash
   uv run tool-routing integration-test --evaluate \
     --tests /tmp/integration-tests.json \
     --report /tmp/integration-report.json
   ```
```

**Step 2: Commit**

```
git add .claude-plugin/commands/validate.md
git commit -m "docs(tool-routing): add integration test steps to validate command"
```

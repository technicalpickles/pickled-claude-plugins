"""Integration test runner for tool routing."""

from dataclasses import dataclass, field

from tool_routing.config import Route


@dataclass
class EvaluateResult:
    """Result of evaluating integration test report."""

    passed: int
    failed: int
    results: list[dict] = field(default_factory=list)


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
        if actual.endswith("ed"):
            actual_normalized = actual[:-2]
        else:
            actual_normalized = actual

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

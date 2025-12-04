"""Tests for integration test runner."""

import pytest

from tool_routing.config import Route, TestCase
from tool_routing.integration_runner import list_integration_tests, evaluate_report, EvaluateResult


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
    assert "does not contain" in result.results[0].get("error", "")


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

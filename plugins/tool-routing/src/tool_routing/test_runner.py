"""Test runner for inline route fixtures."""

from dataclasses import dataclass
from typing import Optional

from tool_routing.checker import check_tool_call
from tool_routing.config import Route


@dataclass
class TestResult:
    """Result of running a single test."""

    route_name: str
    desc: str
    passed: bool
    expected: str
    actual: str
    contains_error: Optional[str] = None  # If contains check failed


def run_route_tests(routes: dict[str, Route]) -> list[TestResult]:
    """Run all inline tests for routes.

    Args:
        routes: Dictionary of routes with inline tests

    Returns:
        List of test results
    """
    results = []

    for route_name, route in routes.items():
        for test in route.tests:
            # Run the check
            check_result = check_tool_call(test.input, routes)

            # Determine actual result
            actual = "block" if check_result.blocked else "allow"
            passed = actual == test.expect

            # Check contains if specified and test passed so far
            contains_error = None
            if passed and test.contains and check_result.blocked:
                if test.contains not in (check_result.message or ""):
                    passed = False
                    contains_error = (
                        f"Expected message to contain '{test.contains}'"
                    )

            results.append(
                TestResult(
                    route_name=route_name,
                    desc=test.desc or f"test {len(results) + 1}",
                    passed=passed,
                    expected=test.expect,
                    actual=actual,
                    contains_error=contains_error,
                )
            )

    return results


def format_results(results: list[TestResult], source: str) -> str:
    """Format test results for display.

    Args:
        results: List of test results
        source: Source file path

    Returns:
        Formatted string for display
    """
    lines = [source]

    for result in results:
        status = "✓" if result.passed else "✗"
        lines.append(f"  {status} {result.route_name}: {result.desc}")
        if not result.passed:
            if result.contains_error:
                lines.append(f"      {result.contains_error}")
            else:
                lines.append(
                    f"      Expected: {result.expected}, Got: {result.actual}"
                )

    return "\n".join(lines)

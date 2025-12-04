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

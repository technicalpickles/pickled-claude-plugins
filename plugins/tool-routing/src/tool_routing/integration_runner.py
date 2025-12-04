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

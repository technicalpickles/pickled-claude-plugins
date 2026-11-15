from tool_routing.config import Route, TestCase
from tool_routing.test_runner import run_route_tests


def _route(pattern, tests):
    return Route(
        tool="Bash", pattern=pattern, message="no", tests=tests, source="x"
    )


def _test(command, expect):
    return TestCase(
        desc=command,
        input={"tool_name": "Bash", "tool_input": {"command": command}},
        expect=expect,
    )


def test_allow_test_ignores_other_routes():
    routes = {
        "mine": _route("alpha", [_test("beta", "allow")]),
        "other": _route("beta", []),
    }
    assert all(r.passed for r in run_route_tests(routes))


def test_block_test_is_not_satisfied_by_other_routes():
    routes = {
        "mine": _route("alpha", [_test("beta", "block")]),
        "other": _route("beta", []),
    }
    assert not any(r.passed for r in run_route_tests(routes))


def test_merged_mode_sees_other_routes():
    routes = {
        "mine": _route("alpha", [_test("beta", "allow")]),
        "other": _route("beta", []),
    }
    assert not any(r.passed for r in run_route_tests(routes, merged=True))

import subprocess
import sys
from pathlib import Path

from tool_routing.checker import matching_routes
from tool_routing.config import Route, TestCase
from tool_routing.overlap import find_overlaps, load_corpus


def _call(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _route(pattern, tests=()):
    return Route(tool="Bash", pattern=pattern, message="no", tests=list(tests), source="x")


def _test(command, expect):
    return TestCase(input=_call(command), expect=expect, desc=command)


def test_matching_routes_returns_every_match():
    routes = {"a": _route("foo"), "b": _route("foo bar"), "c": _route("baz")}
    assert matching_routes(_call("foo bar"), routes) == ["a", "b"]


def test_allow_input_matched_by_another_route_is_an_error():
    routes = {
        "mine": _route("alpha", [_test("beta", "allow")]),
        "other": _route("beta"),
    }
    findings = find_overlaps(routes)
    assert [(f.severity, f.matches) for f in findings] == [("error", ["other"])]


def test_block_input_matched_by_another_route_is_a_warning():
    routes = {
        "mine": _route("alpha", [_test("alpha beta", "block")]),
        "other": _route("beta"),
    }
    findings = find_overlaps(routes)
    assert [(f.severity, f.matches) for f in findings] == [("warning", ["mine", "other"])]


def test_no_overlap_means_no_findings():
    routes = {
        "mine": _route("alpha", [_test("alpha", "block"), _test("gamma", "allow")]),
        "other": _route("beta"),
    }
    assert find_overlaps(routes) == []


def test_corpus_block_case_needs_exact_routes():
    routes = {"a": _route("foo"), "b": _route("foo")}
    corpus = [{"desc": "x", "input": _call("foo"), "expect": "block", "routes": ["a"]}]
    findings = find_overlaps(routes, corpus)
    assert [f.severity for f in findings] == ["error"]


def test_corpus_allow_case_fails_on_any_match():
    routes = {"a": _route("foo")}
    corpus = [{"desc": "x", "input": _call("foo"), "expect": "allow"}]
    assert [f.severity for f in find_overlaps(routes, corpus)] == ["error"]


def test_load_corpus_reads_cases(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("cases:\n  - desc: d\n    input: {tool_name: Bash}\n    expect: allow\n")
    assert load_corpus(path)[0]["desc"] == "d"


def test_cli_overlap_exits_nonzero_on_error(tmp_path, cli_env):
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "tool-routes.yaml").write_text(
        """
routes:
  mine:
    tool: Bash
    pattern: "alpha"
    message: "no"
    tests:
      - desc: "beta allow"
        input: {tool_name: Bash, tool_input: {command: beta}}
        expect: allow
  other:
    tool: Bash
    pattern: "beta"
    message: "no"
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "overlap"],
        capture_output=True,
        text=True,
        env=cli_env,
    )
    assert result.returncode == 1
    assert "1 errors" in result.stdout

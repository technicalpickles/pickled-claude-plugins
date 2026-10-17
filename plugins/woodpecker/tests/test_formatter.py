from woodpecker_snapshot import formatter, states
from woodpecker_snapshot.cli import Pipeline, Step, WpError

from .helpers import fixture


def steps(*pairs):
    return [Step("woodpecker", name, state) for name, state in pairs]


def render(status, step_list, log=None, tail=50, pipeline_status=None):
    pipeline = Pipeline(11, pipeline_status or status, "b2" * 20, "main", "push")
    assessment = states.assess(status, step_list)
    return formatter.format_pipeline("o/n", pipeline, step_list, assessment, log, tail)


def test_state_is_the_first_line():
    out = render("failure", steps(("test", "failure")), log="boom\n")
    assert out.splitlines()[0] == "State: failed"


def test_failed_pipeline_shows_marked_step_and_clean_log_tail():
    out = render(
        "failure",
        steps(("clone", "success"), ("test-web", "failure")),
        log=fixture("log_failed_ansi.txt"),
    )
    assert "\x1b" not in out
    assert "woodpecker/test-web: failure  <- first failure" in out
    assert "Log tail (test-web, last" in out
    assert "AssertionError: expected 2 to be 0" in out


def test_tail_limits_lines():
    log = "".join("line %d\n" % i for i in range(200))
    out = render("failure", steps(("test", "failure")), log=log, tail=5)
    assert "line 199" in out
    assert "line 195" in out
    assert "line 194" not in out


def test_cascade_is_called_out():
    out = render(
        "failure",
        steps(("build", "success"), ("test", "failure"), ("package", "skipped"), ("deploy", "skipped")),
        log="x\n",
    )
    assert "2 later steps skipped" in out


def test_passed_pipeline_warns_about_ignored_failures():
    out = render("success", steps(("lint", "success"), ("typecheck", "failure")))
    assert out.splitlines()[0] == "State: passed"
    assert "typecheck" in out and "ignored" in out
    assert "Log tail" not in out


def test_running_pipeline_says_logs_are_partial():
    out = render("running", steps(("clone", "success"), ("test", "running")))
    assert out.splitlines()[0] == "State: running"
    assert "partial" in out


def test_unknown_status_keeps_raw_status_visible():
    out = render("something-new", steps(("a", "success")))
    assert out.splitlines()[0] == "State: unknown"
    assert "something-new" in out


def test_no_pipeline_lists_causes_and_recent_pipelines():
    recent = [Pipeline(12, "running", "a1" * 20, "feat/widgets", "push")]
    out = formatter.format_no_pipeline("o/n", "f" * 40, recent)
    assert out.splitlines()[0] == "State: no pipeline"
    assert "never means passing" in out
    assert "webhook" in out
    assert "#12" in out and "feat/widgets" in out


def test_no_pipeline_with_empty_history():
    out = formatter.format_no_pipeline("o/n", "f" * 40, [])
    assert "no pipelines at all" in out


def test_problem_states():
    cases = {
        WpError.NOT_INSTALLED: "State: not set up",
        WpError.NOT_CONFIGURED: "State: not set up",
        WpError.UNAUTHORIZED: "State: unauthorized",
        WpError.UNREACHABLE: "State: unreachable",
        WpError.NETWORK_DENIED: "State: unreachable",
        WpError.NOT_FOUND: "State: unknown",
        WpError.OTHER: "State: unknown",
    }
    for kind, first_line in cases.items():
        out = formatter.format_problem(WpError(kind, "msg"), "o/n")
        assert out.splitlines()[0] == first_line, kind


def test_network_denied_mentions_the_sandbox_allowlist():
    out = formatter.format_problem(WpError(WpError.NETWORK_DENIED, "x: Forbidden"), "o/n")
    assert "allowed_domains" in out


def test_not_configured_points_at_setup_and_setup_doc():
    out = formatter.format_problem(WpError(WpError.NOT_CONFIGURED, "x"), "o/n")
    assert "woodpecker-cli setup" in out
    assert "references/setup.md" in out

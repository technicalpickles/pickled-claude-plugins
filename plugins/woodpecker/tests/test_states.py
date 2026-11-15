import pytest

from woodpecker_snapshot import states
from woodpecker_snapshot.cli import Step


def steps(*pairs):
    return [Step("woodpecker", name, state) for name, state in pairs]


@pytest.mark.parametrize(
    "status,expected",
    [
        ("success", states.PASSED),
        ("failure", states.FAILED),
        ("error", states.FAILED),
        ("killed", states.FAILED),
        ("canceled", states.FAILED),
        ("running", states.RUNNING),
        ("pending", states.QUEUED),
        ("blocked", states.BLOCKED),
        ("something-new", states.UNKNOWN),
    ],
)
def test_status_maps_to_state(status, expected):
    assert states.assess(status, []).state == expected


def test_first_failed_step_wins_over_later_ones():
    result = states.assess(
        "failure",
        steps(("clone", "success"), ("test", "failure"), ("lint", "failure"), ("deploy", "skipped")),
    )
    assert result.first_failed.name == "test"


def test_cascade_counts_steps_skipped_after_the_failure():
    result = states.assess(
        "failure", steps(("build", "success"), ("test", "failure"), ("package", "skipped"), ("deploy", "skipped"))
    )
    assert result.skipped_after == 2


def test_passed_pipeline_reports_ignored_failures():
    result = states.assess("success", steps(("lint", "success"), ("typecheck", "failure")))
    assert result.state == states.PASSED
    assert [s.name for s in result.ignored_failures] == ["typecheck"]


def test_stopped_pipeline_says_so():
    result = states.assess("canceled", steps(("build", "success"), ("test", "killed")))
    assert result.state == states.FAILED
    assert "stopped" in result.detail


def test_failed_without_a_failed_step_explains_itself():
    result = states.assess("failure", steps(("clone", "success")))
    assert result.first_failed is None
    assert "no failed step" in result.detail


def test_unknown_status_keeps_the_raw_value():
    assert "something-new" in states.assess("something-new", []).detail


def test_state_derived_from_steps_when_status_missing():
    assert states.assess(None, steps(("a", "success"), ("b", "failure"))).state == states.FAILED
    assert states.assess(None, steps(("a", "success"), ("b", "running"))).state == states.RUNNING
    assert states.assess(None, steps(("a", "success"))).state == states.PASSED
    assert states.assess(None, []).state == states.UNKNOWN

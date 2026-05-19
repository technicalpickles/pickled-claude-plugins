import json
from pathlib import Path

from gha_snapshot.formatter import format_snapshot
from gha_snapshot.url_parser import RunRef

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _minimal_run():
    return {
        "workflowName": "CI",
        "number": 42,
        "conclusion": "failure",
        "event": "push",
        "headBranch": "main",
        "headSha": "abc1234deadbeef",
        "displayTitle": "fix the thing",
        "url": "https://github.com/octocat/Hello-World/actions/runs/123",
        "createdAt": "2026-05-18T12:00:00Z",
        "updatedAt": "2026-05-18T12:03:30Z",
        "jobs": [
            {
                "name": "build",
                "conclusion": "success",
                "url": "https://github.com/octocat/Hello-World/actions/runs/123/job/200",
                "startedAt": "2026-05-18T12:00:10Z",
                "completedAt": "2026-05-18T12:02:24Z",
                "steps": [],
            },
            {
                "name": "test",
                "conclusion": "failure",
                "url": "https://github.com/octocat/Hello-World/actions/runs/123/job/201",
                "startedAt": "2026-05-18T12:02:25Z",
                "completedAt": "2026-05-18T12:03:28Z",
                "steps": [
                    {"name": "Checkout", "conclusion": "success", "number": 1},
                    {"name": "Run npm test", "conclusion": "failure", "number": 2},
                ],
            },
            {
                "name": "deploy",
                "conclusion": "skipped",
                "url": "https://github.com/octocat/Hello-World/actions/runs/123/job/202",
                "startedAt": None,
                "completedAt": None,
                "steps": [],
            },
        ],
    }


class TestFormatSnapshot:
    def test_includes_run_header(self):
        log = (FIXTURE_DIR / "run_log_failed.txt").read_text()
        out = format_snapshot(_minimal_run(), log, RunRef("octocat", "Hello-World", 123), tail=50)
        assert "Run: CI #42" in out
        assert "Status: failure" in out
        assert "Trigger: push on main @ abc1234" in out
        assert "https://github.com/octocat/Hello-World/actions/runs/123" in out

    def test_job_list_uses_status_icons(self):
        out = format_snapshot(_minimal_run(), "", RunRef("octocat", "Hello-World", 123), tail=50)
        assert "✓ build" in out
        assert "✗ test" in out
        assert "⊘ deploy" in out

    def test_failed_step_section_includes_step_name_and_log_tail(self):
        log = (FIXTURE_DIR / "run_log_failed.txt").read_text()
        out = format_snapshot(_minimal_run(), log, RunRef("octocat", "Hello-World", 123), tail=50)
        assert 'Failed step output (test → "Run npm test"' in out
        assert "FAIL src/foo.test.ts" in out

    def test_annotations_grouped_by_job(self):
        log = (FIXTURE_DIR / "run_log_failed.txt").read_text()
        out = format_snapshot(_minimal_run(), log, RunRef("octocat", "Hello-World", 123), tail=50)
        assert "Annotations:" in out
        assert "test: ::error file=src/foo.ts,line=42::Expected 1, got 2" in out

    def test_links_section_lists_run_and_failed_jobs(self):
        out = format_snapshot(_minimal_run(), "", RunRef("octocat", "Hello-World", 123), tail=50)
        assert "Links:" in out
        assert "Run:" in out
        assert "test:" in out
        # successful jobs don't get listed
        assert "build:" not in out.split("Links:")[1]

    def test_tail_caps_log_output(self):
        # 100-line log
        log = "\n".join(f"test\tRun npm test\tline {i}" for i in range(100))
        out = format_snapshot(_minimal_run(), log, RunRef("octocat", "Hello-World", 123), tail=10)
        # Should contain the last 10 lines, not the first
        assert "line 99" in out
        assert "line 0" not in out

    def test_fallback_to_job_lines_when_step_unknown(self):
        # gh sometimes emits "UNKNOWN STEP" in the step column for short-lived
        # steps. The formatter should fall back to all lines for the failing job
        # rather than render an empty Failed step output section.
        log = (
            "test\tUNKNOWN STEP\tprep work\n"
            "test\tUNKNOWN STEP\tactual error happened here\n"
        )
        out = format_snapshot(_minimal_run(), log, RunRef("octocat", "Hello-World", 123), tail=50)
        assert "Failed step output" in out
        assert "actual error happened here" in out

    def test_fallback_trims_after_last_error_marker(self):
        # When falling back to job-wide lines, post-step cleanup output appears
        # after the failing step's ##[error] marker. Trim it so the relevant
        # error context isn't drowned in cleanup noise.
        log = "\n".join([
            "test\tUNKNOWN STEP\tline before error",
            "test\tUNKNOWN STEP\t##[error]Process completed with exit code 1.",
            "test\tUNKNOWN STEP\tPost job cleanup.",
            "test\tUNKNOWN STEP\tgit config cleanup",
            "test\tUNKNOWN STEP\tCleaning up orphan processes",
        ])
        out = format_snapshot(_minimal_run(), log, RunRef("octocat", "Hello-World", 123), tail=50)
        assert "line before error" in out
        assert "##[error]Process completed" in out
        # Cleanup lines after the error should be excluded
        assert "Post job cleanup" not in out
        assert "Cleaning up orphan processes" not in out

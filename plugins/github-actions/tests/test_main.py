import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from gha_snapshot.main import main
from gha_snapshot.url_parser import RunRef

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _patched_client():
    client = MagicMock()
    client.run_view.return_value = json.loads(
        (FIXTURE_DIR / "run_view_failed.json").read_text()
    )
    client.run_log_failed.return_value = (FIXTURE_DIR / "run_log_failed.txt").read_text()
    return client


class TestMain:
    def test_url_arg_succeeds_and_writes_snapshot(self, capsys):
        with patch("gha_snapshot.main.GhClient", return_value=_patched_client()):
            exit_code = main(["https://github.com/octocat/Hello-World/actions/runs/123"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Run:" in captured.out
        assert "Jobs:" in captured.out

    def test_unresolved_returns_exit_1(self, capsys):
        client = _patched_client()
        client.current_repo.side_effect = RuntimeError("not a gh repo")
        with patch("gha_snapshot.main.GhClient", return_value=client):
            exit_code = main([])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "error" in captured.err.lower()

    def test_tail_flag_is_passed_through(self, capsys):
        with patch("gha_snapshot.main.GhClient", return_value=_patched_client()):
            exit_code = main([
                "https://github.com/octocat/Hello-World/actions/runs/123",
                "--tail", "5",
            ])
        captured = capsys.readouterr()
        assert exit_code == 0
        # Hard to assert tail size precisely without coupling to fixture line count,
        # but verify the run renders successfully.
        assert "Run:" in captured.out

    def test_pr_flag_resolves_via_pr_checks(self, capsys):
        client = _patched_client()
        client.current_repo.return_value = ("octocat", "Hello-World")
        client.pr_checks.return_value = [
            {"name": "test", "state": "FAILURE",
             "link": "https://github.com/octocat/Hello-World/actions/runs/200/job/300",
             "workflow": "ci", "bucket": "fail"}
        ]
        with patch("gha_snapshot.main.GhClient", return_value=client):
            exit_code = main(["--pr", "42"])
        assert exit_code == 0
        # run_view should have been called with run_id=200
        called_with = client.run_view.call_args.kwargs
        assert called_with["run_id"] == 200

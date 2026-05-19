import json
from pathlib import Path
from unittest.mock import patch

import pytest
from gha_snapshot.gh_client import GhClient, GhError

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class TestGhClient:
    def test_run_view_returns_parsed_json(self):
        fixture = (FIXTURE_DIR / "run_view_failed.json").read_text()

        with patch("gha_snapshot.gh_client.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = fixture
            mock_run.return_value.stderr = ""

            client = GhClient()
            result = client.run_view(owner="octocat", repo="Hello-World", run_id=123)

            assert result["databaseId"] == 123 or "databaseId" in result
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "gh"
            assert "run" in args and "view" in args
            assert "--repo" in args
            assert "octocat/Hello-World" in args

    def test_run_view_raises_on_gh_failure(self):
        with patch("gha_snapshot.gh_client.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "could not find any workflow runs"

            client = GhClient()
            with pytest.raises(GhError, match="could not find any workflow runs"):
                client.run_view(owner="octocat", repo="Hello-World", run_id=999)

    def test_run_log_failed_returns_text(self):
        with patch("gha_snapshot.gh_client.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "build\tRun npm test\tFAIL src/foo.test.ts\n"
            mock_run.return_value.stderr = ""

            client = GhClient()
            log = client.run_log_failed(owner="octocat", repo="Hello-World", run_id=123)
            assert "FAIL src/foo.test.ts" in log

    def test_current_repo_returns_owner_and_repo(self):
        with patch("gha_snapshot.gh_client.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"owner":{"login":"octocat"},"name":"Hello-World"}'
            mock_run.return_value.stderr = ""

            client = GhClient()
            owner, repo = client.current_repo()
            assert owner == "octocat"
            assert repo == "Hello-World"

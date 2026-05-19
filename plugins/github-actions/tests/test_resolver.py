import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from gha_snapshot.resolver import resolve, ResolveError
from gha_snapshot.url_parser import RunRef

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _fixture_client(**overrides):
    """Build a mock GhClient with sensible defaults."""
    client = MagicMock()
    client.current_repo.return_value = ("octocat", "Hello-World")
    client.current_branch.return_value = "main"
    client.pr_checks.return_value = json.loads(
        (FIXTURE_DIR / "pr_checks.json").read_text()
    )
    client.run_list_branch.return_value = [
        {"databaseId": 999, "url": "https://github.com/octocat/Hello-World/actions/runs/999"}
    ]
    for key, value in overrides.items():
        getattr(client, key).return_value = value
    return client


class TestResolve:
    def test_full_url(self):
        ref = resolve("https://github.com/octocat/Hello-World/actions/runs/123", client=_fixture_client())
        assert ref == RunRef(owner="octocat", repo="Hello-World", run_id=123)

    def test_bare_run_id_uses_current_repo(self):
        ref = resolve("123", client=_fixture_client())
        assert ref == RunRef(owner="octocat", repo="Hello-World", run_id=123)

    def test_pr_number_picks_most_recent_failure(self):
        ref = resolve(None, pr=42, client=_fixture_client())
        # First FAILURE in fixture is run 200; resolver should pick that.
        assert ref.run_id == 200

    def test_pr_with_no_failures_raises(self):
        client = _fixture_client(pr_checks=[
            {"name": "test", "state": "SUCCESS", "link": "...", "workflow": "ci", "bucket": "pass"}
        ])
        with pytest.raises(ResolveError, match="no failed checks"):
            resolve(None, pr=42, client=client)

    def test_default_uses_latest_failure_on_current_branch(self):
        ref = resolve(None, client=_fixture_client())
        assert ref.run_id == 999

    def test_default_with_no_failed_runs_raises(self):
        client = _fixture_client(run_list_branch=[])
        with pytest.raises(ResolveError, match="no failed runs"):
            resolve(None, client=client)

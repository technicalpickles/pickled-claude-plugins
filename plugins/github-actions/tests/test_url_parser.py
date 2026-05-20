import pytest
from gha_snapshot.url_parser import parse_run_url, RunRef


class TestParseRunUrl:
    def test_canonical_run_url(self):
        ref = parse_run_url("https://github.com/octocat/Hello-World/actions/runs/123456789")
        assert ref == RunRef(owner="octocat", repo="Hello-World", run_id=123456789)

    def test_url_with_trailing_slash(self):
        ref = parse_run_url("https://github.com/octocat/Hello-World/actions/runs/123456789/")
        assert ref.run_id == 123456789

    def test_url_with_job_segment(self):
        ref = parse_run_url("https://github.com/octocat/Hello-World/actions/runs/123456789/job/9876")
        assert ref.run_id == 123456789

    def test_url_with_attempt_segment(self):
        ref = parse_run_url("https://github.com/octocat/Hello-World/actions/runs/123456789/attempts/2")
        assert ref.run_id == 123456789

    def test_repo_with_dots(self):
        ref = parse_run_url("https://github.com/octocat/my.repo/actions/runs/1")
        assert ref.repo == "my.repo"

    def test_non_github_url_raises(self):
        with pytest.raises(ValueError, match="not a GitHub Actions run URL"):
            parse_run_url("https://buildkite.com/foo/bar/builds/1")

    def test_github_url_without_run_id_raises(self):
        with pytest.raises(ValueError, match="not a GitHub Actions run URL"):
            parse_run_url("https://github.com/octocat/Hello-World")

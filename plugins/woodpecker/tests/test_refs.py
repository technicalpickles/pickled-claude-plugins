import pytest

from woodpecker_snapshot import refs


@pytest.mark.parametrize(
    "url,expected",
    [
        ("git@github.com:octocat/hello-world.git", "octocat/hello-world"),
        ("https://github.com/octocat/hello-world.git", "octocat/hello-world"),
        ("https://github.com/octocat/hello-world", "octocat/hello-world"),
        ("ssh://git@codeberg.org/octocat/hello-world.git", "octocat/hello-world"),
        ("https://git.example.com/some/group/octocat/hello-world.git", "octocat/hello-world"),
    ],
)
def test_parse_remote(url, expected):
    assert refs.parse_remote(url) == expected


def test_parse_remote_rejects_garbage():
    assert refs.parse_remote("not-a-remote") is None


def test_parse_pipeline_url_with_step():
    parsed = refs.parse_pipeline_url("https://ci.example.com/repos/7/pipeline/29/5")
    assert (parsed.repo, parsed.number) == ("7", 29)


def test_parse_pipeline_url_without_step():
    parsed = refs.parse_pipeline_url("https://ci.example.com/repos/7/pipeline/29")
    assert (parsed.repo, parsed.number) == ("7", 29)


def test_parse_pipeline_url_non_match():
    assert refs.parse_pipeline_url("https://github.com/o/r/actions/runs/1") is None
    assert refs.parse_pipeline_url("29") is None


def test_sha_matches_full_and_short():
    full = "a1" * 20
    assert refs.sha_matches(full, full)
    assert refs.sha_matches(full, full[:7])
    assert not refs.sha_matches(full, "b2b2b2b")
    assert not refs.sha_matches(full, "")

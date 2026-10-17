import pytest

from woodpecker_snapshot import main as main_mod
from woodpecker_snapshot import refs
from woodpecker_snapshot.cli import WoodpeckerCli

from .helpers import FakeRunner, done, fatal, fixture, route

SHA_FAILED = "b2" * 20  # pipeline 11 in pipeline_ls.tsv


@pytest.fixture(autouse=True)
def git_context(monkeypatch):
    monkeypatch.setattr(refs, "repo_from_git", lambda cwd=None: "o/n")
    monkeypatch.setattr(refs, "head_sha", lambda cwd=None: SHA_FAILED)
    monkeypatch.setattr(refs, "pr_head_sha", lambda pr, cwd=None: SHA_FAILED)


def cli_with(*extra_routes, ls="pipeline_ls.tsv", ps="pipeline_ps_failed.tsv"):
    routes = list(extra_routes) + [
        (route("pipeline", "ls"), done(fixture(ls))),
        (route("pipeline", "ps"), done(fixture(ps))),
        (route("log", "show"), done(fixture("log_failed_ansi.txt"))),
    ]
    runner = FakeRunner(routes)
    return WoodpeckerCli(runner=runner), runner


def test_default_resolves_head_sha_to_its_pipeline(capsys):
    cli, runner = cli_with()
    assert main_mod.main([], client=cli) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "State: failed"
    assert "Pipeline: #11" in out
    assert "AssertionError" in out
    assert ["pipeline", "log", "show", "o/n", "11", "test-web"] in runner.calls


def test_pr_flag_uses_pr_head_sha(capsys, monkeypatch):
    monkeypatch.setattr(refs, "head_sha", lambda cwd=None: "0" * 40)
    cli, _ = cli_with()
    assert main_mod.main(["--pr", "7"], client=cli) == 0
    assert "Pipeline: #11" in capsys.readouterr().out


def test_unmatched_sha_is_no_pipeline_not_a_pass(capsys):
    cli, _ = cli_with()
    assert main_mod.main(["--sha", "f" * 40], client=cli) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "State: no pipeline"
    assert "#12" in out


def test_latest_pipeline_wins_when_a_sha_has_several(capsys):
    rows = "14\tsuccess\t%s\tmain\tpush\n13\tfailure\t%s\tmain\tpush\n" % (SHA_FAILED, SHA_FAILED)
    runner = FakeRunner(
        [
            (route("pipeline", "ls"), done(rows)),
            (route("pipeline", "ps"), done(fixture("pipeline_ps_failed.tsv"))),
        ]
    )
    assert main_mod.main([], client=WoodpeckerCli(runner=runner)) == 0
    out = capsys.readouterr().out
    assert "Pipeline: #14" in out
    assert out.splitlines()[0] == "State: passed"


def test_numeric_ref_is_a_pipeline_number(capsys):
    cli, runner = cli_with(ps="pipeline_ps_ignored.tsv")
    assert main_mod.main(["12"], client=cli) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "State: running"
    assert not any("log" in c for c in runner.calls)  # running: no log fetch


def test_pipeline_url_supplies_repo_id_and_number(capsys):
    cli, runner = cli_with()
    assert main_mod.main(["https://ci.example.com/repos/7/pipeline/29/3"], client=cli) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "State: failed"  # 29 isn't in the list, so state comes from steps
    assert ["pipeline", "ps", "7", "29"] == runner.calls[1][:4]


def test_repo_flag_overrides_git_remote(capsys):
    cli, runner = cli_with()
    main_mod.main(["--repo", "x/y"], client=cli)
    assert runner.calls[0][2] == "x/y"


def test_operational_problem_prints_state_and_exits_2(capsys):
    runner = FakeRunner([(route("pipeline", "ls"), done(stderr=fatal("client error 401: "), returncode=1))])
    assert main_mod.main([], client=WoodpeckerCli(runner=runner)) == 2
    assert capsys.readouterr().out.splitlines()[0] == "State: unauthorized"


def test_no_repo_resolvable_is_an_error(capsys, monkeypatch):
    monkeypatch.setattr(refs, "repo_from_git", lambda cwd=None: None)
    cli, _ = cli_with()
    assert main_mod.main([], client=cli) == 2
    assert "--repo" in capsys.readouterr().err

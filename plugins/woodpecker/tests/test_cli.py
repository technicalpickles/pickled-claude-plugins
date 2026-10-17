import pytest

from woodpecker_snapshot.cli import WoodpeckerCli, WpError, classify_error

from .helpers import FakeRunner, done, fatal, fixture, route


# Messages below were captured from woodpecker-cli 3.19.0 against a live server.
@pytest.mark.parametrize(
    "message,kind",
    [
        ("woodpecker-cli is not configured", WpError.NOT_CONFIGURED),
        ("client error 401: ", WpError.UNAUTHORIZED),
        ("client error 403: ", WpError.UNAUTHORIZED),
        ("client error 404: ", WpError.NOT_FOUND),
        ("client error 502: ", WpError.UNREACHABLE),
        (
            'Get "http://127.0.0.1:9/api/repos/lookup/a/b": dial tcp 127.0.0.1:9: connect: connection refused',
            WpError.UNREACHABLE,
        ),
        # The sandbox's network filter shows up as a bare "Forbidden", with no "client error".
        ('Get "https://ci.example.org/api/repos/lookup/a/b": Forbidden', WpError.NETWORK_DENIED),
        ("something nobody planned for", WpError.OTHER),
    ],
)
def test_classify_error(message, kind):
    assert classify_error(fatal(message)).kind == kind


def test_classify_error_ignores_info_lines():
    stderr = (
        '{"level":"info","message":"woodpecker-cli is not set up, run `woodpecker-cli setup`"}\n'
        + fatal("woodpecker-cli is not configured")
    )
    err = classify_error(stderr)
    assert err.kind == WpError.NOT_CONFIGURED
    assert err.message == "woodpecker-cli is not configured"


def test_classify_error_plain_text_fallback():
    assert classify_error("boom\n").message == "boom"


def test_pipelines_parses_tab_separated_rows():
    runner = FakeRunner([(route("pipeline", "ls"), done(fixture("pipeline_ls.tsv")))])
    pipelines = WoodpeckerCli(runner=runner).pipelines("owner/name", limit=50)
    assert [p.number for p in pipelines] == [12, 11, 10, 9, 8]
    assert pipelines[1].status == "failure"
    assert pipelines[1].commit == "b2" * 20
    assert pipelines[1].branch == "main"
    argv = runner.calls[0]
    assert argv[:4] == ["pipeline", "ls", "owner/name", "--limit"]
    assert "50" in argv
    assert any(a.startswith("go-format=") for a in argv)


def test_pipelines_skips_malformed_lines():
    runner = FakeRunner([(route("ls"), done("not a row\n\n12\trunning\tabc\tmain\tpush\n"))])
    assert [p.number for p in WoodpeckerCli(runner=runner).pipelines("o/n")] == [12]


def test_steps_parse():
    runner = FakeRunner([(route("ps"), done(fixture("pipeline_ps_failed.tsv")))])
    steps = WoodpeckerCli(runner=runner).steps("o/n", 11)
    assert [(s.name, s.state) for s in steps][-1] == ("test-web", "failure")
    assert steps[0].workflow == "woodpecker"
    assert runner.calls[0][:4] == ["pipeline", "ps", "o/n", "11"]


def test_log_passes_step_name_through():
    runner = FakeRunner([(route("log", "show"), done("hello\n"))])
    assert WoodpeckerCli(runner=runner).log("o/n", 11, "test-web") == "hello\n"
    assert runner.calls[0] == ["pipeline", "log", "show", "o/n", "11", "test-web"]


def test_nonzero_exit_raises_classified_error():
    runner = FakeRunner([(route("ls"), done(stderr=fatal("client error 401: "), returncode=1))])
    with pytest.raises(WpError) as exc:
        WoodpeckerCli(runner=runner).pipelines("o/n")
    assert exc.value.kind == WpError.UNAUTHORIZED


def test_missing_binary_is_not_installed():
    runner = FakeRunner([(route("ls"), FileNotFoundError("woodpecker-cli"))])
    with pytest.raises(WpError) as exc:
        WoodpeckerCli(runner=runner).pipelines("o/n")
    assert exc.value.kind == WpError.NOT_INSTALLED

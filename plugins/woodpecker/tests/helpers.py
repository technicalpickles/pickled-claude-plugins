"""Shared test helpers: fixture loading and a fake woodpecker-cli runner."""

from pathlib import Path
from types import SimpleNamespace

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return (FIXTURES / name).read_text()


def done(stdout="", stderr="", returncode=0):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def fatal(message):
    """stderr as woodpecker-cli prints it for a fatal error."""
    return '{"level":"fatal","error":%s,"time":"2026-10-17T00:00:00Z","message":"error running cli"}\n' % (
        __import__("json").dumps(message)
    )


def route(*needles):
    """Match calls whose argv contains every needle."""
    return lambda argv: all(n in argv for n in needles)


class FakeRunner:
    """Stands in for subprocess: answers calls from a list of (matcher, result)."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, argv, cwd):
        self.calls.append(list(argv))
        for matcher, result in self.routes:
            if matcher(argv):
                if isinstance(result, Exception):
                    raise result
                return result
        raise AssertionError("unexpected call: %r" % (argv,))

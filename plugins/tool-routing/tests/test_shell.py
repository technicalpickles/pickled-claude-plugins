import pytest

from tool_routing.checker import check_tool_call
from tool_routing.config import Route
from tool_routing.shell import strip_literals


@pytest.mark.parametrize(
    "command, expected",
    [
        ("git status", "git status"),
        ("echo 'git commit -t x'", "echo ''"),
        ('echo "cargo test | tail"', 'echo ""'),
        ('echo "a \\" b" | wc', 'echo "" | wc'),
        ("printf $'a\\'b' | wc", "printf $'' | wc"),
        ("cat > \"my notes.md\" <<'EOF'\nhello\nEOF", "cat > \"\" <<'EOF'\n"),
        ("tee a <<EOF\nbody\nEOF\nmake | tail", "tee a <<EOF\nmake | tail"),
        ("cat <<-EOF\n\tbody\n\tEOF\nls", "cat <<-EOF\nls"),
        ("cat <<A <<B\na\nA\nb\nB\nls", "cat <<A <<B\nls"),
        ("cat <<\\EOF\nx\nEOF", "cat <<\\EOF\n"),
        ("grep x <<< 'make | tail'", "grep x <<< ''"),
        (
            'git commit -m "$(cat <<\'EOF\'\nfix "it" (now)\nEOF\n)" && git push',
            'git commit -m "" && git push',
        ),
        ("echo $(make | tail) done", "echo $(make | tail) done"),
        ("echo $(echo $((1 + 2)) 'x') y", "echo $(echo $((1 + 2)) '') y"),
        ("echo `make | tail` 'x'", "echo `make | tail` ''"),
        ("echo 'unterminated | tail", "echo ''"),
        ("echo a\\'b", "echo a\\'b"),
    ],
)
def test_strip_literals(command, expected):
    assert strip_literals(command) == expected


def test_bash_route_ignores_heredoc_body_and_quotes():
    routes = {"r": Route(tool="Bash", pattern=r"make\b.*\|\s*tail", message="m")}

    def blocked(command):
        return check_tool_call(
            {"tool_name": "Bash", "tool_input": {"command": command}}, routes
        ).blocked

    assert not blocked("tee notes.md <<'EOF'\nmake 2>&1 | tail\nEOF")
    assert not blocked("git commit -m 'make | tail hides failures'")
    assert blocked("tee notes.md <<'EOF'\nhi\nEOF\nmake 2>&1 | tail")


def test_webfetch_url_is_matched_as_is():
    routes = {"r": Route(tool="WebFetch", pattern=r"x'y", message="m")}
    result = check_tool_call(
        {"tool_name": "WebFetch", "tool_input": {"url": "https://a/x'y'"}}, routes
    )
    assert result.blocked

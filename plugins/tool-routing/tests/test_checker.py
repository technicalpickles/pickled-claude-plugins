from tool_routing.checker import check_tool_call
from tool_routing.config import Route


def test_check_webfetch_matches():
    """WebFetch URL matching route blocks."""
    routes = {
        "github-pr": Route(
            tool="WebFetch",
            pattern=r"github\.com/[^/]+/[^/]+/pull/\d+",
            message="Use gh pr view",
        )
    }

    tool_call = {
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://github.com/foo/bar/pull/123"},
    }

    result = check_tool_call(tool_call, routes)

    assert result.blocked is True
    assert result.route_name == "github-pr"
    assert result.message == "Use gh pr view"


def test_check_webfetch_no_match():
    """WebFetch URL not matching any route allows."""
    routes = {
        "github-pr": Route(
            tool="WebFetch",
            pattern=r"github\.com/[^/]+/[^/]+/pull/\d+",
            message="Use gh pr view",
        )
    }

    tool_call = {
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://example.com/page"},
    }

    result = check_tool_call(tool_call, routes)

    assert result.blocked is False


def test_check_bash_matches():
    """Bash command matching route blocks."""
    routes = {
        "mcp-cli": Route(
            tool="Bash",
            pattern=r"^\s*mcp\s+",
            message="Use MCP tools directly",
        )
    }

    tool_call = {
        "tool_name": "Bash",
        "tool_input": {"command": "mcp list-tools"},
    }

    result = check_tool_call(tool_call, routes)

    assert result.blocked is True
    assert result.route_name == "mcp-cli"


def test_check_unmonitored_tool_allows():
    """Tools not in any route are allowed."""
    routes = {
        "github-pr": Route(
            tool="WebFetch",
            pattern=r"github\.com",
            message="Use gh",
        )
    }

    tool_call = {
        "tool_name": "Read",
        "tool_input": {"file_path": "/some/file"},
    }

    result = check_tool_call(tool_call, routes)

    assert result.blocked is False


def test_check_wrong_tool_type_allows():
    """Route for different tool doesn't match."""
    routes = {
        "github-pr": Route(
            tool="WebFetch",
            pattern=r"github\.com",
            message="Use gh",
        )
    }

    # Bash command containing github.com shouldn't match WebFetch route
    tool_call = {
        "tool_name": "Bash",
        "tool_input": {"command": "curl https://github.com/foo"},
    }

    result = check_tool_call(tool_call, routes)

    assert result.blocked is False

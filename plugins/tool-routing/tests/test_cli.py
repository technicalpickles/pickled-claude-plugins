import json
import subprocess
import sys


def test_cli_check_blocks_matching_route(tmp_path, cli_env):
    """CLI check exits 2 and prints message for matching route."""
    # Create routes file
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  check-blocks-route:
    tool: WebFetch
    pattern: "blocked\\\\.com"
    message: "Don't fetch blocked.com"
""")

    tool_call = json.dumps({
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://blocked.com/page"},
    })

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "check"],
        input=tool_call,
        capture_output=True,
        text=True,
        env=cli_env,
    )

    assert result.returncode == 2
    assert "Don't fetch blocked.com" in result.stderr


def test_cli_check_allows_non_matching(tmp_path, cli_env):
    """CLI check exits 0 for non-matching route."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  check-allows-route:
    tool: WebFetch
    pattern: "blocked\\\\.com"
    message: "Don't fetch blocked.com"
""")

    tool_call = json.dumps({
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://allowed.com/page"},
    })

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "check"],
        input=tool_call,
        capture_output=True,
        text=True,
        env=cli_env,
    )

    assert result.returncode == 0


def test_cli_check_allows_on_missing_config(tmp_path, cli_env):
    """CLI check exits 0 when no config exists (fail open)."""
    tool_call = json.dumps({
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://any.com"},
    })

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "check"],
        input=tool_call,
        capture_output=True,
        text=True,
        env=cli_env,
    )

    assert result.returncode == 0


def test_cli_test_runs_fixtures(tmp_path, cli_env):
    """CLI test runs inline fixtures and reports results."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  fixtures-route:
    tool: WebFetch
    pattern: "blocked\\\\.com"
    message: "Don't fetch blocked.com"
    tests:
      - desc: "blocked URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://blocked.com/page"
        expect: block
      - desc: "other URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://allowed.com"
        expect: allow
""")

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "test"],
        capture_output=True,
        text=True,
        env=cli_env,
    )

    assert result.returncode == 0
    assert "2 passed" in result.stdout or "2 tests passed" in result.stdout


def test_cli_test_reports_failures(tmp_path, cli_env):
    """CLI test reports failing fixtures."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  failures-route:
    tool: WebFetch
    pattern: "blocked\\\\.com"
    message: "Don't fetch"
    tests:
      - desc: "this should fail - expects allow but will block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://blocked.com/page"
        expect: allow
""")

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "test"],
        capture_output=True,
        text=True,
        env=cli_env,
    )

    assert result.returncode == 1
    assert "failed" in result.stdout.lower() or "FAIL" in result.stdout


def test_cli_list_shows_routes(tmp_path, cli_env):
    """CLI list shows all routes with their sources."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  list-route-a:
    tool: WebFetch
    pattern: "a\\\\.com"
    message: "Use A"
  list-route-b:
    tool: Bash
    pattern: "^command-b"
    message: "Use B"
""")

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "list"],
        capture_output=True,
        text=True,
        env=cli_env,
    )

    assert result.returncode == 0
    assert "list-route-a" in result.stdout
    assert "list-route-b" in result.stdout
    assert "WebFetch" in result.stdout
    assert "Bash" in result.stdout


def test_cli_list_with_multiple_route_files(tmp_path):
    """CLI list can load routes from multiple files via TOOL_ROUTING_ROUTES."""
    import os
    from pathlib import Path

    # Create first routes file
    routes_dir1 = tmp_path / "plugin1"
    routes_dir1.mkdir()
    routes_file1 = routes_dir1 / "tool-routes.yaml"
    routes_file1.write_text("""
routes:
  plugin1-route:
    tool: TestTool
    pattern: "plugin1-pattern"
    message: "Route from plugin 1"
""")

    # Create second routes file
    routes_dir2 = tmp_path / "plugin2"
    routes_dir2.mkdir()
    routes_file2 = routes_dir2 / "tool-routes.yaml"
    routes_file2.write_text("""
routes:
  plugin2-route:
    tool: OtherTool
    pattern: "plugin2-pattern"
    message: "Route from plugin 2"
""")

    src_path = Path(__file__).parent.parent / "src"
    env = {
        "PYTHONPATH": str(src_path),
        "PATH": os.environ.get("PATH", ""),
        "TOOL_ROUTING_ROUTES": f"{routes_file1},{routes_file2}",
    }

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "list"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Should find routes from both files
    assert result.returncode == 0
    assert "plugin1-route" in result.stdout
    assert "plugin2-route" in result.stdout
    assert "merged from 2 sources" in result.stdout

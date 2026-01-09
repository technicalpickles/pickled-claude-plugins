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


def test_cli_list_includes_craftdesk_skills(tmp_path, cli_env):
    """CLI list includes routes from craftdesk-installed skills."""
    # Create craftdesk skill with routes
    skill_dir = tmp_path / ".claude" / "skills" / "test-skill" / "hooks"
    skill_dir.mkdir(parents=True)
    (skill_dir / "tool-routes.yaml").write_text("""
routes:
  craftdesk-route:
    tool: TestTool
    pattern: "test-pattern"
    message: "Test tool from craftdesk skill"
""")

    # Add CLAUDE_PROJECT_ROOT for craftdesk discovery (uses project root, not plugin root)
    env = {**cli_env, "CLAUDE_PROJECT_ROOT": str(tmp_path)}

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "list"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Should find the craftdesk skill routes
    assert result.returncode == 0
    assert "craftdesk-route" in result.stdout
    assert "test-skill" in result.stdout or ".claude/skills" in result.stdout

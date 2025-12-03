# Tool Routing Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a standalone `tool-routing` plugin that intercepts tool calls and suggests better alternatives, with support for plugin-contributed routes and project-local configuration.

**Architecture:** Python package with CLI (`tool-routing check/test/list`), YAML config with inline tests, merges routes from multiple plugins plus project `.claude/tool-routes.yaml`.

**Tech Stack:** Python 3.9+, uv, pyyaml, pytest, ruff

---

## Task 1: Create Plugin Skeleton

**Files:**
- Create: `plugins/tool-routing/pyproject.toml`
- Create: `plugins/tool-routing/src/tool_routing/__init__.py`
- Create: `plugins/tool-routing/README.md`

**Step 1: Create directory structure**

```bash
mkdir -p plugins/tool-routing/src/tool_routing
mkdir -p plugins/tool-routing/tests
mkdir -p plugins/tool-routing/hooks
```

**Step 2: Create pyproject.toml**

Create `plugins/tool-routing/pyproject.toml`:

```toml
[project]
name = "tool-routing"
version = "0.1.0"
description = "Claude Code plugin for routing tool calls to better alternatives"
requires-python = ">=3.9"
dependencies = [
    "pyyaml>=6.0",
]

[project.scripts]
tool-routing = "tool_routing.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 3: Create __init__.py**

Create `plugins/tool-routing/src/tool_routing/__init__.py`:

```python
"""Tool routing plugin for Claude Code."""

__version__ = "0.1.0"
```

**Step 4: Create README.md**

Create `plugins/tool-routing/README.md`:

```markdown
# Tool Routing Plugin

Intercepts tool calls and suggests better alternatives.

## Installation

Add to your Claude Code plugins.

## Usage

Routes are configured in `hooks/tool-routes.yaml`. Other plugins can contribute routes by including their own `hooks/tool-routes.yaml`.

Project-specific routes go in `.claude/tool-routes.yaml`.

## CLI

- `tool-routing check` - Hook entry point (reads tool call from stdin)
- `tool-routing test` - Run inline test fixtures
- `tool-routing list` - Show merged routes from all sources
```

**Step 5: Verify uv can see the project**

Run: `cd plugins/tool-routing && uv sync`

Expected: Dependencies installed successfully

**Step 6: Commit**

```bash
git add plugins/tool-routing/
git commit -m "feat(tool-routing): create plugin skeleton with pyproject.toml"
```

---

## Task 2: Implement Config Loading

**Files:**
- Create: `plugins/tool-routing/src/tool_routing/config.py`
- Create: `plugins/tool-routing/tests/test_config.py`

**Step 1: Write failing test for loading single YAML file**

Create `plugins/tool-routing/tests/test_config.py`:

```python
import pytest
from pathlib import Path
from tool_routing.config import load_routes_file, Route


def test_load_routes_file_basic(tmp_path):
    """Load a simple routes file."""
    routes_file = tmp_path / "tool-routes.yaml"
    routes_file.write_text("""
routes:
  test-route:
    tool: WebFetch
    pattern: "example\\\\.com"
    message: "Use something else"
""")

    routes = load_routes_file(routes_file)

    assert len(routes) == 1
    assert "test-route" in routes
    assert routes["test-route"].tool == "WebFetch"
    assert routes["test-route"].pattern == "example\\.com"
    assert routes["test-route"].message == "Use something else"


def test_load_routes_file_not_found(tmp_path):
    """Missing file returns empty dict."""
    routes = load_routes_file(tmp_path / "nonexistent.yaml")
    assert routes == {}


def test_load_routes_file_invalid_yaml(tmp_path):
    """Invalid YAML returns empty dict (fail open)."""
    routes_file = tmp_path / "tool-routes.yaml"
    routes_file.write_text("not: valid: yaml: {{{{")

    routes = load_routes_file(routes_file)
    assert routes == {}
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_config.py -v`

Expected: FAIL with "No module named 'tool_routing.config'"

**Step 3: Implement config loading**

Create `plugins/tool-routing/src/tool_routing/config.py`:

```python
"""Configuration loading and merging for tool routing."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class TestCase:
    """Inline test case for a route."""

    input: dict
    expect: str  # "block" or "allow"
    desc: Optional[str] = None
    contains: Optional[str] = None


@dataclass
class Route:
    """A single routing rule."""

    tool: str
    pattern: str
    message: str
    tests: list[TestCase] = field(default_factory=list)
    source: Optional[str] = None  # File path where route was defined


def load_routes_file(path: Path) -> dict[str, Route]:
    """Load routes from a YAML file.

    Returns empty dict if file doesn't exist or is invalid (fail open).
    """
    if not path.exists():
        return {}

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return {}

    if not data or "routes" not in data:
        return {}

    routes = {}
    for name, route_data in data.get("routes", {}).items():
        tests = []
        for test_data in route_data.get("tests", []):
            tests.append(
                TestCase(
                    input=test_data["input"],
                    expect=test_data["expect"],
                    desc=test_data.get("desc"),
                    contains=test_data.get("contains"),
                )
            )

        routes[name] = Route(
            tool=route_data["tool"],
            pattern=route_data["pattern"],
            message=route_data["message"],
            tests=tests,
            source=str(path),
        )

    return routes
```

**Step 4: Run test to verify it passes**

Run: `cd plugins/tool-routing && uv run pytest tests/test_config.py -v`

Expected: 3 tests PASS

**Step 5: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/config.py plugins/tool-routing/tests/test_config.py
git commit -m "feat(tool-routing): add config loading from YAML files"
```

---

## Task 3: Implement Config Merging

**Files:**
- Modify: `plugins/tool-routing/src/tool_routing/config.py`
- Modify: `plugins/tool-routing/tests/test_config.py`

**Step 1: Write failing test for merging routes**

Add to `plugins/tool-routing/tests/test_config.py`:

```python
from tool_routing.config import merge_routes, RouteConflictError


def test_merge_routes_no_conflict(tmp_path):
    """Merge routes from multiple files without conflicts."""
    file1 = tmp_path / "routes1.yaml"
    file1.write_text("""
routes:
  route-a:
    tool: WebFetch
    pattern: "a\\\\.com"
    message: "Use A"
""")

    file2 = tmp_path / "routes2.yaml"
    file2.write_text("""
routes:
  route-b:
    tool: Bash
    pattern: "^command-b"
    message: "Use B"
""")

    merged = merge_routes([file1, file2])

    assert len(merged) == 2
    assert "route-a" in merged
    assert "route-b" in merged


def test_merge_routes_conflict_raises():
    """Duplicate route names raise RouteConflictError."""
    from tool_routing.config import Route

    routes1 = {"same-name": Route(tool="WebFetch", pattern="a", message="A")}
    routes2 = {"same-name": Route(tool="Bash", pattern="b", message="B")}

    with pytest.raises(RouteConflictError) as exc_info:
        merge_routes_dicts([routes1, routes2], ["file1.yaml", "file2.yaml"])

    assert "same-name" in str(exc_info.value)
    assert "file1.yaml" in str(exc_info.value)
    assert "file2.yaml" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_config.py::test_merge_routes_no_conflict -v`

Expected: FAIL with "cannot import name 'merge_routes'"

**Step 3: Implement merging**

Add to `plugins/tool-routing/src/tool_routing/config.py`:

```python
class RouteConflictError(Exception):
    """Raised when two sources define the same route name."""

    pass


def merge_routes_dicts(
    route_dicts: list[dict[str, Route]], sources: list[str]
) -> dict[str, Route]:
    """Merge multiple route dictionaries, erroring on conflicts.

    Args:
        route_dicts: List of route dictionaries to merge
        sources: List of source file paths (parallel to route_dicts)

    Returns:
        Merged dictionary of routes

    Raises:
        RouteConflictError: If same route name appears in multiple sources
    """
    merged = {}
    route_sources = {}  # Track which source defined each route

    for routes, source in zip(route_dicts, sources):
        for name, route in routes.items():
            if name in merged:
                raise RouteConflictError(
                    f"Route '{name}' defined in multiple sources: "
                    f"'{route_sources[name]}' and '{source}'"
                )
            merged[name] = route
            route.source = source
            route_sources[name] = source

    return merged


def merge_routes(paths: list[Path]) -> dict[str, Route]:
    """Load and merge routes from multiple YAML files.

    Args:
        paths: List of paths to tool-routes.yaml files

    Returns:
        Merged dictionary of routes

    Raises:
        RouteConflictError: If same route name appears in multiple files
    """
    route_dicts = []
    sources = []

    for path in paths:
        routes = load_routes_file(path)
        if routes:
            route_dicts.append(routes)
            sources.append(str(path))

    return merge_routes_dicts(route_dicts, sources)
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/tool-routing && uv run pytest tests/test_config.py -v`

Expected: 5 tests PASS

**Step 5: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/config.py plugins/tool-routing/tests/test_config.py
git commit -m "feat(tool-routing): add route merging with conflict detection"
```

---

## Task 4: Implement Route Discovery

**Files:**
- Modify: `plugins/tool-routing/src/tool_routing/config.py`
- Modify: `plugins/tool-routing/tests/test_config.py`

**Step 1: Write failing test for discovering routes**

Add to `plugins/tool-routing/tests/test_config.py`:

```python
import os


def test_discover_routes_from_plugins(tmp_path, monkeypatch):
    """Discover tool-routes.yaml from plugin directories."""
    # Create fake plugin structure
    plugin1 = tmp_path / "plugins" / "plugin-a" / "hooks"
    plugin1.mkdir(parents=True)
    (plugin1 / "tool-routes.yaml").write_text("""
routes:
  from-plugin-a:
    tool: WebFetch
    pattern: "plugin-a"
    message: "From A"
""")

    plugin2 = tmp_path / "plugins" / "plugin-b" / "hooks"
    plugin2.mkdir(parents=True)
    (plugin2 / "tool-routes.yaml").write_text("""
routes:
  from-plugin-b:
    tool: Bash
    pattern: "plugin-b"
    message: "From B"
""")

    # Plugin without routes
    plugin3 = tmp_path / "plugins" / "plugin-c"
    plugin3.mkdir(parents=True)

    paths = discover_plugin_routes(tmp_path / "plugins")

    assert len(paths) == 2
    assert any("plugin-a" in str(p) for p in paths)
    assert any("plugin-b" in str(p) for p in paths)


def test_discover_project_routes(tmp_path):
    """Discover project-local tool-routes.yaml."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "tool-routes.yaml").write_text("""
routes:
  project-route:
    tool: WebFetch
    pattern: "project"
    message: "Project route"
""")

    path = discover_project_routes(tmp_path)

    assert path is not None
    assert ".claude" in str(path)


def test_discover_project_routes_missing(tmp_path):
    """No project routes returns None."""
    path = discover_project_routes(tmp_path)
    assert path is None
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_config.py::test_discover_routes_from_plugins -v`

Expected: FAIL with "cannot import name 'discover_plugin_routes'"

**Step 3: Implement discovery**

Add to `plugins/tool-routing/src/tool_routing/config.py`:

```python
def discover_plugin_routes(plugins_dir: Path) -> list[Path]:
    """Find all tool-routes.yaml files in plugin directories.

    Args:
        plugins_dir: Path to plugins directory

    Returns:
        List of paths to tool-routes.yaml files
    """
    if not plugins_dir.exists():
        return []

    paths = []
    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        routes_file = plugin_dir / "hooks" / "tool-routes.yaml"
        if routes_file.exists():
            paths.append(routes_file)

    return sorted(paths)  # Consistent ordering


def discover_project_routes(project_root: Path) -> Optional[Path]:
    """Find project-local tool-routes.yaml.

    Args:
        project_root: Path to project root

    Returns:
        Path to .claude/tool-routes.yaml if it exists, None otherwise
    """
    routes_file = project_root / ".claude" / "tool-routes.yaml"
    if routes_file.exists():
        return routes_file
    return None


def load_all_routes(plugins_dir: Path, project_root: Path) -> dict[str, Route]:
    """Load and merge routes from all sources.

    Order:
    1. Plugin-contributed routes (from plugins_dir/*/hooks/tool-routes.yaml)
    2. Project-local routes (from project_root/.claude/tool-routes.yaml)

    Args:
        plugins_dir: Path to plugins directory
        project_root: Path to project root

    Returns:
        Merged dictionary of all routes

    Raises:
        RouteConflictError: If same route name appears in multiple sources
    """
    paths = discover_plugin_routes(plugins_dir)

    project_routes = discover_project_routes(project_root)
    if project_routes:
        paths.append(project_routes)

    return merge_routes(paths)
```

**Step 4: Update imports in test file**

Add to imports at top of `plugins/tool-routing/tests/test_config.py`:

```python
from tool_routing.config import (
    load_routes_file,
    Route,
    merge_routes,
    merge_routes_dicts,
    RouteConflictError,
    discover_plugin_routes,
    discover_project_routes,
)
```

**Step 5: Run tests to verify they pass**

Run: `cd plugins/tool-routing && uv run pytest tests/test_config.py -v`

Expected: 8 tests PASS

**Step 6: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/config.py plugins/tool-routing/tests/test_config.py
git commit -m "feat(tool-routing): add route discovery from plugins and project"
```

---

## Task 5: Implement Pattern Matching (Checker)

**Files:**
- Create: `plugins/tool-routing/src/tool_routing/checker.py`
- Create: `plugins/tool-routing/tests/test_checker.py`

**Step 1: Write failing test for pattern matching**

Create `plugins/tool-routing/tests/test_checker.py`:

```python
import pytest
from tool_routing.checker import check_tool_call, CheckResult
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
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_checker.py -v`

Expected: FAIL with "No module named 'tool_routing.checker'"

**Step 3: Implement checker**

Create `plugins/tool-routing/src/tool_routing/checker.py`:

```python
"""Pattern matching for tool calls against routes."""

import re
from dataclasses import dataclass
from typing import Optional

from tool_routing.config import Route


# Maps tool name to the field in tool_input to match against
TOOL_INPUT_FIELDS = {
    "WebFetch": "url",
    "Bash": "command",
}


@dataclass
class CheckResult:
    """Result of checking a tool call against routes."""

    blocked: bool
    route_name: Optional[str] = None
    message: Optional[str] = None
    matched_value: Optional[str] = None
    pattern: Optional[str] = None


def check_tool_call(tool_call: dict, routes: dict[str, Route]) -> CheckResult:
    """Check a tool call against all routes.

    Args:
        tool_call: Dict with tool_name and tool_input
        routes: Dictionary of routes to check against

    Returns:
        CheckResult indicating if blocked and why
    """
    tool_name = tool_call.get("tool_name", "")
    tool_input = tool_call.get("tool_input", {})

    # Get the field to match for this tool type
    input_field = TOOL_INPUT_FIELDS.get(tool_name)
    if not input_field:
        # Tool type not monitored
        return CheckResult(blocked=False)

    value = tool_input.get(input_field, "")
    if not value:
        return CheckResult(blocked=False)

    # Check against each route
    for route_name, route in routes.items():
        # Only check routes for this tool type
        if route.tool != tool_name:
            continue

        try:
            if re.search(route.pattern, value, re.IGNORECASE):
                return CheckResult(
                    blocked=True,
                    route_name=route_name,
                    message=route.message,
                    matched_value=value,
                    pattern=route.pattern,
                )
        except re.error:
            # Invalid regex - skip this route (fail open)
            continue

    return CheckResult(blocked=False)
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/tool-routing && uv run pytest tests/test_checker.py -v`

Expected: 5 tests PASS

**Step 5: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/checker.py plugins/tool-routing/tests/test_checker.py
git commit -m "feat(tool-routing): add pattern matching checker"
```

---

## Task 6: Implement CLI - Check Subcommand

**Files:**
- Create: `plugins/tool-routing/src/tool_routing/cli.py`
- Create: `plugins/tool-routing/tests/test_cli.py`

**Step 1: Write failing test for check subcommand**

Create `plugins/tool-routing/tests/test_cli.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_cli_check_blocks_matching_route(tmp_path):
    """CLI check exits 2 and prints message for matching route."""
    # Create routes file
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  test-route:
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
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "PATH": "",
        },
    )

    assert result.returncode == 2
    assert "Don't fetch blocked.com" in result.stderr


def test_cli_check_allows_non_matching(tmp_path):
    """CLI check exits 0 for non-matching route."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  test-route:
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
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "PATH": "",
        },
    )

    assert result.returncode == 0


def test_cli_check_allows_on_missing_config(tmp_path):
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
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "PATH": "",
        },
    )

    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_cli.py::test_cli_check_blocks_matching_route -v`

Expected: FAIL with "No module named tool_routing.__main__" or similar

**Step 3: Implement CLI**

Create `plugins/tool-routing/src/tool_routing/cli.py`:

```python
"""Command-line interface for tool-routing."""

import argparse
import json
import os
import sys
from pathlib import Path

from tool_routing.checker import check_tool_call
from tool_routing.config import load_routes_file, RouteConflictError


DEBUG = os.environ.get("TOOL_ROUTING_DEBUG", "").lower() in ("1", "true", "yes")


def get_plugin_root() -> Path:
    """Get plugin root from environment."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        return Path(plugin_root)
    return Path.cwd()


def cmd_check(args: argparse.Namespace) -> int:
    """Check a tool call against routes (hook entry point)."""
    plugin_root = get_plugin_root()

    # Load routes from plugin's hooks directory
    routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    routes = load_routes_file(routes_file)

    if not routes:
        # No routes configured, allow
        return 0

    # Read tool call from stdin
    try:
        raw_input = sys.stdin.read()
        tool_call = json.loads(raw_input)
    except json.JSONDecodeError:
        # Invalid input, fail open
        return 0

    # Check against routes
    result = check_tool_call(tool_call, routes)

    if result.blocked:
        if DEBUG:
            print(f"❌ Tool Routing: {result.route_name}", file=sys.stderr)
            if result.matched_value:
                display = result.matched_value
                if len(display) > 200:
                    display = display[:200] + "..."
                print(f"Matched: {display}", file=sys.stderr)
            print(f"Pattern: {result.pattern}", file=sys.stderr)
            print("", file=sys.stderr)
        print(result.message, file=sys.stderr)
        return 2

    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run inline test fixtures."""
    # TODO: Implement in Task 7
    print("test command not yet implemented", file=sys.stderr)
    return 1


def cmd_list(args: argparse.Namespace) -> int:
    """List merged routes."""
    # TODO: Implement in Task 8
    print("list command not yet implemented", file=sys.stderr)
    return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="tool-routing",
        description="Route tool calls to better alternatives",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check subcommand
    check_parser = subparsers.add_parser(
        "check",
        help="Check a tool call against routes (hook entry point)",
    )
    check_parser.set_defaults(func=cmd_check)

    # test subcommand
    test_parser = subparsers.add_parser(
        "test",
        help="Run inline test fixtures",
    )
    test_parser.set_defaults(func=cmd_test)

    # list subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="List merged routes from all sources",
    )
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Create __main__.py for -m invocation**

Create `plugins/tool-routing/src/tool_routing/__main__.py`:

```python
"""Allow running as python -m tool_routing."""

from tool_routing.cli import main
import sys

sys.exit(main())
```

**Step 5: Run tests to verify they pass**

Run: `cd plugins/tool-routing && uv run pytest tests/test_cli.py -v`

Expected: 3 tests PASS

**Step 6: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/cli.py plugins/tool-routing/src/tool_routing/__main__.py plugins/tool-routing/tests/test_cli.py
git commit -m "feat(tool-routing): add CLI with check subcommand"
```

---

## Task 7: Implement CLI - Test Subcommand

**Files:**
- Create: `plugins/tool-routing/src/tool_routing/test_runner.py`
- Modify: `plugins/tool-routing/src/tool_routing/cli.py`
- Modify: `plugins/tool-routing/tests/test_cli.py`

**Step 1: Write failing test for test subcommand**

Add to `plugins/tool-routing/tests/test_cli.py`:

```python
def test_cli_test_runs_fixtures(tmp_path):
    """CLI test runs inline fixtures and reports results."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  test-route:
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
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "PATH": "",
        },
    )

    assert result.returncode == 0
    assert "2 passed" in result.stdout or "2 tests passed" in result.stdout


def test_cli_test_reports_failures(tmp_path):
    """CLI test reports failing fixtures."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  test-route:
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
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "PATH": "",
        },
    )

    assert result.returncode == 1
    assert "failed" in result.stdout.lower() or "FAIL" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_cli.py::test_cli_test_runs_fixtures -v`

Expected: FAIL (returns 1, "not yet implemented")

**Step 3: Implement test runner**

Create `plugins/tool-routing/src/tool_routing/test_runner.py`:

```python
"""Test runner for inline route fixtures."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tool_routing.checker import check_tool_call
from tool_routing.config import Route, load_routes_file


@dataclass
class TestResult:
    """Result of running a single test."""

    route_name: str
    desc: str
    passed: bool
    expected: str
    actual: str
    contains_error: Optional[str] = None  # If contains check failed


def run_route_tests(routes: dict[str, Route]) -> list[TestResult]:
    """Run all inline tests for routes.

    Args:
        routes: Dictionary of routes with inline tests

    Returns:
        List of test results
    """
    results = []

    for route_name, route in routes.items():
        for test in route.tests:
            # Run the check
            check_result = check_tool_call(test.input, routes)

            # Determine actual result
            actual = "block" if check_result.blocked else "allow"
            passed = actual == test.expect

            # Check contains if specified and test passed so far
            contains_error = None
            if passed and test.contains and check_result.blocked:
                if test.contains not in (check_result.message or ""):
                    passed = False
                    contains_error = (
                        f"Expected message to contain '{test.contains}'"
                    )

            results.append(
                TestResult(
                    route_name=route_name,
                    desc=test.desc or f"test {len(results) + 1}",
                    passed=passed,
                    expected=test.expect,
                    actual=actual,
                    contains_error=contains_error,
                )
            )

    return results


def format_results(results: list[TestResult], source: str) -> str:
    """Format test results for display.

    Args:
        results: List of test results
        source: Source file path

    Returns:
        Formatted string for display
    """
    lines = [source]

    for result in results:
        status = "✓" if result.passed else "✗"
        lines.append(f"  {status} {result.route_name}: {result.desc}")
        if not result.passed:
            if result.contains_error:
                lines.append(f"      {result.contains_error}")
            else:
                lines.append(
                    f"      Expected: {result.expected}, Got: {result.actual}"
                )

    return "\n".join(lines)
```

**Step 4: Update CLI to use test runner**

Update `cmd_test` in `plugins/tool-routing/src/tool_routing/cli.py`:

```python
def cmd_test(args: argparse.Namespace) -> int:
    """Run inline test fixtures."""
    from tool_routing.test_runner import run_route_tests, format_results

    plugin_root = get_plugin_root()

    # Load routes from plugin's hooks directory
    routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    routes = load_routes_file(routes_file)

    if not routes:
        print("No routes found", file=sys.stderr)
        return 1

    # Count tests
    total_tests = sum(len(r.tests) for r in routes.values())
    if total_tests == 0:
        print("No tests found in routes")
        return 0

    # Run tests
    results = run_route_tests(routes)

    # Format and print results
    print(format_results(results, str(routes_file)))
    print()

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"{passed} passed, {failed} failed")

    return 0 if failed == 0 else 1
```

**Step 5: Run tests to verify they pass**

Run: `cd plugins/tool-routing && uv run pytest tests/test_cli.py -v`

Expected: 5 tests PASS

**Step 6: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/test_runner.py plugins/tool-routing/src/tool_routing/cli.py plugins/tool-routing/tests/test_cli.py
git commit -m "feat(tool-routing): add test subcommand for inline fixtures"
```

---

## Task 8: Implement CLI - List Subcommand

**Files:**
- Modify: `plugins/tool-routing/src/tool_routing/cli.py`
- Modify: `plugins/tool-routing/tests/test_cli.py`

**Step 1: Write failing test for list subcommand**

Add to `plugins/tool-routing/tests/test_cli.py`:

```python
def test_cli_list_shows_routes(tmp_path):
    """CLI list shows all routes with their sources."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  route-a:
    tool: WebFetch
    pattern: "a\\\\.com"
    message: "Use A"
  route-b:
    tool: Bash
    pattern: "^command-b"
    message: "Use B"
""")

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "list"],
        capture_output=True,
        text=True,
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "PATH": "",
        },
    )

    assert result.returncode == 0
    assert "route-a" in result.stdout
    assert "route-b" in result.stdout
    assert "WebFetch" in result.stdout
    assert "Bash" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_cli.py::test_cli_list_shows_routes -v`

Expected: FAIL (returns 1, "not yet implemented")

**Step 3: Implement list command**

Update `cmd_list` in `plugins/tool-routing/src/tool_routing/cli.py`:

```python
def cmd_list(args: argparse.Namespace) -> int:
    """List merged routes."""
    plugin_root = get_plugin_root()

    # Load routes from plugin's hooks directory
    routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    routes = load_routes_file(routes_file)

    if not routes:
        print("No routes found")
        return 0

    print(f"Routes (from {routes_file}):\n")

    for name, route in routes.items():
        print(f"{name}")
        print(f"  tool: {route.tool}")
        print(f"  pattern: {route.pattern}")
        if route.tests:
            print(f"  tests: {len(route.tests)}")
        print()

    return 0
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/tool-routing && uv run pytest tests/test_cli.py -v`

Expected: 6 tests PASS

**Step 5: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/cli.py plugins/tool-routing/tests/test_cli.py
git commit -m "feat(tool-routing): add list subcommand"
```

---

## Task 9: Create Hook Registration

**Files:**
- Create: `plugins/tool-routing/hooks/hooks.json`
- Create: `plugins/tool-routing/hooks/tool-routes.yaml`

**Step 1: Create hooks.json**

Create `plugins/tool-routing/hooks/hooks.json`:

```json
{
  "hooks": [
    {
      "matcher": {
        "tool_name": "WebFetch"
      },
      "hooks": [
        {
          "type": "preToolUse",
          "command": "uv run --project $CLAUDE_PLUGIN_ROOT tool-routing check"
        }
      ]
    },
    {
      "matcher": {
        "tool_name": "Bash"
      },
      "hooks": [
        {
          "type": "preToolUse",
          "command": "uv run --project $CLAUDE_PLUGIN_ROOT tool-routing check"
        }
      ]
    }
  ]
}
```

**Step 2: Create default routes file**

Create `plugins/tool-routing/hooks/tool-routes.yaml`:

```yaml
# Default tool routes shipped with the plugin.
# Other plugins can contribute routes via their own hooks/tool-routes.yaml.
# Project-specific routes go in .claude/tool-routes.yaml.

routes:
  # GitHub PRs - use gh CLI instead of scraping
  github-pr:
    tool: WebFetch
    pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"
    message: |
      Use `gh pr view <number>` for GitHub PRs.

      This works for both public and private PRs and
      provides better formatting than HTML scraping.
    tests:
      - desc: "PR URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar/pull/123"
        expect: block
        contains: "gh pr view"
      - desc: "repo URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar"
        expect: allow
      - desc: "issues URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar/issues/123"
        expect: allow

  # Atlassian - use MCP tools
  atlassian:
    tool: WebFetch
    pattern: "https?://[^/]*\\.atlassian\\.net"
    message: |
      Use Atlassian MCP tools for Jira/Confluence.

      Call: mcp__MCPProxy__retrieve_tools
      Query: 'jira confluence atlassian issue'

      MCP tools provide authentication and structured data.
    tests:
      - desc: "Jira URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://mycompany.atlassian.net/browse/PROJ-123"
        expect: block
      - desc: "Confluence URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://mycompany.atlassian.net/wiki/spaces/DOC/pages/123"
        expect: block

  # Prevent calling nonexistent mcp CLI via Bash
  bash-mcp-cli:
    tool: Bash
    pattern: "^\\s*mcp\\s+"
    message: |
      Don't use Bash to call the 'mcp' CLI.

      The 'mcp' command is not available. Use MCP tools directly:

      1. Discover tools: mcp__MCPProxy__retrieve_tools
      2. Call a tool: mcp__MCPProxy__call_tool

      Example:
      mcp__MCPProxy__retrieve_tools(query="buildkite build status")
      mcp__MCPProxy__call_tool(name="buildkite:get_build", args_json=...)
    tests:
      - desc: "mcp list-tools should block"
        input:
          tool_name: Bash
          tool_input:
            command: "mcp list-tools"
        expect: block
      - desc: "mcp search should block"
        input:
          tool_name: Bash
          tool_input:
            command: "  mcp search foo"
        expect: block

  # Prevent calling MCP tool names as Bash commands
  bash-mcp-tool:
    tool: Bash
    pattern: "^\\s*mcp__"
    message: |
      Don't use Bash to call MCP tool functions.

      MCP tools like 'mcp__MCPProxy__retrieve_tools' are tool calls, not Bash commands.

      Use the tool directly:
      - mcp__MCPProxy__retrieve_tools (tool call)
      - mcp__MCPProxy__call_tool (tool call)

      NOT as Bash commands.
    tests:
      - desc: "mcp__MCPProxy should block"
        input:
          tool_name: Bash
          tool_input:
            command: "mcp__MCPProxy__retrieve_tools"
        expect: block
```

**Step 3: Test that routes load correctly**

Run: `cd plugins/tool-routing && uv run tool-routing list`

Expected: Shows all routes defined above

**Step 4: Test that inline tests pass**

Run: `cd plugins/tool-routing && uv run tool-routing test`

Expected: All tests pass

**Step 5: Commit**

```bash
git add plugins/tool-routing/hooks/
git commit -m "feat(tool-routing): add hook registration and default routes"
```

---

## Task 10: Migrate Additional Routes from dev-tools

**Files:**
- Modify: `plugins/tool-routing/hooks/tool-routes.yaml`

**Step 1: Add remaining routes from dev-tools**

Add to `plugins/tool-routing/hooks/tool-routes.yaml`:

```yaml
  # Buildkite - use MCP tools
  buildkite:
    tool: WebFetch
    pattern: "https?://buildkite\\.com/[^/]+/[^/]+/builds/\\d+"
    message: |
      Use Buildkite MCP tools for build information.

      Call: mcp__MCPProxy__retrieve_tools
      Query: 'buildkite build status pipeline'

      MCP tools provide authentication and structured build data.
    tests:
      - desc: "build URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://buildkite.com/myorg/mypipeline/builds/123"
        expect: block
      - desc: "pipeline URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://buildkite.com/myorg/mypipeline"
        expect: allow

  # Git commit - use Write + -F for multiline
  git-commit-multiline:
    tool: Bash
    pattern: "git\\s+commit\\s+.*(?:(?:-m\\s+[\"'][^\"']*[\"'].*-m)|(?:\\$\\(cat\\s*<<)|(?:<<[-]?\\s*['\"]?\\w+['\"]?))"
    message: |
      Don't use multiple -m flags or heredocs for git commit messages.

      For multiline commit messages:
        1. Use Write tool to create a commit message file in .tmp/
        2. Use git commit -F <file> to read from the file

      Example:
        Write(file_path=".tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt", content="Title\n\nBody")
        git commit -F .tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt
    tests:
      - desc: "multiple -m flags should block"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"Title\" -m \"Body\""
        expect: block
      - desc: "heredoc should block"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"$(cat <<'EOF'\nTitle\nEOF\n)\""
        expect: block
      - desc: "single -m should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"Simple message\""
        expect: allow
      - desc: "-F with file should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -F .tmp/commit-msg.txt"
        expect: allow

  # gh pr create - use Write + --body-file for multiline
  gh-pr-create-multiline:
    tool: Bash
    pattern: "gh\\s+pr\\s+create\\s+.*(?:(?:--body\\s+[\"']\\$\\(cat\\s*<<)|(?:<<[-]?\\s*['\"]?\\w+['\"]?))"
    message: |
      Don't use heredocs or command substitution for gh pr create body.

      For multiline PR descriptions:
        1. Use Write tool to create a PR body file in .tmp/
        2. Use gh pr create --body-file <file>

      Example:
        Write(file_path=".tmp/pr-body-YYYY-MM-DD-HHMMSS.md", content="## Summary\n...")
        gh pr create --title "Title" --body-file .tmp/pr-body-YYYY-MM-DD-HHMMSS.md
    tests:
      - desc: "heredoc body should block"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr create --title \"Title\" --body \"$(cat <<'EOF'\n## Summary\nEOF\n)\""
        expect: block
      - desc: "--body-file should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr create --title \"Title\" --body-file .tmp/pr-body.md"
        expect: allow
      - desc: "simple --body should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr create --title \"Title\" --body \"Simple description\""
        expect: allow

  # cat heredoc - use Write tool instead
  bash-cat-heredoc:
    tool: Bash
    pattern: "cat\\s+.*<<[-]?\\s*['\"]?\\w+['\"]?(?!.*\\|)"
    message: |
      Don't use cat with heredocs for file creation or display.

      For writing to files:
        Use the Write tool instead of cat with redirection.
        Example: Write(file_path="/path/to/file", content="...")

      For displaying text to the user:
        Output text directly in your response.
        Don't use cat or echo - just write the text.

      Valid heredoc use:
        Only use cat <<EOF when piping to another command:
        cat <<EOF | jq .
    tests:
      - desc: "cat heredoc to file should block"
        input:
          tool_name: Bash
          tool_input:
            command: "cat > file.txt << 'EOF'\nHello\nEOF"
        expect: block
      - desc: "cat heredoc with pipe should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "cat <<EOF | jq .\n{\"key\": \"value\"}\nEOF"
        expect: allow

  # chained echo - output directly instead
  bash-echo-chained:
    tool: Bash
    pattern: "echo\\s+[\"'].*&&\\s+echo.*&&\\s+echo"
    message: |
      Don't use chained echo commands for multi-line output.

      For displaying information to the user:
        Output text directly in your response.
        Don't use echo with && chains - just write the text.

      The echo command should only be used for:
        - Single simple outputs in legitimate shell operations
        - Testing or debugging actual shell behavior
    tests:
      - desc: "triple echo chain should block"
        input:
          tool_name: Bash
          tool_input:
            command: "echo \"=== SUMMARY ===\" && echo \"\" && echo \"Done\""
        expect: block
      - desc: "single echo should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "echo 'test'"
        expect: allow

  # echo redirect - use Write tool instead
  bash-echo-redirect:
    tool: Bash
    pattern: "^echo\\s+[\\s\\S]*>\\s*/"
    message: |
      Don't use echo with file redirection to write files.

      Use Write tool instead:
        Write(file_path="/path/to/file", content="...")

      The echo command should only be used for:
        - Displaying output to stdout in legitimate shell operations
        - Testing or debugging actual shell behavior
    tests:
      - desc: "echo redirect to absolute path should block"
        input:
          tool_name: Bash
          tool_input:
            command: "echo 'content' > /tmp/file.txt"
        expect: block
      - desc: "echo to stdout should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "echo 'hello'"
        expect: allow
```

**Step 2: Run tests to verify all routes work**

Run: `cd plugins/tool-routing && uv run tool-routing test`

Expected: All tests pass

**Step 3: Commit**

```bash
git add plugins/tool-routing/hooks/tool-routes.yaml
git commit -m "feat(tool-routing): migrate routes from dev-tools"
```

---

## Task 11: Add Full Route Discovery (Multi-Plugin Support)

**Files:**
- Modify: `plugins/tool-routing/src/tool_routing/cli.py`
- Create: `plugins/tool-routing/tests/test_discovery.py`

**Step 1: Write test for multi-source discovery**

Create `plugins/tool-routing/tests/test_discovery.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_cli_merges_multiple_sources(tmp_path):
    """CLI merges routes from plugin and project sources."""
    # Plugin routes
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "tool-routes.yaml").write_text("""
routes:
  plugin-route:
    tool: WebFetch
    pattern: "plugin\\\\.com"
    message: "From plugin"
""")

    # Simulate another plugin's routes
    other_plugin = tmp_path / "other-plugins" / "other" / "hooks"
    other_plugin.mkdir(parents=True)
    (other_plugin / "tool-routes.yaml").write_text("""
routes:
  other-plugin-route:
    tool: Bash
    pattern: "^other-command"
    message: "From other plugin"
""")

    # Project routes
    claude_dir = tmp_path / "project" / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "tool-routes.yaml").write_text("""
routes:
  project-route:
    tool: WebFetch
    pattern: "project\\\\.com"
    message: "From project"
""")

    result = subprocess.run(
        [sys.executable, "-m", "tool_routing", "list"],
        capture_output=True,
        text=True,
        env={
            "CLAUDE_PLUGIN_ROOT": str(tmp_path),
            "CLAUDE_PLUGINS_DIR": str(tmp_path / "other-plugins"),
            "CLAUDE_PROJECT_ROOT": str(tmp_path / "project"),
            "PATH": "",
        },
    )

    assert result.returncode == 0
    assert "plugin-route" in result.stdout
    assert "other-plugin-route" in result.stdout
    assert "project-route" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_discovery.py -v`

Expected: FAIL (only shows plugin-route, not others)

**Step 3: Update CLI to use full discovery**

Update `plugins/tool-routing/src/tool_routing/cli.py`:

Add helper function:

```python
def get_all_routes() -> tuple[dict[str, "Route"], list[str]]:
    """Load routes from all sources.

    Returns:
        Tuple of (merged routes dict, list of source files)
    """
    from tool_routing.config import (
        load_routes_file,
        merge_routes_dicts,
        discover_plugin_routes,
        discover_project_routes,
        RouteConflictError,
    )

    plugin_root = get_plugin_root()
    plugins_dir = Path(os.environ.get("CLAUDE_PLUGINS_DIR", ""))
    project_root = Path(os.environ.get("CLAUDE_PROJECT_ROOT", Path.cwd()))

    all_routes = []
    all_sources = []

    # 1. This plugin's routes
    own_routes_file = plugin_root / "hooks" / "tool-routes.yaml"
    if own_routes_file.exists():
        routes = load_routes_file(own_routes_file)
        if routes:
            all_routes.append(routes)
            all_sources.append(str(own_routes_file))

    # 2. Other plugins' routes
    if plugins_dir.exists():
        for path in discover_plugin_routes(plugins_dir):
            # Skip our own routes (already loaded)
            if path == own_routes_file:
                continue
            routes = load_routes_file(path)
            if routes:
                all_routes.append(routes)
                all_sources.append(str(path))

    # 3. Project routes
    project_routes_path = discover_project_routes(project_root)
    if project_routes_path:
        routes = load_routes_file(project_routes_path)
        if routes:
            all_routes.append(routes)
            all_sources.append(str(project_routes_path))

    if not all_routes:
        return {}, []

    merged = merge_routes_dicts(all_routes, all_sources)
    return merged, all_sources
```

Update `cmd_check`:

```python
def cmd_check(args: argparse.Namespace) -> int:
    """Check a tool call against routes (hook entry point)."""
    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 0  # Fail open

    if not routes:
        return 0

    # Read tool call from stdin
    try:
        raw_input = sys.stdin.read()
        tool_call = json.loads(raw_input)
    except json.JSONDecodeError:
        return 0

    result = check_tool_call(tool_call, routes)

    if result.blocked:
        if DEBUG:
            print(f"❌ Tool Routing: {result.route_name}", file=sys.stderr)
            if result.matched_value:
                display = result.matched_value
                if len(display) > 200:
                    display = display[:200] + "..."
                print(f"Matched: {display}", file=sys.stderr)
            print(f"Pattern: {result.pattern}", file=sys.stderr)
            print("", file=sys.stderr)
        print(result.message, file=sys.stderr)
        return 2

    return 0
```

Update `cmd_list`:

```python
def cmd_list(args: argparse.Namespace) -> int:
    """List merged routes."""
    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    if not routes:
        print("No routes found")
        return 0

    print(f"Routes (merged from {len(sources)} sources):\n")

    for name, route in routes.items():
        print(f"{name} (from: {route.source})")
        print(f"  tool: {route.tool}")
        print(f"  pattern: {route.pattern}")
        if route.tests:
            print(f"  tests: {len(route.tests)}")
        print()

    return 0
```

Update `cmd_test`:

```python
def cmd_test(args: argparse.Namespace) -> int:
    """Run inline test fixtures."""
    from tool_routing.test_runner import run_route_tests, format_results

    try:
        routes, sources = get_all_routes()
    except RouteConflictError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    if not routes:
        print("No routes found", file=sys.stderr)
        return 1

    total_tests = sum(len(r.tests) for r in routes.values())
    if total_tests == 0:
        print("No tests found in routes")
        return 0

    results = run_route_tests(routes)

    # Group results by source
    by_source = {}
    for result in results:
        route = routes[result.route_name]
        source = route.source or "unknown"
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(result)

    # Print grouped results
    for source, source_results in by_source.items():
        print(format_results(source_results, source))
        print()

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    print(f"{passed} passed, {failed} failed")

    return 0 if failed == 0 else 1
```

Add import at top:

```python
from tool_routing.config import RouteConflictError
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/tool-routing && uv run pytest tests/ -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/cli.py plugins/tool-routing/tests/test_discovery.py
git commit -m "feat(tool-routing): add multi-source route discovery"
```

---

## Task 12: Remove Tool Routing from dev-tools

**Files:**
- Delete: `plugins/dev-tools/hooks/check_tool_routing.py`
- Delete: `plugins/dev-tools/hooks/test_tool_routing.py`
- Delete: `plugins/dev-tools/hooks/tool-routes.json`
- Delete: `plugins/dev-tools/hooks/run_fixture.sh`
- Delete: `plugins/dev-tools/hooks/fixtures/` (entire directory)
- Modify: `plugins/dev-tools/hooks/hooks.json`

**Step 1: Check what's in dev-tools hooks.json**

Read `plugins/dev-tools/hooks/hooks.json` to see if it has other hooks besides tool routing.

**Step 2: Remove tool routing files**

```bash
rm plugins/dev-tools/hooks/check_tool_routing.py
rm plugins/dev-tools/hooks/test_tool_routing.py
rm plugins/dev-tools/hooks/tool-routes.json
rm plugins/dev-tools/hooks/run_fixture.sh
rm -rf plugins/dev-tools/hooks/fixtures/
```

**Step 3: Update or remove hooks.json**

If hooks.json only contained tool routing hooks, remove it:
```bash
rm plugins/dev-tools/hooks/hooks.json
```

If it has other hooks, edit to remove only the tool routing entries.

**Step 4: Update dev-tools README if needed**

Remove any references to tool routing from `plugins/dev-tools/README.md`.

**Step 5: Commit**

```bash
git add -A plugins/dev-tools/
git commit -m "refactor(dev-tools): remove tool routing (moved to standalone plugin)"
```

---

## Task 13: Final Verification

**Step 1: Run all tool-routing tests**

```bash
cd plugins/tool-routing && uv run pytest tests/ -v
```

Expected: All tests pass

**Step 2: Run inline fixture tests**

```bash
cd plugins/tool-routing && uv run tool-routing test
```

Expected: All inline tests pass

**Step 3: Verify list command**

```bash
cd plugins/tool-routing && uv run tool-routing list
```

Expected: Shows all routes with sources

**Step 4: Test check command manually**

```bash
cd plugins/tool-routing && echo '{"tool_name": "WebFetch", "tool_input": {"url": "https://github.com/foo/bar/pull/123"}}' | CLAUDE_PLUGIN_ROOT=. uv run tool-routing check
echo "Exit code: $?"
```

Expected: Exit code 2, message about gh pr view

**Step 5: Run ruff for code quality**

```bash
cd plugins/tool-routing && uv run ruff check src/ tests/
```

Expected: No errors

**Step 6: Commit any fixes**

If any issues found, fix and commit.

---

## Summary

After completing all tasks:

1. New standalone `tool-routing` plugin with:
   - Python package with src layout
   - CLI with `check`, `test`, `list` subcommands
   - YAML config with inline tests
   - Multi-source route discovery

2. Routes migrated from dev-tools:
   - GitHub PR routing
   - Atlassian routing
   - Buildkite routing
   - MCP CLI/tool misuse prevention
   - Heredoc/commit message routing
   - Echo/cat abuse prevention

3. dev-tools cleaned up:
   - Tool routing code removed
   - Only skills remain

4. Architecture supports:
   - Plugin-contributed routes
   - Project-local routes
   - Conflict detection
   - Inline test fixtures

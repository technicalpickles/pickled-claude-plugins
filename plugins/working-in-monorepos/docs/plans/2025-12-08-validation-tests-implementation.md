# Validation Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add three-layer testing (static, integration, subagent E2E) to catch hook errors before release.

**Architecture:** Pytest for static and script integration tests; slash command for subagent E2E tests. Tests adapted from tool-routing plugin patterns.

**Tech Stack:** pytest, Python 3.11+, uv for dependency management

---

## Task 1: Create pyproject.toml

**Files:**
- Create: `plugins/working-in-monorepos/pyproject.toml`

**Step 1: Create pyproject.toml with pytest dependency**

```toml
[project]
name = "working-in-monorepos-tests"
version = "0.1.0"
description = "Tests for working-in-monorepos plugin"
requires-python = ">=3.11"

dependencies = [
    "pytest>=8.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

**Step 2: Verify uv can sync**

Run: `cd plugins/working-in-monorepos && uv sync`
Expected: Dependencies installed successfully

**Step 3: Commit**

```
git add plugins/working-in-monorepos/pyproject.toml
git commit -m "build(working-in-monorepos): add pyproject.toml with pytest"
```

---

## Task 2: Create test_plugin_structure.py - TestPluginManifest

**Files:**
- Create: `plugins/working-in-monorepos/tests/__init__.py`
- Create: `plugins/working-in-monorepos/tests/test_plugin_structure.py`

**Step 1: Create empty __init__.py**

```python
# Tests for working-in-monorepos plugin
```

**Step 2: Write TestPluginManifest tests**

```python
"""Tests to validate plugin structure matches Claude Code's expected format."""

import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


class TestPluginManifest:
    """Validate .claude-plugin/plugin.json exists and has required fields."""

    def test_manifest_exists(self):
        """Plugin manifest must exist."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        assert manifest_path.exists(), (
            f"Missing plugin manifest at {manifest_path}. "
            "Create .claude-plugin/plugin.json with at least a 'name' field."
        )

    def test_manifest_is_valid_json(self):
        """Plugin manifest must be valid JSON."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            pytest.skip("Manifest doesn't exist (covered by other test)")

        content = manifest_path.read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in plugin.json: {e}")

    def test_manifest_has_required_fields(self):
        """Plugin manifest must have required 'name' field."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            pytest.skip("Manifest doesn't exist (covered by other test)")

        manifest = json.loads(manifest_path.read_text())

        assert "name" in manifest, "Plugin manifest must have 'name' field"
        assert isinstance(manifest["name"], str), "'name' must be a string"
        assert len(manifest["name"]) > 0, "'name' must not be empty"

    def test_manifest_name_matches_directory(self):
        """Plugin name should match directory name for consistency."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            pytest.skip("Manifest doesn't exist (covered by other test)")

        manifest = json.loads(manifest_path.read_text())
        expected_name = PLUGIN_ROOT.name

        assert manifest.get("name") == expected_name, (
            f"Plugin name '{manifest.get('name')}' doesn't match "
            f"directory name '{expected_name}'"
        )
```

**Step 3: Run tests to verify they pass**

Run: `cd plugins/working-in-monorepos && uv run pytest tests/test_plugin_structure.py::TestPluginManifest -v`
Expected: All 4 tests pass

**Step 4: Commit**

```
git add plugins/working-in-monorepos/tests/
git commit -m "test(working-in-monorepos): add TestPluginManifest tests"
```

---

## Task 3: Add TestHooksJson to test_plugin_structure.py

**Files:**
- Modify: `plugins/working-in-monorepos/tests/test_plugin_structure.py`

**Step 1: Add TestHooksJson class**

Append to test_plugin_structure.py:

```python
class TestHooksJson:
    """Validate hooks/hooks.json format matches Claude Code's expected structure."""

    VALID_HOOK_EVENTS = {
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "Notification",
        "Stop",
        "SubagentStop",
        "SessionStart",
        "SessionEnd",
        "PreCompact",
    }

    VALID_HOOK_TYPES = {"command"}

    def test_hooks_json_exists(self):
        """hooks/hooks.json should exist if plugin provides hooks."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        assert hooks_path.exists(), (
            f"Missing hooks.json at {hooks_path}. "
            "Plugin hooks must be defined in hooks/hooks.json"
        )

    def test_hooks_json_is_valid_json(self):
        """hooks.json must be valid JSON."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        content = hooks_path.read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in hooks.json: {e}")

    def test_hooks_top_level_structure(self):
        """Top-level 'hooks' must be an object keyed by event name."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())

        assert "hooks" in data, "hooks.json must have a 'hooks' key"

        hooks = data["hooks"]
        assert isinstance(hooks, dict), (
            "hooks must be an object keyed by event name, "
            f"not {type(hooks).__name__}"
        )

    def test_hooks_event_names_are_valid(self):
        """Hook event names must be valid Claude Code events."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid (covered by other test)")

        for event_name in hooks.keys():
            assert event_name in self.VALID_HOOK_EVENTS, (
                f"Invalid hook event '{event_name}'. "
                f"Valid events: {sorted(self.VALID_HOOK_EVENTS)}"
            )

    def test_hooks_type_is_command(self):
        """Hook type must be 'command'."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid")

        for event_name, event_hooks in hooks.items():
            if not isinstance(event_hooks, list):
                continue

            for i, hook_entry in enumerate(event_hooks):
                inner_hooks = hook_entry.get("hooks", [])
                if not isinstance(inner_hooks, list):
                    continue

                for j, inner_hook in enumerate(inner_hooks):
                    if "type" in inner_hook:
                        hook_type = inner_hook["type"]
                        assert hook_type in self.VALID_HOOK_TYPES, (
                            f"hooks['{event_name}'][{i}].hooks[{j}].type "
                            f"must be one of {self.VALID_HOOK_TYPES}, not '{hook_type}'"
                        )

    def test_hooks_command_uses_braced_plugin_root(self):
        """Hook commands should use ${CLAUDE_PLUGIN_ROOT} with braces."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid")

        for event_name, event_hooks in hooks.items():
            if not isinstance(event_hooks, list):
                continue

            for i, hook_entry in enumerate(event_hooks):
                inner_hooks = hook_entry.get("hooks", [])
                if not isinstance(inner_hooks, list):
                    continue

                for j, inner_hook in enumerate(inner_hooks):
                    command = inner_hook.get("command", "")
                    if "$CLAUDE_PLUGIN_ROOT" in command and "${CLAUDE_PLUGIN_ROOT}" not in command:
                        pytest.fail(
                            f"hooks['{event_name}'][{i}].hooks[{j}].command uses "
                            "$CLAUDE_PLUGIN_ROOT without braces. "
                            "Use ${CLAUDE_PLUGIN_ROOT} for reliable expansion."
                        )
```

**Step 2: Run tests to verify they pass**

Run: `cd plugins/working-in-monorepos && uv run pytest tests/test_plugin_structure.py::TestHooksJson -v`
Expected: All 6 tests pass

**Step 3: Commit**

```
git add plugins/working-in-monorepos/tests/test_plugin_structure.py
git commit -m "test(working-in-monorepos): add TestHooksJson validation tests"
```

---

## Task 4: Add TestHooksAntiPatterns

**Files:**
- Modify: `plugins/working-in-monorepos/tests/test_plugin_structure.py`

**Step 1: Add TestHooksAntiPatterns class**

Append to test_plugin_structure.py:

```python
class TestHooksAntiPatterns:
    """Detect known-bad hook patterns that cause subtle runtime failures."""

    def test_no_bash_with_script_args(self):
        """Detect bash+args anti-pattern that breaks stdin handling.

        Wrong: {"command": "bash", "args": ["script.sh"]}
        Right: {"command": "script.sh"} (call script directly)

        When bash receives stdin AND a script via args, the stdin
        gets interpreted as commands by bash itself, not passed
        to the script. This causes errors like:
        "bash: line 1: session_id:xxx: command not found"
        """
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            pytest.skip("hooks.json doesn't exist")

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})

        if not isinstance(hooks, dict):
            pytest.skip("hooks structure invalid")

        for event_name, event_hooks in hooks.items():
            if not isinstance(event_hooks, list):
                continue

            for i, hook_entry in enumerate(event_hooks):
                inner_hooks = hook_entry.get("hooks", [])
                if not isinstance(inner_hooks, list):
                    continue

                for j, inner_hook in enumerate(inner_hooks):
                    command = inner_hook.get("command", "")
                    args = inner_hook.get("args", [])

                    # Check for bash/sh with script in args
                    if command in ("bash", "sh", "/bin/bash", "/bin/sh"):
                        script_args = [
                            a for a in args
                            if a.endswith(".sh") or "/" in a
                        ]
                        if script_args:
                            pytest.fail(
                                f"hooks['{event_name}'][{i}].hooks[{j}] uses "
                                f"bash+args anti-pattern: command='{command}', "
                                f"args={args}. This breaks stdin handling. "
                                f"Call the script directly instead: "
                                f'command="{script_args[0]}"'
                            )
```

**Step 2: Run test to verify it passes**

Run: `cd plugins/working-in-monorepos && uv run pytest tests/test_plugin_structure.py::TestHooksAntiPatterns -v`
Expected: 1 test passes (current hooks.json uses correct format)

**Step 3: Commit**

```
git add plugins/working-in-monorepos/tests/test_plugin_structure.py
git commit -m "test(working-in-monorepos): add bash+args anti-pattern detection"
```

---

## Task 5: Create test_hooks_integration.py - Script Existence Tests

**Files:**
- Create: `plugins/working-in-monorepos/tests/test_hooks_integration.py`

**Step 1: Write script existence and executability tests**

```python
"""Integration tests that run hooks like Claude Code does."""

import json
import os
import subprocess
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


class TestSessionStartHook:
    """Integration tests for the SessionStart hook script."""

    def get_hook_script_path(self) -> Path | None:
        """Extract script path from hooks.json."""
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        if not hooks_path.exists():
            return None

        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})
        session_start = hooks.get("SessionStart", [])

        if not session_start:
            return None

        for hook_entry in session_start:
            inner_hooks = hook_entry.get("hooks", [])
            for inner_hook in inner_hooks:
                command = inner_hook.get("command", "")
                # Replace ${CLAUDE_PLUGIN_ROOT} with actual path
                if "${CLAUDE_PLUGIN_ROOT}" in command:
                    command = command.replace(
                        "${CLAUDE_PLUGIN_ROOT}",
                        str(PLUGIN_ROOT)
                    )
                if command.endswith(".sh"):
                    return Path(command)

        return None

    def test_hook_script_exists(self):
        """Script referenced in hooks.json must exist."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")

        assert script_path.exists(), (
            f"Hook script does not exist: {script_path}"
        )

    def test_hook_script_is_executable(self):
        """Script must be executable."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist (covered by other test)")

        assert os.access(script_path, os.X_OK), (
            f"Hook script is not executable: {script_path}. "
            f"Run: chmod +x {script_path}"
        )

    def test_hook_script_has_shebang(self):
        """Script must have a valid shebang line."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        content = script_path.read_text()
        first_line = content.split("\n")[0] if content else ""

        assert first_line.startswith("#!"), (
            f"Hook script missing shebang: {script_path}. "
            "First line should be #!/usr/bin/env bash or similar"
        )
```

**Step 2: Run tests to verify they pass**

Run: `cd plugins/working-in-monorepos && uv run pytest tests/test_hooks_integration.py -v`
Expected: All 3 tests pass

**Step 3: Commit**

```
git add plugins/working-in-monorepos/tests/test_hooks_integration.py
git commit -m "test(working-in-monorepos): add hook script existence tests"
```

---

## Task 6: Add stdin handling tests to test_hooks_integration.py

**Files:**
- Modify: `plugins/working-in-monorepos/tests/test_hooks_integration.py`

**Step 1: Add stdin handling test**

Append to TestSessionStartHook class:

```python
    def test_hook_handles_stdin_json(self):
        """Hook must handle JSON stdin without errors.

        Claude Code passes session data as JSON on stdin.
        The hook should consume or ignore it, not fail.
        """
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        # Simulate Claude Code's stdin format
        stdin_data = json.dumps({
            "session_id": "test-session-123",
            "cwd": "/tmp/test-project",
            "timestamp": "2025-12-08T12:00:00Z"
        })

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/tmp"  # Run outside git repo
        )

        # Should exit 0 (success) even if it can't detect a monorepo
        assert result.returncode == 0, (
            f"Hook failed with stdin. Exit code: {result.returncode}\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )

        # Should not have error messages about parsing stdin
        assert "command not found" not in result.stderr, (
            "Hook is interpreting stdin as commands. "
            "Ensure script consumes stdin with 'cat > /dev/null' or similar."
        )
```

**Step 2: Run test to verify it passes**

Run: `cd plugins/working-in-monorepos && uv run pytest tests/test_hooks_integration.py::TestSessionStartHook::test_hook_handles_stdin_json -v`
Expected: Test passes

**Step 3: Commit**

```
git add plugins/working-in-monorepos/tests/test_hooks_integration.py
git commit -m "test(working-in-monorepos): add stdin handling test"
```

---

## Task 7: Add git repo scenario tests

**Files:**
- Modify: `plugins/working-in-monorepos/tests/test_hooks_integration.py`

**Step 1: Add git repo scenario tests**

Append to TestSessionStartHook class:

```python
    def test_hook_succeeds_outside_git_repo(self, tmp_path):
        """Hook should exit cleanly when not in a git repo."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        stdin_data = json.dumps({"session_id": "test"})

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0, (
            f"Hook should exit 0 outside git repo. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_hook_succeeds_in_git_repo_without_monorepo(self, tmp_path):
        """Hook should work in a git repo without .monorepo.json."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        # Create a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        stdin_data = json.dumps({"session_id": "test"})

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0, (
            f"Hook failed in git repo. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_hook_detects_monorepo_config(self, tmp_path):
        """Hook should detect existing .monorepo.json."""
        script_path = self.get_hook_script_path()
        if script_path is None:
            pytest.skip("No SessionStart hook script found")
        if not script_path.exists():
            pytest.skip("Script doesn't exist")

        # Create a git repo with .monorepo.json
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        monorepo_config = tmp_path / ".monorepo.json"
        monorepo_config.write_text(json.dumps({
            "subprojects": [
                {"name": "frontend", "path": "frontend"},
                {"name": "backend", "path": "backend"}
            ]
        }))

        stdin_data = json.dumps({"session_id": "test"})

        result = subprocess.run(
            [str(script_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(tmp_path)
        )

        assert result.returncode == 0, (
            f"Hook failed with .monorepo.json. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

        # Should mention detecting the monorepo
        assert "monorepo" in result.stdout.lower() or "subproject" in result.stdout.lower(), (
            f"Hook should report detecting monorepo. stdout: {result.stdout}"
        )
```

**Step 2: Run tests to verify they pass**

Run: `cd plugins/working-in-monorepos && uv run pytest tests/test_hooks_integration.py -v`
Expected: All 6 tests pass

**Step 3: Commit**

```
git add plugins/working-in-monorepos/tests/test_hooks_integration.py
git commit -m "test(working-in-monorepos): add git repo scenario tests"
```

---

## Task 8: Create /validate command for subagent E2E tests

**Files:**
- Create: `plugins/working-in-monorepos/commands/validate.md`

**Step 1: Write the validate command**

```markdown
Run integration tests for the working-in-monorepos plugin.

## What This Tests

1. **Hook Configuration** - Validates hooks.json structure and patterns
2. **Script Execution** - Runs hooks with realistic stdin
3. **Skill Effectiveness** - Tests agent behavior in monorepo scenarios

## Quick Mode (Default)

Run pytest tests only:

```bash
cd plugins/working-in-monorepos && uv run pytest tests/ -v
```

Report results and any failures.

## Full Mode (with --full flag)

Additionally run subagent scenarios from `skills/working-in-monorepos/tests/baseline-scenarios.md`:

1. Set up test monorepo in /tmp with structure:
   - /tmp/test-monorepo/
   - /tmp/test-monorepo/ruby/ (with Gemfile)
   - /tmp/test-monorepo/cli/ (with package.json)

2. For each scenario, dispatch a Task subagent with the scenario prompt

3. Evaluate: Did the agent use absolute paths?

4. Report pass/fail for each scenario

## Usage

```
/working-in-monorepos:validate           # Quick mode - pytest only
/working-in-monorepos:validate --full    # Full mode - includes subagent tests
```
```

**Step 2: Commit**

```
git add plugins/working-in-monorepos/commands/validate.md
git commit -m "feat(working-in-monorepos): add /validate command for E2E tests"
```

---

## Task 9: Create test fixture for session-start input

**Files:**
- Create: `plugins/working-in-monorepos/tests/fixtures/session-start.json`

**Step 1: Create fixture file**

```json
{
  "session_id": "test-session-abc123",
  "cwd": "/Users/test/workspace/my-monorepo",
  "timestamp": "2025-12-08T12:00:00Z"
}
```

**Step 2: Commit**

```
git add plugins/working-in-monorepos/tests/fixtures/
git commit -m "test(working-in-monorepos): add session-start test fixture"
```

---

## Task 10: Run full test suite and verify

**Step 1: Run all tests**

Run: `cd plugins/working-in-monorepos && uv run pytest tests/ -v`
Expected: All tests pass (approximately 12 tests)

**Step 2: Verify test coverage**

Confirm tests cover:
- [ ] Plugin manifest validation (4 tests)
- [ ] Hooks.json structure validation (6 tests)
- [ ] Anti-pattern detection (1 test)
- [ ] Script existence and executability (3 tests)
- [ ] Stdin handling (1 test)
- [ ] Git repo scenarios (3 tests)

**Step 3: Final commit if any cleanup needed**

```
git commit -m "test(working-in-monorepos): complete validation test suite"
```

---

## Summary

After completing all tasks:

- **11 static tests** catch configuration errors at development time
- **6 integration tests** verify script behavior with realistic inputs
- **1 slash command** enables subagent E2E testing

Run `uv run pytest tests/ -v` from the plugin directory to execute all automated tests.

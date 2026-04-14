# Sandbox-First Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configurable `skip_failure_requirement` to the sandbox-first plugin so known-broken-in-sandbox commands can use `dangerouslyDisableSandbox: true` without a prior sandboxed failure.

**Architecture:** A new `config.py` module handles loading and merging config from two JSON files (user-level and project-level). The checker gains a `command_matches_skip_list()` function and calls it before the transcript check. The CLI resolves config paths from env vars and passes them through.

**Tech Stack:** Python 3.10+, pytest, existing sandbox-first plugin structure

**Spec:** `docs/plans/2026-04-14-sandbox-first-config-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/sandbox_first/config.py` (new) | Load JSON config from disk, merge user + project lists, validate schema |
| `src/sandbox_first/checker.py` (modify) | Add `command_matches_skip_list()`, integrate config into `check_pre_tool_use()` |
| `src/sandbox_first/cli.py` (modify) | Resolve config paths from env vars, pass to checker |
| `tests/test_config.py` (new) | Config loading, schema validation, merge behavior |
| `tests/test_checker.py` (modify) | Prefix matching, integration with skip list |
| `skills/sandbox-first/SKILL.md` (modify) | Add "Configured Exceptions" section |
| `README.md` (modify) | Document config file format and locations |

---

### Task 1: Config Loading Module

**Files:**
- Create: `plugins/sandbox-first/src/sandbox_first/config.py`
- Create: `plugins/sandbox-first/tests/test_config.py`

- [ ] **Step 1: Write failing tests for `load_skip_list_from_file()`**

In `tests/test_config.py`:

```python
import json

import pytest

from sandbox_first.config import load_skip_list_from_file


class TestLoadSkipListFromFile:
    def test_valid_config(self, tmp_path):
        """Reads skip_failure_requirement from a valid JSON file."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker", "bk"]}))
        assert load_skip_list_from_file(str(config)) == ["docker", "bk"]

    def test_missing_file(self):
        """Missing file returns empty list."""
        assert load_skip_list_from_file("/nonexistent/sandbox-first.json") == []

    def test_malformed_json(self, tmp_path):
        """Malformed JSON returns empty list."""
        config = tmp_path / "sandbox-first.json"
        config.write_text("not json {{{")
        assert load_skip_list_from_file(str(config)) == []

    def test_missing_key(self, tmp_path):
        """JSON without skip_failure_requirement returns empty list."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"other_key": "value"}))
        assert load_skip_list_from_file(str(config)) == []

    def test_wrong_type_for_key(self, tmp_path):
        """Non-array skip_failure_requirement returns empty list."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": "not-an-array"}))
        assert load_skip_list_from_file(str(config)) == []

    def test_filters_non_strings(self, tmp_path):
        """Non-string values in the array are filtered out."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker", 42, None, "bk"]}))
        assert load_skip_list_from_file(str(config)) == ["docker", "bk"]

    def test_extra_keys_ignored(self, tmp_path):
        """Extra keys in the config are silently ignored."""
        config = tmp_path / "sandbox-first.json"
        config.write_text(json.dumps({
            "skip_failure_requirement": ["docker"],
            "future_key": True,
        }))
        assert load_skip_list_from_file(str(config)) == ["docker"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_config.py -v`

Expected: ImportError (module doesn't exist yet)

- [ ] **Step 3: Implement `load_skip_list_from_file()`**

Create `src/sandbox_first/config.py`:

```python
"""Configuration loading for sandbox-first plugin."""

import json


def load_skip_list_from_file(path: str) -> list[str]:
    """Load skip_failure_requirement entries from a JSON config file.

    Returns an empty list if the file is missing, malformed, or has
    an invalid schema. Non-string entries are filtered out.
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    entries = data.get("skip_failure_requirement") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []

    return [e for e in entries if isinstance(e, str)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_config.py -v`

Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```
feat(sandbox-first): add config loader for skip_failure_requirement
```

---

### Task 2: Config Merge Function

**Files:**
- Modify: `plugins/sandbox-first/src/sandbox_first/config.py`
- Modify: `plugins/sandbox-first/tests/test_config.py`

- [ ] **Step 1: Write failing tests for `load_merged_skip_list()`**

Append to `tests/test_config.py`:

```python
from sandbox_first.config import load_merged_skip_list


class TestLoadMergedSkipList:
    def test_both_files_present(self, tmp_path):
        """Union of user and project lists."""
        user = tmp_path / "user" / "sandbox-first.json"
        user.parent.mkdir()
        user.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        project = tmp_path / "project" / "sandbox-first.json"
        project.parent.mkdir()
        project.write_text(json.dumps({"skip_failure_requirement": ["bk"]}))

        result = load_merged_skip_list(str(user), str(project))
        assert sorted(result) == ["bk", "docker"]

    def test_duplicates_deduplicated(self, tmp_path):
        """Same entry in both files appears once."""
        user = tmp_path / "user" / "sandbox-first.json"
        user.parent.mkdir()
        user.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        project = tmp_path / "project" / "sandbox-first.json"
        project.parent.mkdir()
        project.write_text(json.dumps({"skip_failure_requirement": ["docker", "bk"]}))

        result = load_merged_skip_list(str(user), str(project))
        assert sorted(result) == ["bk", "docker"]

    def test_only_user_file(self, tmp_path):
        """Only user config exists."""
        user = tmp_path / "sandbox-first.json"
        user.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        result = load_merged_skip_list(str(user), "/nonexistent/sandbox-first.json")
        assert result == ["docker"]

    def test_only_project_file(self, tmp_path):
        """Only project config exists."""
        project = tmp_path / "sandbox-first.json"
        project.write_text(json.dumps({"skip_failure_requirement": ["bk"]}))

        result = load_merged_skip_list("/nonexistent/sandbox-first.json", str(project))
        assert result == ["bk"]

    def test_neither_file(self):
        """No config files returns empty list."""
        result = load_merged_skip_list("/nonexistent/a.json", "/nonexistent/b.json")
        assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_config.py::TestLoadMergedSkipList -v`

Expected: ImportError (function doesn't exist yet)

- [ ] **Step 3: Implement `load_merged_skip_list()`**

Add to `src/sandbox_first/config.py`:

```python
def load_merged_skip_list(user_config_path: str, project_config_path: str) -> list[str]:
    """Load and merge skip lists from user and project config files.

    Returns the union of both lists (deduplicated, order not guaranteed).
    """
    user_entries = load_skip_list_from_file(user_config_path)
    project_entries = load_skip_list_from_file(project_config_path)
    return list(set(user_entries + project_entries))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_config.py -v`

Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```
feat(sandbox-first): add merged config loading from user + project paths
```

---

### Task 3: Prefix Matching Logic

**Files:**
- Modify: `plugins/sandbox-first/src/sandbox_first/checker.py`
- Modify: `plugins/sandbox-first/tests/test_checker.py`

- [ ] **Step 1: Write failing tests for `command_matches_skip_list()`**

Add to `tests/test_checker.py`:

```python
from sandbox_first.checker import command_matches_skip_list


class TestCommandMatchesSkipList:
    def test_exact_match(self):
        """Command equals entry exactly."""
        assert command_matches_skip_list("docker", ["docker"]) is True

    def test_prefix_with_args(self):
        """Command starts with entry followed by space."""
        assert command_matches_skip_list("docker build .", ["docker"]) is True

    def test_multi_word_prefix(self):
        """Multi-word entry matches multi-word prefix."""
        assert command_matches_skip_list("colima ssh myhost", ["colima ssh"]) is True

    def test_no_word_boundary_no_match(self):
        """Entry without word boundary does not match."""
        assert command_matches_skip_list("dockerize app", ["docker"]) is False

    def test_partial_entry_no_match(self):
        """Partial entry does not match full command name."""
        assert command_matches_skip_list("docker build", ["dock"]) is False

    def test_leading_whitespace_stripped(self):
        """Leading whitespace on command is stripped before matching."""
        assert command_matches_skip_list("  docker build", ["docker"]) is True

    def test_no_match_different_command(self):
        """Completely different command does not match."""
        assert command_matches_skip_list("echo hello", ["docker", "bk"]) is False

    def test_empty_skip_list(self):
        """Empty skip list matches nothing."""
        assert command_matches_skip_list("docker build", []) is False

    def test_multiple_entries_any_match(self):
        """Matches if any entry in the list matches."""
        assert command_matches_skip_list("bk local run", ["docker", "bk"]) is True

    def test_multi_word_no_match_different_subcommand(self):
        """Multi-word entry doesn't match different subcommand."""
        assert command_matches_skip_list("colima status", ["colima ssh"]) is False

    def test_empty_command(self):
        """Empty command matches nothing."""
        assert command_matches_skip_list("", ["docker"]) is False

    def test_tab_after_prefix(self):
        """Tab counts as whitespace boundary."""
        assert command_matches_skip_list("docker\tbuild", ["docker"]) is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_checker.py::TestCommandMatchesSkipList -v`

Expected: ImportError (function doesn't exist yet)

- [ ] **Step 3: Implement `command_matches_skip_list()`**

Add to `src/sandbox_first/checker.py`:

```python
def command_matches_skip_list(command: str, skip_list: list[str]) -> bool:
    """True if command matches any entry in the skip list (word-boundary prefix match).

    An entry matches if the command (after stripping leading whitespace) equals
    the entry exactly, or starts with the entry followed by whitespace.
    """
    cmd = command.lstrip()
    for entry in skip_list:
        if cmd == entry or (cmd.startswith(entry) and cmd[len(entry):len(entry) + 1].isspace()):
            return True
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_checker.py::TestCommandMatchesSkipList -v`

Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```
feat(sandbox-first): add word-boundary prefix matching for skip list
```

---

### Task 4: Wire Config Into checker.py

**Files:**
- Modify: `plugins/sandbox-first/src/sandbox_first/checker.py`
- Modify: `plugins/sandbox-first/tests/test_checker.py`

- [ ] **Step 1: Write failing tests for config-aware `check_pre_tool_use()`**

Add to `tests/test_checker.py`:

```python
class TestCheckPreToolUseWithConfig:
    def test_configured_command_allowed_without_prior_failure(self):
        """Unsandboxed call for a configured command is allowed without transcript failure."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "docker build .",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input, skip_list=["docker"])
        assert result is None

    def test_non_configured_command_still_denied(self):
        """Unsandboxed call for a non-configured command still requires transcript failure."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hello",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input, skip_list=["docker"])
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_empty_skip_list_preserves_existing_behavior(self):
        """Empty skip list means all unsandboxed calls need prior failure."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "docker build .",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input, skip_list=[])
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_default_skip_list_is_empty(self):
        """When skip_list is not passed, defaults to empty (backward compat)."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "docker build .",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input)
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_sandboxed_call_unaffected_by_config(self):
        """Sandboxed calls pass through regardless of config."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "docker build ."},
            "transcript_path": "/nonexistent",
        }
        assert check_pre_tool_use(hook_input, skip_list=["docker"]) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_checker.py::TestCheckPreToolUseWithConfig -v`

Expected: TypeError (check_pre_tool_use doesn't accept skip_list yet)

- [ ] **Step 3: Update `check_pre_tool_use()` signature and logic**

Modify `check_pre_tool_use()` in `src/sandbox_first/checker.py`:

```python
def check_pre_tool_use(hook_input: dict, skip_list: list[str] | None = None) -> dict | None:
    """Check a PreToolUse Bash call. Returns JSON output dict or None to allow."""
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    if not tool_input.get("dangerouslyDisableSandbox"):
        return None

    # dangerouslyDisableSandbox is set. Check skip list first.
    command = tool_input.get("command", "")
    if skip_list and command_matches_skip_list(command, skip_list):
        return None  # Allow: command is configured to skip failure requirement

    # Fall back to transcript check for recent sandboxed failure.
    transcript_path = hook_input.get("transcript_path", "")
    if find_recent_sandboxed_failure(transcript_path, lookback=LOOKBACK):
        return None  # Allow: there was a recent sandboxed failure

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": DENY_MESSAGE,
        }
    }
```

- [ ] **Step 4: Run all checker tests to verify nothing broke**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_checker.py -v`

Expected: All tests PASS (existing tests use positional arg so `skip_list` defaults to None)

- [ ] **Step 5: Commit**

```
feat(sandbox-first): integrate skip list into pre-tool-use check
```

---

### Task 5: Wire Config Into CLI

**Files:**
- Modify: `plugins/sandbox-first/src/sandbox_first/cli.py`
- Modify: `plugins/sandbox-first/tests/test_cli.py`

- [ ] **Step 1: Write failing CLI integration test**

Add to `tests/test_cli.py`:

```python
class TestPreToolUseWithConfig:
    def test_configured_command_allowed(self, tmp_path):
        """CLI allows configured command without prior failure."""
        # Put config at $HOME/.claude/sandbox-first.json
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        user_config = claude_dir / "sandbox-first.json"
        user_config.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        result = subprocess.run(
            [sys.executable, "-m", "sandbox_first.cli", "pre-tool-use"],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {
                    "command": "docker build .",
                    "dangerouslyDisableSandbox": True,
                },
                "transcript_path": "/nonexistent",
            }),
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_claude_config_dir_takes_precedence(self, tmp_path):
        """CLAUDE_CONFIG_DIR is preferred over $HOME/.claude/."""
        custom_dir = tmp_path / "custom-config"
        custom_dir.mkdir()
        config = custom_dir / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        env = {
            **os.environ,
            "PYTHONPATH": "src",
            "HOME": str(tmp_path),
            "CLAUDE_CONFIG_DIR": str(custom_dir),
        }

        result = subprocess.run(
            [sys.executable, "-m", "sandbox_first.cli", "pre-tool-use"],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {
                    "command": "docker build .",
                    "dangerouslyDisableSandbox": True,
                },
                "transcript_path": "/nonexistent",
            }),
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_project_config_via_env(self, tmp_path):
        """CLAUDE_PROJECT_DIR config is loaded."""
        project_dir = tmp_path / "myproject"
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir(parents=True)
        config = claude_dir / "sandbox-first.json"
        config.write_text(json.dumps({"skip_failure_requirement": ["docker"]}))

        env = {
            **os.environ,
            "PYTHONPATH": "src",
            "HOME": str(tmp_path),
            "CLAUDE_PROJECT_DIR": str(project_dir),
        }

        result = subprocess.run(
            [sys.executable, "-m", "sandbox_first.cli", "pre-tool-use"],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {
                    "command": "docker build .",
                    "dangerouslyDisableSandbox": True,
                },
                "transcript_path": "/nonexistent",
            }),
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_cli.py::TestPreToolUseWithConfig -v`

Expected: FAIL (CLI doesn't load config yet)

- [ ] **Step 3: Update CLI to resolve config paths and pass skip list**

Replace `src/sandbox_first/cli.py`:

```python
"""CLI entry point for sandbox-first plugin hooks."""

import json
import os
import sys

from sandbox_first.checker import check_pre_tool_use, check_post_tool_use_failure
from sandbox_first.config import load_merged_skip_list

CONFIG_FILENAME = "sandbox-first.json"


def _resolve_config_paths() -> tuple[str, str]:
    """Resolve user and project config file paths from environment."""
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if not config_dir:
        config_dir = os.path.join(os.path.expanduser("~"), ".claude")
    user_config = os.path.join(config_dir, CONFIG_FILENAME)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    project_config = os.path.join(project_dir, ".claude", CONFIG_FILENAME) if project_dir else ""

    return user_config, project_config


def main():
    if len(sys.argv) < 2:
        print("Usage: sandbox-first <pre-tool-use|post-tool-use-failure>", file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Fail open: if we can't parse input, allow the tool call
        sys.exit(0)

    if subcommand == "pre-tool-use":
        user_config, project_config = _resolve_config_paths()
        skip_list = load_merged_skip_list(user_config, project_config)
        result = check_pre_tool_use(hook_input, skip_list=skip_list)
    elif subcommand == "post-tool-use-failure":
        result = check_post_tool_use_failure(hook_input)
    else:
        sys.exit(0)

    if result is not None:
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest -v`

Expected: All tests PASS

- [ ] **Step 5: Commit**

```
feat(sandbox-first): wire config loading into CLI entry point
```

---

### Task 6: Update Skill and README

**Files:**
- Modify: `plugins/sandbox-first/skills/sandbox-first/SKILL.md`
- Modify: `plugins/sandbox-first/README.md`

- [ ] **Step 1: Update SKILL.md with configured exceptions**

Two changes:

1. Update the "Core Rule" section to acknowledge configured exceptions:

Replace:
```markdown
Always run Bash commands sandboxed first. Never set `dangerouslyDisableSandbox: true` unless
a sandboxed attempt has already failed in this session.
```

With:
```markdown
Always run Bash commands sandboxed first. Never set `dangerouslyDisableSandbox: true` unless
a sandboxed attempt has already failed in this session, or the command is listed in
`skip_failure_requirement` (see Configured Exceptions below).
```

2. Append a new section before "What NOT to Do":

```markdown
## Configured Exceptions

Some commands are known to always fail in the sandbox (e.g. `docker`, `colima ssh`).
These can be configured in `~/.claude/sandbox-first.json` or `.claude/sandbox-first.json`
under the `skip_failure_requirement` key. The enforcement hook will allow
`dangerouslyDisableSandbox: true` for these commands without requiring a prior
sandboxed failure.
```

- [ ] **Step 2: Update README.md Configuration section**

Replace the Configuration section in README.md with:

```markdown
## Configuration

### Skip Failure Requirement

Some commands are known to always fail in the sandbox. You can configure these so the plugin
allows `dangerouslyDisableSandbox: true` without requiring a prior sandboxed failure.

Create `~/.claude/sandbox-first.json` (user-level) or `.claude/sandbox-first.json` (project-level):

```json
{
  "skip_failure_requirement": [
    "docker",
    "colima ssh",
    "bk"
  ]
}
```

Entries use word-boundary prefix matching: `"docker"` matches `docker build` but not `dockerize`.
Both files are merged (union). If `CLAUDE_CONFIG_DIR` is set, user config is read from there
instead of `~/.claude/`.

### Lookback Window

The lookback window (how many transcript entries to scan for prior failures) defaults to 10.
This covers roughly 5 tool call round-trips.
```

- [ ] **Step 3: Commit**

```
docs(sandbox-first): document skip_failure_requirement config
```

---

### Task 7: Final Verification

- [ ] **Step 1: Run the full test suite**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest -v`

Expected: All tests PASS

- [ ] **Step 2: Run linter**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first ruff check src/ tests/`

Expected: No errors

- [ ] **Step 3: Verify existing tests still pass unchanged**

Run: `cd /Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/main && uv run --directory plugins/sandbox-first pytest tests/test_checker.py::TestCheckPreToolUse -v`

Expected: Original 4 tests still PASS with no modifications needed (skip_list defaults to None)

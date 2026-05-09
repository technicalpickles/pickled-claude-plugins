# Sandbox Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a `sandbox` plugin that promotes sandbox-first execution by blocking unnecessary unsandboxed Bash calls and surfacing sandbox failure guidance.

**Architecture:** A Python-based plugin with PreToolUse and PostToolUseFailure hooks, plus a skill for soft behavioral guidance. PreToolUse denies `dangerouslyDisableSandbox: true` calls unless the transcript shows a recent sandboxed failure. PostToolUseFailure injects context about sandbox restrictions when sandboxed commands fail.

**Tech Stack:** Python 3 (matching tool-routing patterns), uv for running, pytest for tests, hatchling for build.

---

## Verified Assumptions

These were confirmed via test harness (`/tmp/sandbox-hook-test/`):

- `tool_input.dangerouslyDisableSandbox` is present (as `true`) in PreToolUse when Claude sets it
- `tool_input.dangerouslyDisableSandbox` is absent when running sandboxed
- PostToolUseFailure fires on failed Bash calls with `tool_input` and `error` fields
- `error` field contains stderr output (e.g. `"Operation not permitted"`)
- `transcript_path` is available in all hook inputs
- Transcript JSONL contains full tool_use blocks with `dangerouslyDisableSandbox` when set

## Design Decisions

1. **Python, not bash** - need JSON parsing, JSONL scanning, structured output
2. **Transcript as state** - no temp files or breadcrumbs; scan transcript for prior sandboxed failures
3. **Lookback window, not command matching** - check "any failed sandboxed Bash call in last N transcript entries" rather than trying to match specific commands (too fragile across retries)
4. **PostToolUseFailure, not PostToolUse** - purpose-built hook for failure cases, cleaner separation
5. **Deny + allow pattern** - PreToolUse denies unsandboxed by default, allows if transcript shows recent sandboxed failure
6. **Generic guidance in v1** - PostToolUseFailure points to sandbox config keys, no smart error pattern matching yet

## Plugin Structure

```
plugins/sandbox/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json      # (added to root marketplace.json)
├── hooks/
│   └── hooks.json
├── skills/
│   └── sandbox-first/
│       └── SKILL.md
├── src/
│   └── sandbox_plugin/
│       ├── __init__.py
│       ├── cli.py            # Entry point: subcommands for each hook
│       ├── transcript.py     # JSONL transcript reader
│       └── checker.py        # Logic for pre/post hook decisions
├── tests/
│   ├── conftest.py
│   ├── test_checker.py
│   └── test_transcript.py
├── pyproject.toml
└── README.md
```

---

### Task 1: Scaffold the plugin

**Files:**
- Create: `plugins/sandbox/.claude-plugin/plugin.json`
- Create: `plugins/sandbox/pyproject.toml`
- Create: `plugins/sandbox/src/sandbox_plugin/__init__.py`
- Create: `plugins/sandbox/hooks/hooks.json`
- Modify: `.claude-plugin/marketplace.json` (add sandbox entry)

**Step 1: Create plugin.json**

```json
{
  "name": "sandbox",
  "description": "Promotes sandbox-first execution by intercepting unnecessary unsandboxed Bash calls",
  "author": {"name": "Josh Nichols", "email": "josh@technicalpickles.com"},
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT"
}
```

**Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sandbox-plugin"
version = "0.1.0"
description = "Claude Code sandbox enforcement plugin"
requires-python = ">=3.10"

[project.scripts]
sandbox-plugin = "sandbox_plugin.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/sandbox_plugin"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[dependency-groups]
dev = ["pytest", "ruff"]
```

**Step 3: Create empty `__init__.py`**

**Step 4: Create hooks.json**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --quiet --directory \"${CLAUDE_PLUGIN_ROOT}\" sandbox-plugin pre-tool-use"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --quiet --directory \"${CLAUDE_PLUGIN_ROOT}\" sandbox-plugin post-tool-use-failure"
          }
        ]
      }
    ]
  }
}
```

**Step 5: Add to marketplace.json**

Add entry to root `.claude-plugin/marketplace.json`:
```json
{"name": "sandbox", "source": "./plugins/sandbox", "version": "0.1.0"}
```

**Step 6: Commit**

```
feat(sandbox): scaffold plugin structure
```

---

### Task 2: Implement transcript reader

**Files:**
- Create: `plugins/sandbox/src/sandbox_plugin/transcript.py`
- Create: `plugins/sandbox/tests/test_transcript.py`

**Step 1: Write failing tests**

Tests for `transcript.py`:

```python
import json
import tempfile
from sandbox_plugin.transcript import find_recent_sandboxed_failure

def write_transcript(entries):
    """Helper: write list of JSONL dicts to a temp file, return path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for entry in entries:
        f.write(json.dumps(entry) + "\n")
    f.close()
    return f.name


def make_tool_use_entry(command, dangerously_disable=False):
    """Helper: create a transcript entry with a Bash tool_use block."""
    tool_input = {"command": command}
    if dangerously_disable:
        tool_input["dangerouslyDisableSandbox"] = True
    return {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "Bash",
                    "input": tool_input
                }
            ]
        }
    }


def make_tool_error_entry(error_text):
    """Helper: create a transcript entry representing a tool failure."""
    return {
        "message": {
            "role": "tool",
            "content": [
                {
                    "type": "tool_result",
                    "is_error": True,
                    "content": error_text,
                }
            ]
        }
    }


def make_tool_success_entry(stdout="ok"):
    """Helper: create a transcript entry representing a tool success."""
    return {
        "message": {
            "role": "tool",
            "content": [
                {
                    "type": "tool_result",
                    "is_error": False,
                    "content": stdout,
                }
            ]
        }
    }


class TestFindRecentSandboxedFailure:
    def test_no_entries(self):
        path = write_transcript([])
        assert find_recent_sandboxed_failure(path, lookback=10) is False

    def test_sandboxed_failure_found(self):
        entries = [
            make_tool_use_entry("curl https://example.com"),
            make_tool_error_entry("Operation not permitted"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is True

    def test_unsandboxed_failure_not_counted(self):
        entries = [
            make_tool_use_entry("curl https://example.com", dangerously_disable=True),
            make_tool_error_entry("Connection refused"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is False

    def test_sandboxed_success_not_counted(self):
        entries = [
            make_tool_use_entry("echo hello"),
            make_tool_success_entry("hello"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is False

    def test_outside_lookback_window(self):
        """Old failure + many entries after = outside window."""
        entries = [
            make_tool_use_entry("curl https://example.com"),
            make_tool_error_entry("Operation not permitted"),
        ]
        # Add filler entries to push failure outside lookback
        for i in range(15):
            entries.append(make_tool_use_entry(f"echo {i}"))
            entries.append(make_tool_success_entry(str(i)))
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=5) is False

    def test_sandboxed_failure_within_lookback(self):
        """Recent failure within window."""
        entries = [
            make_tool_use_entry("echo old"),
            make_tool_success_entry("old"),
            make_tool_use_entry("curl https://example.com"),
            make_tool_error_entry("Operation not permitted"),
            make_tool_use_entry("echo thinking"),  # Claude does something between
            make_tool_success_entry("thinking"),
        ]
        path = write_transcript(entries)
        assert find_recent_sandboxed_failure(path, lookback=10) is True

    def test_malformed_lines_skipped(self):
        """Gracefully handle non-JSON lines."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        f.write("not json\n")
        f.write(json.dumps(make_tool_use_entry("curl https://x.com")) + "\n")
        f.write(json.dumps(make_tool_error_entry("Operation not permitted")) + "\n")
        f.close()
        assert find_recent_sandboxed_failure(f.name, lookback=10) is True
```

**Step 2: Run tests to verify they fail**

Run: `uv run --directory plugins/sandbox pytest tests/test_transcript.py -v`
Expected: FAIL (module not found)

**Step 3: Implement transcript reader**

```python
"""Read Claude Code transcript JSONL and find recent sandboxed Bash failures."""

import json


def find_recent_sandboxed_failure(transcript_path: str, lookback: int = 10) -> bool:
    """Check if there's a recent sandboxed Bash failure in the transcript.

    Reads the last `lookback` entries and looks for a Bash tool_use
    without dangerouslyDisableSandbox followed by an error tool_result.
    """
    entries = _read_tail(transcript_path, lookback)

    # Walk backwards looking for pattern: tool_use(sandboxed) + tool_result(error)
    i = len(entries) - 1
    while i >= 0:
        entry = entries[i]
        if _is_sandboxed_bash_failure(entry, entries, i):
            return True
        i -= 1

    return False


def _read_tail(path: str, n: int) -> list[dict]:
    """Read the last n lines of a JSONL file, skipping malformed lines."""
    entries = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return []

    return entries[-n:] if len(entries) > n else entries


def _is_sandboxed_bash_failure(entry: dict, entries: list[dict], index: int) -> bool:
    """Check if entry is a tool error that follows a sandboxed Bash call."""
    msg = entry.get("message", {})
    if msg.get("role") != "tool":
        return False

    content = msg.get("content", [])
    if not isinstance(content, list):
        return False

    is_error = any(
        isinstance(block, dict) and block.get("is_error")
        for block in content
    )
    if not is_error:
        return False

    # Look backwards for the preceding Bash tool_use (sandboxed)
    for j in range(index - 1, -1, -1):
        prev = entries[j]
        prev_msg = prev.get("message", {})
        if prev_msg.get("role") != "assistant":
            continue
        prev_content = prev_msg.get("content", [])
        if not isinstance(prev_content, list):
            continue
        for block in prev_content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                tool_input = block.get("input", {})
                if not tool_input.get("dangerouslyDisableSandbox"):
                    return True
                else:
                    return False  # Was unsandboxed, doesn't count
        break  # Only check the immediately preceding assistant message

    return False
```

**Step 4: Run tests to verify they pass**

Run: `uv run --directory plugins/sandbox pytest tests/test_transcript.py -v`
Expected: all PASS

**Step 5: Commit**

```
feat(sandbox): add transcript reader for sandboxed failure detection
```

---

### Task 3: Implement checker logic

**Files:**
- Create: `plugins/sandbox/src/sandbox_plugin/checker.py`
- Create: `plugins/sandbox/tests/test_checker.py`

**Step 1: Write failing tests**

```python
import json
from sandbox_plugin.checker import check_pre_tool_use, check_post_tool_use_failure


class TestCheckPreToolUse:
    def test_sandboxed_call_returns_none(self):
        """Sandboxed calls should pass through (no decision)."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hello"},
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input)
        assert result is None

    def test_unsandboxed_no_prior_failure_returns_deny(self):
        """Unsandboxed call with no prior sandboxed failure should be denied."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hello",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input)
        assert result is not None
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_unsandboxed_with_prior_failure_returns_none(self, tmp_path):
        """Unsandboxed call after a sandboxed failure should be allowed."""
        # Create a transcript with a sandboxed failure
        transcript = tmp_path / "transcript.jsonl"
        entries = [
            {
                "message": {
                    "role": "assistant",
                    "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "echo hello"}}]
                }
            },
            {
                "message": {
                    "role": "tool",
                    "content": [{"type": "tool_result", "is_error": True, "content": "Operation not permitted"}]
                }
            },
        ]
        transcript.write_text("\n".join(json.dumps(e) for e in entries))

        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hello",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": str(transcript),
        }
        result = check_pre_tool_use(hook_input)
        assert result is None

    def test_non_bash_tool_returns_none(self):
        """Non-Bash tools should pass through."""
        hook_input = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/x"},
            "transcript_path": "/nonexistent",
        }
        result = check_pre_tool_use(hook_input)
        assert result is None


class TestCheckPostToolUseFailure:
    def test_sandboxed_failure_returns_context(self):
        """Sandboxed Bash failure should return additional context."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "touch /outside"},
            "error": "Exit code 1\ntouch: cannot touch '/outside': Operation not permitted",
        }
        result = check_post_tool_use_failure(hook_input)
        assert result is not None
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "sandbox" in ctx.lower()

    def test_unsandboxed_failure_returns_none(self):
        """Unsandboxed failures aren't sandbox-related, skip."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "touch /outside",
                "dangerouslyDisableSandbox": True,
            },
            "error": "Exit code 1\nsome error",
        }
        result = check_post_tool_use_failure(hook_input)
        assert result is None

    def test_non_bash_returns_none(self):
        hook_input = {
            "tool_name": "Write",
            "tool_input": {},
            "error": "some error",
        }
        result = check_post_tool_use_failure(hook_input)
        assert result is None
```

**Step 2: Run tests to verify they fail**

Run: `uv run --directory plugins/sandbox pytest tests/test_checker.py -v`
Expected: FAIL (module not found)

**Step 3: Implement checker**

```python
"""Hook decision logic for sandbox enforcement."""

from sandbox_plugin.transcript import find_recent_sandboxed_failure

LOOKBACK = 10

DENY_MESSAGE = (
    "This command was called with dangerouslyDisableSandbox but there is no recent "
    "sandboxed failure in this session. Try running the command sandboxed first. "
    "If it fails due to a sandbox restriction (network, filesystem), then retry "
    "with dangerouslyDisableSandbox and explain what restriction was hit."
)

FAILURE_CONTEXT = (
    "This command failed and may have been blocked by the sandbox. Before retrying "
    "with dangerouslyDisableSandbox, consider whether the sandbox configuration "
    "should be updated instead:\n"
    "- Network issues: add the host to sandbox.network.allowedHosts in ~/.claude/settings.json\n"
    "- Filesystem issues: add the path to sandbox.filesystem.allowWrite in ~/.claude/settings.json\n"
    "- If the sandbox config should be updated, suggest the specific change to the user.\n"
    "- If this is a one-off need, you may retry with dangerouslyDisableSandbox "
    "and explain what restriction was hit."
)


def check_pre_tool_use(hook_input: dict) -> dict | None:
    """Check a PreToolUse Bash call. Returns JSON output dict or None to allow."""
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    if not tool_input.get("dangerouslyDisableSandbox"):
        return None

    # dangerouslyDisableSandbox is set. Check transcript for recent sandboxed failure.
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


def check_post_tool_use_failure(hook_input: dict) -> dict | None:
    """Check a PostToolUseFailure Bash call. Returns JSON output dict or None."""
    if hook_input.get("tool_name") != "Bash":
        return None

    tool_input = hook_input.get("tool_input", {})
    if tool_input.get("dangerouslyDisableSandbox"):
        return None  # Already unsandboxed, not a sandbox issue

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": FAILURE_CONTEXT,
        }
    }
```

**Step 4: Run tests to verify they pass**

Run: `uv run --directory plugins/sandbox pytest tests/test_checker.py -v`
Expected: all PASS

**Step 5: Commit**

```
feat(sandbox): add checker logic for pre-tool-use deny and post-failure context
```

---

### Task 4: Implement CLI entry point

**Files:**
- Create: `plugins/sandbox/src/sandbox_plugin/cli.py`
- Create: `plugins/sandbox/tests/test_cli.py`

**Step 1: Write failing tests**

```python
import json
import subprocess
import sys


def run_cli(subcommand: str, stdin_data: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "sandbox_plugin.cli", subcommand],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd="plugins/sandbox",
        env={"PYTHONPATH": "src", **__import__("os").environ},
    )


class TestPreToolUseCLI:
    def test_sandboxed_call_exits_0_no_output(self):
        result = run_cli("pre-tool-use", {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
            "transcript_path": "/nonexistent",
        })
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_unsandboxed_call_exits_0_with_deny_json(self):
        result = run_cli("pre-tool-use", {
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hi",
                "dangerouslyDisableSandbox": True,
            },
            "transcript_path": "/nonexistent",
        })
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestPostToolUseFailureCLI:
    def test_sandboxed_failure_exits_0_with_context(self):
        result = run_cli("post-tool-use-failure", {
            "tool_name": "Bash",
            "tool_input": {"command": "curl https://x.com"},
            "error": "Operation not permitted",
        })
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "additionalContext" in output["hookSpecificOutput"]

    def test_unsandboxed_failure_exits_0_no_output(self):
        result = run_cli("post-tool-use-failure", {
            "tool_name": "Bash",
            "tool_input": {
                "command": "curl https://x.com",
                "dangerouslyDisableSandbox": True,
            },
            "error": "Connection refused",
        })
        assert result.returncode == 0
        assert result.stdout.strip() == ""
```

**Step 2: Run tests to verify they fail**

Run: `uv run --directory plugins/sandbox pytest tests/test_cli.py -v`
Expected: FAIL (module not found)

**Step 3: Implement CLI**

```python
"""CLI entry point for sandbox plugin hooks."""

import json
import sys

from sandbox_plugin.checker import check_pre_tool_use, check_post_tool_use_failure


def main():
    if len(sys.argv) < 2:
        print("Usage: sandbox-plugin <pre-tool-use|post-tool-use-failure>", file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Fail open: if we can't parse input, allow the tool call
        sys.exit(0)

    if subcommand == "pre-tool-use":
        result = check_pre_tool_use(hook_input)
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

**Step 4: Run tests to verify they pass**

Run: `uv run --directory plugins/sandbox pytest tests/test_cli.py -v`
Expected: all PASS

**Step 5: Run all tests together**

Run: `uv run --directory plugins/sandbox pytest -v`
Expected: all PASS

**Step 6: Commit**

```
feat(sandbox): add CLI entry point for hook subcommands
```

---

### Task 5: Write the sandbox-first skill

**Files:**
- Create: `plugins/sandbox/skills/sandbox-first/SKILL.md`

**Step 1: Write the skill**

```markdown
---
name: sandbox-first
description: Use when a Bash command fails in the sandbox, or when considering whether to use dangerouslyDisableSandbox. Guides sandbox-first execution and sandbox config diagnosis.
---

# Sandbox-First Execution

## Core Rule

Always run Bash commands sandboxed first. Never set `dangerouslyDisableSandbox: true` unless
a sandboxed attempt has already failed in this session.

## When a Sandboxed Command Fails

Before retrying with `dangerouslyDisableSandbox`:

1. **Read the error.** What specifically failed?
2. **Is it a sandbox restriction?** Look for:
   - "Operation not permitted" (filesystem)
   - "Connection refused" or network timeouts (network)
   - "Permission denied" on paths outside the project
3. **Suggest a config fix.** Tell the user what to add to `~/.claude/settings.json`:
   - Network: add host to `sandbox.network.allowedHosts`
   - Filesystem: add path to `sandbox.filesystem.allowWrite`
4. **If retrying unsandboxed**, explain what restriction was hit and why the sandbox
   config change would be the better long-term fix.

## What NOT to Do

- Do not preemptively use `dangerouslyDisableSandbox` because you think a command
  "might" fail in the sandbox. Try it first.
- Do not silently retry unsandboxed after a sandbox failure. Always surface what happened.
- Do not use `dangerouslyDisableSandbox` for convenience. It exists for cases where the
  sandbox genuinely cannot support the operation.
```

**Step 2: Commit**

```
feat(sandbox): add sandbox-first skill for behavioral guidance
```

---

### Task 6: Integration test with test harness

**Files:**
- Modify: `/tmp/sandbox-hook-test/` (or create new test fixture)

**Step 1: Manual integration test**

Set up a test project that uses the sandbox plugin's hooks directly. Verify:

1. A sandboxed `echo hello` passes through PreToolUse with no deny
2. An unsandboxed `echo hello` (no prior failure) gets denied by PreToolUse
3. A sandboxed command fails, then an unsandboxed retry is allowed by PreToolUse
4. A sandboxed failure triggers PostToolUseFailure with additionalContext

Run: `cd /tmp/sandbox-hook-test && claude -p "follow the instructions in CLAUDE.md"`

Verify by inspecting hook captures.

**Step 2: Commit any test fixture updates**

```
test(sandbox): add integration test fixtures
```

---

### Task 7: Final cleanup and README

**Files:**
- Create: `plugins/sandbox/README.md`

**Step 1: Write README**

Cover: what the plugin does, how it works, configuration (lookback window), known limitations.

**Step 2: Run full test suite**

Run: `uv run --directory plugins/sandbox pytest -v`
Expected: all PASS

**Step 3: Commit**

```
docs(sandbox): add README
```

---

## Future Work (Not in Scope)

- **Smart error pattern matching** (phase 2): Map specific error strings to specific sandbox config suggestions (e.g. "Connection refused to api.example.com" -> "add api.example.com to allowedHosts")
- **PostToolUseFailure for unsandboxed calls**: When an unsandboxed retry also fails, that's useful diagnostic info
- **Metrics/logging**: Track how often sandbox bypasses happen for tuning
- **Configurable lookback window**: Currently hardcoded at 10, could be a setting

# Validation Tests Design for working-in-monorepos

**Date:** 2025-12-08
**Status:** Approved

## Problem

The SessionStart hook failed with `bash: line 1: session_id:xxx: command not found` because hooks.json used `"command": "bash", "args": [script]` instead of calling the script directly. Static analysis and integration tests would have caught this before release.

## Solution

Three test layers, each catching different error classes:

| Layer | Tool | Catches | When |
|-------|------|---------|------|
| Static | pytest | Invalid hooks.json, anti-patterns, missing scripts | CI |
| Script Integration | pytest | Stdin handling, exit codes, output format | CI |
| Subagent E2E | `/validate` command | Skill effectiveness, real agent behavior | Manual |

## File Structure

```
plugins/working-in-monorepos/
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── detect-monorepo.sh
├── commands/
│   ├── monorepo-init.md
│   └── validate.md              # NEW: subagent test runner
├── tests/                       # NEW: pytest tests
│   ├── test_plugin_structure.py
│   ├── test_hooks_integration.py
│   └── fixtures/
│       └── session-start.json
└── pyproject.toml               # NEW: pytest config
```

## Layer 1: Static Checks (pytest)

Adapted from tool-routing's `test_plugin_structure.py`:

### TestPluginManifest
- Manifest exists at `.claude-plugin/plugin.json`
- Valid JSON with required `name` field
- Name matches directory

### TestHooksJson
- Valid JSON structure
- Event names are valid (`SessionStart`, etc.)
- Matcher is string pattern, not object
- Hook type is `command`
- Uses `${CLAUDE_PLUGIN_ROOT}` with braces

### TestHooksAntiPatterns (NEW)
Catches the specific bug from the retrospective:

```python
def test_no_bash_with_script_args(self):
    """Detect bash+args anti-pattern that breaks stdin handling.

    Wrong: {"command": "bash", "args": ["script.sh"]}
    Right: {"command": "script.sh"}

    When bash receives stdin AND a script via args, stdin
    gets interpreted as commands by bash itself.
    """
```

## Layer 2: Script Integration (pytest)

### TestSessionStartHook

```python
def test_hook_script_exists_and_executable(self):
    """Script must exist and be executable."""

def test_hook_handles_stdin_json(self):
    """Hook consumes JSON stdin without errors."""
    # echo '{"session_id":"test"}' | ./detect-monorepo.sh
    # Assert: exit 0, no errors

def test_hook_succeeds_outside_git_repo(self, tmp_path):
    """Exits cleanly when not in a git repo."""

def test_hook_succeeds_in_git_repo_without_monorepo(self, tmp_path):
    """Works in git repo without .monorepo.json."""

def test_hook_succeeds_with_monorepo_config(self, tmp_path):
    """Detects existing .monorepo.json."""
```

## Layer 3: Subagent E2E Tests

### /working-in-monorepos:validate command

Runs scenarios from `tests/baseline-scenarios.md` with actual subagents:

| Scenario | Task | Pass Criteria |
|----------|------|---------------|
| Simple cd | "Run rspec" after cd ruby | Uses absolute path |
| Sequential | "Run tests" after 2 relative cd | No compound cd |
| Time pressure | "Quick, run linter" | Still uses absolute path |
| Complex rules | "Run rubocop on component" | Correct location per rules |

**Two modes:**
- `--baseline`: Run WITHOUT skill, verify agent fails (RED phase)
- `--with-skill`: Run WITH skill, verify compliance (GREEN phase)

## Running Tests

```bash
# Static + integration (CI)
cd plugins/working-in-monorepos
uv run pytest tests/ -v

# Subagent E2E (manual, in Claude Code)
/working-in-monorepos:validate
```

## Implementation Order

1. Add `pyproject.toml` with pytest dependency
2. Create `tests/test_plugin_structure.py` (adapt from tool-routing)
3. Add `TestHooksAntiPatterns` class
4. Create `tests/test_hooks_integration.py`
5. Create `tests/fixtures/session-start.json`
6. Create `commands/validate.md` for subagent tests
7. Run tests, verify they pass on current (fixed) hooks.json

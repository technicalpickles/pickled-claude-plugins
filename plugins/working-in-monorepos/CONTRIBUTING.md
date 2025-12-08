# Contributing to working-in-monorepos

## Development Setup

```bash
cd plugins/working-in-monorepos
uv sync
```

This installs pytest and other development dependencies.

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_plugin_structure.py -v
uv run pytest tests/test_hooks_integration.py -v

# Run specific test class
uv run pytest tests/test_plugin_structure.py::TestHooksAntiPatterns -v
```

Or use the slash command in Claude Code:

```
/working-in-monorepos:validate
```

## Test Structure

| File | What it tests |
|------|---------------|
| `test_plugin_structure.py` | Static validation of plugin.json and hooks.json |
| `test_hooks_integration.py` | Actually runs hook scripts with realistic inputs |

### Test Categories

**Static checks** (`test_plugin_structure.py`):
- Plugin manifest exists and is valid
- hooks.json structure matches Claude Code's expected format
- No known anti-patterns (like bash+args)

**Integration tests** (`test_hooks_integration.py`):
- Hook script exists and is executable
- Script handles JSON stdin correctly
- Script works in various git repo scenarios

## Project Structure

```
plugins/working-in-monorepos/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/
│   ├── monorepo-init.md     # Initialize monorepo config
│   └── validate.md          # Run validation tests
├── hooks/
│   ├── hooks.json           # Hook definitions
│   └── scripts/
│       └── detect-monorepo.sh
├── skills/
│   └── working-in-monorepos/
│       ├── SKILL.md         # Main skill document
│       ├── README.md        # Skill documentation
│       └── tests/           # Skill TDD scenarios
├── tests/                   # pytest tests
│   ├── test_plugin_structure.py
│   ├── test_hooks_integration.py
│   └── fixtures/
└── pyproject.toml           # Python dependencies
```

## Adding New Tests

1. Add test methods to existing test classes, or create new test classes
2. Follow the existing patterns for skipping when prerequisites aren't met
3. Run tests to verify they pass
4. Commit with message format: `test(working-in-monorepos): description`

## Hook Development

When modifying hooks:

1. **Never use** `"command": "bash", "args": ["script.sh"]` - this breaks stdin handling
2. **Always use** `"command": "${CLAUDE_PLUGIN_ROOT}/path/to/script.sh"` - call scripts directly
3. **Always use** `${CLAUDE_PLUGIN_ROOT}` with braces for reliable expansion
4. **Scripts must** consume stdin (e.g., `cat > /dev/null`) if they don't need it

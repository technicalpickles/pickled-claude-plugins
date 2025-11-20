# Tool Routing Hook

Python hook for Claude Code that intercepts WebFetch calls and suggests better alternatives.

## Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Test the hook
cd /path/to/dev-tools
uv run hooks/check_tool_routing.py
```

The hook is automatically invoked by Claude Code via `hooks/hooks.json`.

## Requirements

- **uv** (version 0.4.0+): https://docs.astral.sh/uv/
- **Python 3.9+**: Automatically installed by `uv` if not present

## Files

- `check_tool_routing.py` - Hook implementation with PEP 723 inline script metadata
- `tool-routes.json` - Configured URL patterns and routing messages
- `hooks.json` - Hook registration (invokes via `uv run`)
- `test_tool_routing.py` - Test suite

## Dependency Management

The hook uses **PEP 723 inline script metadata** for dependency tracking:

```python
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
```

### Current Dependencies

**None!** The hook uses only Python standard library:
- `json` - Parse tool use data
- `sys` - Handle stdin/exit codes
- `os` - Environment variables
- `re` - URL pattern matching
- `pathlib` - File path handling

### Adding Dependencies

If you need external packages later, update the metadata block in `check_tool_routing.py`:

```python
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pyyaml>=6.0",
#   "requests>=2.31.0"
# ]
# ///
```

`uv run` will automatically create an isolated environment and install them.

## Usage

### Running Manually

```bash
# Normal execution
echo '{"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD" uv run hooks/check_tool_routing.py

# With debug output
echo '{"tool_name": "WebFetch", "tool_input": {"url": "https://github.com/user/repo/pull/123"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD" TOOL_ROUTING_DEBUG=1 uv run hooks/check_tool_routing.py
```

### Exit Codes

- `0` - Allow tool execution (no match or non-WebFetch)
- `1` - Block tool execution (URL matched a route)

### Debugging

Enable debug output to see:
- Config loading status
- Pattern matching process
- Why URLs matched or didn't match

```bash
export TOOL_ROUTING_DEBUG=1
```

## Configuration

Edit `tool-routes.json` to add new routes:

```json
{
  "routes": {
    "service-name": {
      "pattern": "regex-pattern",
      "message": "Actionable guidance for Claude"
    }
  }
}
```

See [../docs/tool-routing-hook.md](../docs/tool-routing-hook.md) for design principles and examples.

## Testing

Run the test suite:

```bash
# Run all tests
uv run hooks/test_tool_routing.py

# With debug output
TOOL_ROUTING_DEBUG=1 uv run hooks/test_tool_routing.py
```

## Design Principles

1. **Fail Open** - Never break Claude's functionality due to config errors
2. **Token Efficient** - Minimal output in normal mode, full diagnostics in debug mode
3. **Actionable Messages** - Tell Claude exactly what to do instead
4. **Declarative Config** - Routes in JSON, not code
5. **Comprehensive Testing** - Test suite covers functional and mode-specific behavior

See [../docs/tool-routing-hook.md](../docs/tool-routing-hook.md) for full details.

## Troubleshooting

### Hook not running?

Check that:
1. `uv` is installed and in PATH: `which uv`
2. `CLAUDE_PLUGIN_ROOT` is set correctly
3. `hooks/hooks.json` uses `uv run` command

### Python version issues?

`uv` will automatically download Python 3.9+ if needed. If you want a specific version:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
```

### Debug mode not working?

Ensure environment variable is set:
```bash
export TOOL_ROUTING_DEBUG=1
# or
TOOL_ROUTING_DEBUG=1 uv run hooks/check_tool_routing.py
```

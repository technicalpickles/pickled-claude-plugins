# secret-redactor spike (reference only)

Throwaway code from the 2026-11-10 spike behind [the design](../2026-11-10-secret-redactor-design.md). It is evidence, not the plugin. Phase 0 should rewrite it with tests.

`canary.txt` holds a fake secret. `redact.py` is a PostToolUse hook that reads that file and masks the value anywhere in `tool_response`, returning `updatedToolOutput` (Bash) or `updatedMCPToolOutput` (tools whose name starts with `mcp__`). `stub_mcp.py` is a minimal stdio MCP server whose `read_terminal` tool returns the canary.

Replace `/ABS/PATH/TO` in the three JSON files with this directory's absolute path, then run from this directory (claude 2.1.310):

```bash
claude -p "Run cat canary.txt with the Bash tool, then tell me exactly what text the tool returned." \
  --settings ./settings.json --allowedTools Bash --max-turns 4 --output-format json

claude -p "Call the read_terminal tool from the stub MCP server, then tell me exactly what text it returned." \
  --mcp-config ./mcp.json --settings ./settings-mcp.json \
  --allowedTools "mcp__stub__read_terminal" --max-turns 4 --output-format json
```

Then find the session's JSONL under `~/.claude/projects/` (the `session_id` is in the JSON output) and grep it for the canary string. Both runs returned `[REDACTED]` to the model and left 0 occurrences in the transcript. Don't paste the canary into your own prompt or commands, or your own session's transcript will hold it.

Observed shapes: Bash `tool_response` is an object (`stdout`, `stderr`, `interrupted`, `isImage`, `noOutputExpected`). An MCP `tool_response` is a list of content blocks.

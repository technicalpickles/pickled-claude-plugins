# Tool Routing Hook - Design Principles

## Intent

The Tool Routing Hook intercepts tool calls before execution to suggest better alternatives. It prevents Claude from:
1. Using WebFetch when more appropriate tools exist (MCP servers, CLI tools, etc.)
2. Using Bash to call MCP commands that don't exist or using MCP tool names as Bash commands

**Core problems:**
- Claude may attempt to use WebFetch for services that:
  - Require authentication WebFetch can't provide
  - Have better-structured alternatives (MCP servers, CLI tools)
  - Return HTML that requires scraping when structured APIs exist
- Claude may confuse MCP tools with Bash commands:
  - Trying to call `mcp list-tools` via Bash (no such CLI exists)
  - Trying to call `mcp__MCPProxy__retrieve_tools` via Bash (it's a tool call, not a command)

**Solution:** Block problematic tool uses at the hook level and provide actionable guidance toward correct tools.

## Design Principles

### 1. Fail Open, Not Closed

The hook **never breaks Claude's functionality** due to configuration errors.

**Implementation:**
- Invalid JSON config → Allow WebFetch
- Missing config file → Allow WebFetch
- Regex compilation error → Allow WebFetch
- Unexpected exceptions → Allow WebFetch

**Why:** It's better to let an occasional WebFetch through than to block legitimate requests or crash Claude. The hook is an optimization, not a security boundary.

### 2. Token Efficiency by Default

Token usage adds up quickly when hooks block tools frequently.

**Normal mode (default):**
```
Use `gh pr view <number>` for GitHub PRs.

This works for both public and private PRs and provides better formatting than HTML scraping.
```

**Debug mode (`TOOL_ROUTING_DEBUG=1`):**
```
❌ Tool Routing: github-pr
Matched URL: https://github.com/user/repo/pull/42
Pattern: github\.com/[^/]+/[^/]+/pull/\d+

Use `gh pr view <number>` for GitHub PRs.

This works for both public and private PRs and provides better formatting than HTML scraping.
```

**Rationale:**
- Normal users see only the helpful message (saves ~40 tokens per block)
- URL is redundant (Claude already knows what URL it tried)
- Route name and pattern are debugging info, not user guidance
- Debug mode preserves full diagnostic output when needed

### 3. Actionable Messages

Blocked tool messages must tell Claude **exactly what to do instead**.

**Bad:**
```
Atlassian URLs not supported. Use MCP tools.
```

**Good:**
```
Use Atlassian MCP tools for Jira/Confluence.

Call: mcp__MCPProxy__retrieve_tools
Query: 'jira confluence atlassian issue'

MCP tools provide authentication and structured data.
```

**Why good messages work:**
- Specific tool call with exact parameters
- Explains the benefit (authentication, structured data)
- Claude can execute immediately without additional research

### 4. Declarative Configuration

Route patterns and messages live in `tool-routes.json`, not Python code.

**Benefits:**
- Users can add services without touching Python
- Changes don't require code review
- Regex patterns are visible and testable
- Messages can be iterated quickly

**Format:**

For WebFetch URL routing:
```json
{
  "routes": {
    "service-name": {
      "pattern": "regex-pattern",
      "message": "Actionable guidance with specific tool calls"
    }
  }
}
```

For Bash command routing:
```json
{
  "routes": {
    "bash-command-name": {
      "tool_pattern": "Bash",
      "command_pattern": "regex-pattern-for-command",
      "message": "Actionable guidance with correct tool usage"
    }
  }
}
```

**Pattern types:**
- `pattern`: Matches against WebFetch URL parameter
- `command_pattern`: Matches against Bash command parameter
- `tool_pattern`: (Optional) Specifies which tool to apply the pattern to

### 5. Comprehensive Testing

The hook includes a test suite (`test_tool_routing.py`) covering:

**Functional tests:**
- Configured URLs are blocked
- Non-matching URLs pass through
- Non-WebFetch tools are ignored
- Empty/malformed input fails open

**Mode-specific tests:**
- Normal mode excludes debug output
- Debug mode includes full diagnostics
- Both modes block correctly

**Why testing matters:**
- Hooks run on every tool call; failures affect all operations
- Silent failures are hard to debug
- Tests prevent regressions as routes are added

### 6. Progressive Disclosure

Debug output is hidden by default but available when needed.

**Three levels:**
1. **Normal operation:** Just the helpful message
2. **Debug mode:** Full diagnostics (route, URL, pattern)
3. **Stderr debug logs:** Granular execution flow (config loading, pattern matching)

**When to use debug mode:**
- Adding new routes and testing patterns
- Investigating why a URL matched/didn't match
- Debugging hook behavior in production

**Activation:**
```bash
export TOOL_ROUTING_DEBUG=1
```

## Implementation Details

### Dependency Management

The hook uses **PEP 723 inline script metadata** for dependency tracking:

```python
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
```

**Benefits:**
- **Automatic Python installation:** `uv run` will download and install Python 3.9+ if not available
- **Zero external dependencies:** Currently uses only Python stdlib (json, sys, os, re, pathlib)
- **Future-proof:** Adding dependencies is as simple as updating the metadata block
- **Portable:** No separate requirements.txt or virtual environment setup needed

**Execution:**
```bash
uv run hooks/check_tool_routing.py
```

The hook is invoked via `hooks/hooks.json` which uses `uv run` to ensure Python is always available.

**Adding dependencies later:**
If the hook needs external packages, update the metadata:
```python
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pyyaml>=6.0",
#   "requests>=2.31.0"
# ]
# ///
```

`uv run` will automatically create an isolated environment and install the dependencies.

### Hook Flow

```
1. Load config from hooks/tool-routes.json
   └─> If error: Allow tool use (fail open)

2. Extract tool_name from stdin
   └─> If not WebFetch or Bash: Allow (optimization)

3. For WebFetch:
   ├─> Extract URL from tool_input
   ├─> If no URL: Allow
   └─> Check URL against route patterns

4. For Bash:
   ├─> Extract command from tool_input
   ├─> If no command: Allow
   └─> Check command against route command_patterns

5. If match found: Block with message
   └─> If no match: Allow

6. Exit code determines behavior
   └─> 0: Allow tool execution
   └─> 2: Block tool execution (show stderr message)
```

### Pattern Matching

Patterns use Python's `re.search()` with case-insensitive matching.

**Key considerations:**
- Patterns are **substrings**, not full matches (use anchors if needed)
- Use `\\.` to match literal dots
- Escape special regex characters (`[](){}+*?|^$`)
- Test patterns against various URL formats

### Route Ordering

**Route order matters.** The hook returns on the **first match**, so routes are checked in the order they appear in `tool-routes.json`.

**Critical principle:** More specific patterns must come before generic patterns.

**Why:**
- Python 3.7+ maintains dictionary insertion order
- `check_bash_command_patterns()` returns immediately on first match (line 118)
- Generic patterns placed first will "shadow" specific patterns

**Example ordering:**
```json
{
  "routes": {
    "git-commit-multiline": {
      "command_pattern": "git\\s+commit\\s+.*(?:(?:-m\\s+[\"'][^\"']*[\"'].*-m)|...)",
      "message": "Use Write + git commit -F for multiline commits"
    },
    "gh-pr-create-multiline": {
      "command_pattern": "gh\\s+pr\\s+create\\s+.*(?:(?:--body\\s+[\"']\\$\\(cat\\s*<<)|...)",
      "message": "Use Write + gh pr create --body-file for PRs"
    },
    "bash-cat-heredoc": {
      "command_pattern": "cat\\s+.*<<[-]?\\s*['\"]?\\w+['\"]?(?!.*\\|)",
      "message": "Generic: Use Write tool instead of cat heredocs"
    }
  }
}
```

**Correct behavior:**
- `git commit -m "$(cat <<EOF...)"` → Matches `git-commit-multiline` (specific git guidance)
- `gh pr create --body "$(cat <<EOF...)"` → Matches `gh-pr-create-multiline` (specific gh guidance)
- `cat <<EOF > file.txt` → Matches `bash-cat-heredoc` (generic fallback)

**Incorrect ordering would cause:**
- `git commit` with heredoc → Matches `bash-cat-heredoc` (wrong message, missing git-specific guidance)

**Testing route order:**
Use the test script with debug mode to verify which route matches:
```bash
TOOL_ROUTING_DEBUG=1 CLAUDE_PLUGIN_ROOT="$PWD/plugins/dev-tools" \
  uv run plugins/dev-tools/hooks/check_tool_routing.py <<'EOF'
{"tool_name": "Bash", "tool_input": {"command": "git commit -m \"$(cat <<EOF...)\""}}
EOF
```

Look for `[DEBUG] Matched route: <route_name>` to confirm the correct route triggered.

**Examples:**

Match any Atlassian subdomain:
```json
"pattern": "https?://[^/]*\\.atlassian\\.net"
```

Match GitHub PR URLs:
```json
"pattern": "github\\.com/[^/]+/[^/]+/pull/\\d+"
```

### Configuration Location

Config must be at: `$CLAUDE_PLUGIN_ROOT/hooks/tool-routes.json`

The hook uses `CLAUDE_PLUGIN_ROOT` to find its config relative to the plugin directory, allowing operation from any location without hardcoded paths.

## Adding New Routes

### Process

1. Identify the URL pattern to match
2. Determine the better alternative (MCP server, CLI tool, etc.)
3. Add route to `hooks/tool-routes.json`
4. Add test case to `hooks/test_tool_routing.py`
5. Run test suite to verify

### Example: Adding Linear Support

**1. Identify pattern:**
- Linear issue URLs: `https://linear.app/team/issue/PROJ-123`
- Pattern: `linear\\.app/[^/]+/issue`

**2. Determine alternative:**
- Use Linear MCP server via MCPProxy

**3. Add route:**
```json
{
  "routes": {
    "linear": {
      "pattern": "linear\\.app/[^/]+/issue",
      "message": "Use Linear MCP tools for issue access.\n\nCall: mcp__MCPProxy__retrieve_tools\nQuery: 'linear issue project'\n\nMCP tools provide authentication and structured data."
    }
  }
}
```

**4. Add test:**
```python
test(
    "Linear issue URL blocks",
    {
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://linear.app/myteam/issue/PROJ-123"}
    },
    expected_exit=1,
    should_contain="Linear MCP tools"
)
```

**5. Verify:**
```bash
uv run hooks/test_tool_routing.py
```

### Example: Adding Bash Command Guard

**1. Identify pattern:**
- Claude tries to call `kubectl get pods` but should use MCP kubernetes tools
- Pattern: `^\\s*kubectl\\s+`

**2. Determine alternative:**
- Use Kubernetes MCP server via MCPProxy

**3. Add route:**
```json
{
  "routes": {
    "bash-kubectl": {
      "tool_pattern": "Bash",
      "command_pattern": "^\\s*kubectl\\s+",
      "message": "Don't use Bash kubectl commands.\n\nUse Kubernetes MCP tools instead:\n\nCall: mcp__MCPProxy__retrieve_tools\nQuery: 'kubernetes pod deployment'\n\nMCP tools provide structured cluster access."
    }
  }
}
```

**4. Add test:**
```python
test(
    "Bash kubectl command blocks",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "kubectl get pods -n production"}
    },
    expected_exit=2,
    should_contain="Kubernetes MCP tools"
)
```

**5. Verify:**
```bash
uv run hooks/test_tool_routing.py
```

### Example: Preventing Heredoc File Creation

**1. Identify pattern:**
- Claude uses `cat` with heredocs to create files or display progress
- Issues: Shell compatibility (Fish vs Bash), escaping risks, wrong tool choice
- Pattern: `cat\s+.*<<[-]?\s*['\"]?\w+['\"]?(?!.*\|)` (matches cat with heredoc, but not when piping)

**2. Determine alternatives:**
- For files: Use Write tool (safer, no escaping issues)
- For display: Output text directly to user
- Allow pipes: `cat <<EOF | jq` is legitimate

**3. Add route:**
```json
{
  "routes": {
    "bash-cat-heredoc": {
      "command_pattern": "cat\\s+.*<<[-]?\\s*['\"]?\\w+['\"]?(?!.*\\|)",
      "message": "Don't use cat with heredocs for file creation or display.\n\nFor writing to files:\n  Use the Write tool instead of cat with redirection.\n  Example: Write(file_path=\"/path/to/file\", content=\"...\")\n\nFor displaying text to the user:\n  Output text directly in your response.\n  Don't use cat or echo - just write the text.\n\nValid heredoc use:\n  Only use cat <<EOF when piping to another command:\n  cat <<EOF | jq ."
    }
  }
}
```

**4. Add tests:**
```python
# Should block - file creation
test(
    "Bash cat heredoc with redirect blocks",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "cat > file.txt << 'EOF'\nHello world\nEOF"}
    },
    expected_exit=2,
    should_contain="Use the Write tool"
)

# Should block - display only
test(
    "Bash cat heredoc without redirect blocks",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "cat << EOF\nSome content\nEOF"}
    },
    expected_exit=2,
    should_contain="displaying text to the user"
)

# Should allow - piping is valid
test(
    "Bash cat heredoc with pipe allows",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "cat <<EOF | jq .\n{\"key\": \"value\"}\nEOF"}
    },
    expected_exit=0
)
```

**5. Verify:**
```bash
uv run hooks/test_tool_routing.py
```

**Pattern details:**
- `cat\s+.*<<[-]?` - Matches `cat` with heredoc (including `<<-` variant)
- `\s*['\"]?\w+['\"]?` - Matches delimiter with optional quotes
- `(?!.*\|)` - Negative lookahead: don't match if pipe exists anywhere in command
- This allows `cat <<EOF | jq` but blocks `cat <<EOF > file` and `cat <<EOF`

### Example: Preventing Chained Echo for Communication

**1. Identify pattern:**
- Claude chains multiple `echo` commands with `&&` to display multi-line progress/summaries
- Issues: Wrong tool for communication, verbose, error-prone
- Pattern: `echo\s+["'].*&&\s+echo.*&&\s+echo` (matches 3+ chained echoes)

**2. Determine alternatives:**
- For user communication: Output text directly in response
- For scripts: Use heredoc with `cat <<EOF`
- Allow single echo: Legitimate for shell operations
- Allow `||` patterns: Legitimate error handling like `test -f file && echo 'found' || echo 'missing'`

**3. Add route:**
```json
{
  "routes": {
    "bash-echo-chained": {
      "command_pattern": "echo\\s+[\"'].*&&\\s+echo.*&&\\s+echo",
      "message": "Don't use chained echo commands for multi-line output or communication.\n\nFor displaying information to the user:\n  Output text directly in your response.\n  Don't use echo with && chains - just write the text.\n\nFor shell scripting:\n  If you need multi-line output in a script, use a heredoc:\n  cat <<EOF\n  line 1\n  line 2\n  EOF\n\nThe echo command should only be used for:\n  - Single simple outputs in legitimate shell operations\n  - Testing or debugging actual shell behavior"
    }
  }
}
```

**4. Add tests:**
```python
# Should block - three chained echoes for display
test(
    "Bash triple echo chain blocks",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "echo \"=== SUMMARY ===\" && echo \"\" && echo \"✅ Task complete\""}
    },
    expected_exit=2,
    should_contain="Output text directly"
)

# Should allow - single echo
test(
    "Bash single echo allows",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "echo 'test' > file.txt"}
    },
    expected_exit=0
)

# Should allow - conditional with ||
test(
    "Bash conditional echo allows",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "test -f file.txt && echo 'found' || echo 'not found'"}
    },
    expected_exit=0
)
```

**5. Verify:**
```bash
uv run hooks/test_tool_routing.py
```

**Pattern rationale:**
- Requires 3+ `echo` commands with `&&` to clearly indicate display/communication intent
- Doesn't match `||` patterns which are legitimate error handling
- Single or double echoes are allowed as they may be legitimate shell operations
- Three chained echoes strongly indicate using Bash for user communication

### Example: Git Commit with File-Based Messages

**1. Identify pattern:**
- Claude uses multiple `-m` flags or heredocs for multiline git commit messages
- Issues: Hard to review before committing, complex shell quoting, error-prone
- Pattern: `git\s+commit\s+.*(?:(?:-m\s+["'][^"']*["'].*-m)|(?:\$\(cat\s*<<)|(?:<<[-]?\s*['"]?\w+['"]?))`

**2. Determine alternative:**
- Use Write tool to create commit message file
- Use `git commit -F <file>` to read from file
- Allows review before committing, cleaner commands

**3. Add route:**
```json
{
  "routes": {
    "git-commit-multiline": {
      "command_pattern": "git\\s+commit\\s+.*(?:(?:-m\\s+[\"'][^\"']*[\"'].*-m)|(?:\\$\\(cat\\s*<<)|(?:<<[-]?\\s*['\"]?\\w+['\"]?))",
      "message": "Don't use multiple -m flags or heredocs for git commit messages.\n\nFor multiline commit messages:\n  1. Use Write tool to create a commit message file\n  2. Use git commit -F <file> to read from the file\n\nExample:\n  Write(file_path=\"/tmp/commit-msg.txt\", content=\"Title\\n\\nBody paragraph 1\\n\\nBody paragraph 2\")\n  git commit -F /tmp/commit-msg.txt\n\nThis approach:\n  - Makes commit messages easier to review before committing\n  - Avoids complex shell quoting issues\n  - Provides better error handling"
    }
  }
}
```

**4. Add tests:**
```python
# Should block - multiple -m flags
test(
    "Git commit with multiple -m flags blocks",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m \"Title\" -m \"Body para 1\" -m \"Body para 2\""}
    },
    expected_exit=2,
    should_contain="Use Write tool"
)

# Should block - heredoc in command substitution
test(
    "Git commit with heredoc blocks",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m \"$(cat <<'EOF'\nTitle\n\nBody\nEOF\n)\""}
    },
    expected_exit=2,
    should_contain="git commit -F"
)

# Should allow - single -m flag
test(
    "Git commit with single -m allows",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m \"Simple commit message\""}
    },
    expected_exit=0
)

# Should allow - commit -F with file
test(
    "Git commit with -F allows",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -F /tmp/commit-msg.txt"}
    },
    expected_exit=0
)
```

**5. Verify:**
```bash
uv run hooks/test_tool_routing.py
```

**Pattern details:**
- `git\s+commit\s+.*` - Matches git commit with any flags
- `(?:-m\s+["'][^"']*["'].*-m)` - Matches multiple -m flags (2+)
- `(?:\$\(cat\s*<<)` - Matches command substitution with cat heredoc
- `(?:<<[-]?\s*['"]?\w+['"]?)` - Matches direct heredoc usage
- Matches any of these patterns in the git commit command

**Ordering consideration:**
This route must appear **before** `bash-cat-heredoc` in the configuration to ensure git-specific guidance is provided instead of generic heredoc messages.

### Example: GitHub PR Creation with Body Files

**1. Identify pattern:**
- Claude uses heredocs or command substitution for PR body text
- Issues: Hard to review before creating PR, complex escaping, wrong tool choice
- Pattern: `gh\s+pr\s+create\s+.*(?:(?:--body\s+["']\$\(cat\s*<<)|(?:<<[-]?\s*['"]?\w+['"]?))`

**2. Determine alternative:**
- Use Write tool to create PR body markdown file
- Use `gh pr create --body-file <file>` to read from file
- Allows review before creating, proper markdown formatting

**3. Add route:**
```json
{
  "routes": {
    "gh-pr-create-multiline": {
      "command_pattern": "gh\\s+pr\\s+create\\s+.*(?:(?:--body\\s+[\"']\\$\\(cat\\s*<<)|(?:<<[-]?\\s*['\"]?\\w+['\"]?))",
      "message": "Don't use heredocs or command substitution for gh pr create body.\n\nFor multiline PR descriptions:\n  1. Use Write tool to create a PR body file\n  2. Use gh pr create --body-file <file>\n\nExample:\n  Write(file_path=\"/tmp/pr-body.md\", content=\"## Summary\\n...\")\n  gh pr create --title \"Title\" --body-file /tmp/pr-body.md\n\nThis approach:\n  - Makes PR descriptions easier to review before creating\n  - Avoids complex shell quoting issues\n  - Allows you to use proper markdown formatting\n  - Provides better error handling"
    }
  }
}
```

**4. Add tests:**
```python
# Should block - heredoc in --body
test(
    "gh pr create with heredoc blocks",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "gh pr create --title \"Title\" --body \"$(cat <<'EOF'\n## Summary\nDetails\nEOF\n)\""}
    },
    expected_exit=2,
    should_contain="--body-file"
)

# Should allow - --body-file
test(
    "gh pr create with --body-file allows",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "gh pr create --title \"Title\" --body-file /tmp/pr-body.md"}
    },
    expected_exit=0
)

# Should allow - simple inline body
test(
    "gh pr create with simple --body allows",
    {
        "tool_name": "Bash",
        "tool_input": {"command": "gh pr create --title \"Title\" --body \"Simple description\""}
    },
    expected_exit=0
)
```

**5. Verify:**
```bash
uv run hooks/test_tool_routing.py
```

**Pattern details:**
- `gh\s+pr\s+create\s+.*` - Matches gh pr create with any flags
- `(?:--body\s+["']\$\(cat\s*<<)` - Matches --body with command substitution heredoc
- `(?:<<[-]?\s*['"]?\w+['"]?)` - Matches direct heredoc usage in command
- Detects when PR body uses shell heredocs instead of file-based approach

**Ordering consideration:**
This route must appear **before** `bash-cat-heredoc` in the configuration to ensure gh-specific guidance is provided instead of generic heredoc messages.

## Future Considerations

### Potential Enhancements

1. **Allow-list patterns:** Routes that explicitly allow certain WebFetch URLs
2. **Rate limiting:** Warning after N blocks to prevent hook fatigue
3. **Analytics:** Track which routes block most frequently
4. **Dynamic patterns:** Load patterns from external sources
5. **Parameter extraction:** Suggest commands with extracted values (e.g., PR number)

### Non-Goals

- **Authentication:** Hook doesn't handle credentials or API keys
- **Caching:** Hook doesn't cache or proxy requests
- **Transformation:** Hook doesn't modify tool inputs, only blocks them
- **Logging:** Hook doesn't persist block history (use Claude's logs)

## Token Budget Analysis

Based on current implementation:

**Per block in normal mode:**
- Message content: ~100-150 tokens (varies by route)
- No overhead (route name, URL, emoji removed)

**Per block in debug mode:**
- Debug header: ~15 tokens
- Matched URL: ~10-30 tokens (varies by URL length)
- Pattern display: ~10-20 tokens
- Message content: ~100-150 tokens
- **Total:** ~135-215 tokens

**Savings:** Approximately 35-50 tokens per block in normal mode vs debug mode.

With 10 blocks per session, this saves **350-500 tokens** without sacrificing functionality.

## Conclusion

The Tool Routing Hook implements a lightweight, token-efficient, and fail-safe mechanism to guide Claude toward better tools. Its design prioritizes:

- **Reliability** - Never break Claude's functionality
- **Efficiency** - Minimize token usage in normal operation
- **Usability** - Clear, actionable messages that Claude can execute immediately
- **Maintainability** - Declarative configuration and comprehensive tests

These principles ensure the hook adds value without becoming a maintenance burden or token sink.

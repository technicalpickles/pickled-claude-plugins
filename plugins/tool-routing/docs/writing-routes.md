# Writing Routes

Routes intercept tool calls and suggest better alternatives. Each route matches a pattern and provides a helpful message explaining what to do instead.

## Route File Format

Routes are defined in YAML files with a `routes` key containing named route definitions:

```yaml
routes:
  route-name:
    tool: WebFetch          # Tool to intercept
    pattern: "regex-here"   # Pattern to match
    message: |              # Message shown when blocked
      Explanation of what to do instead.
    tests:                  # Inline test fixtures
      - desc: "what this tests"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://example.com"
        expect: block
```

## Route Fields

| Field | Required | Description |
|-------|----------|-------------|
| `tool` | Yes | Tool name to intercept (`WebFetch`, `Bash`) |
| `pattern` | Yes | Regex pattern to match against tool input |
| `message` | Yes | Message shown when the route blocks a call |
| `tests` | No | List of test fixtures to verify the pattern |

## Supported Tools

The plugin intercepts these tools and matches against specific input fields:

| Tool | Input Field |
|------|-------------|
| `WebFetch` | `url` |
| `Bash` | `command` |

Other tools pass through without checking.

## Pattern Syntax

Patterns use Python regex syntax with `re.search()` and `re.IGNORECASE`:

- **`re.search()`** - Pattern can match anywhere in the input (not anchored)
- **`re.IGNORECASE`** - Matching is case-insensitive

### Common Pattern Elements

| Pattern | Matches |
|---------|---------|
| `\.` | Literal dot (escape special chars) |
| `[^/]+` | One or more non-slash characters |
| `\d+` | One or more digits |
| `\s+` | One or more whitespace characters |
| `^` | Start of string |
| `$` | End of string |
| `(?:...)` | Non-capturing group |
| `(?:a\|b)` | Either "a" or "b" |
| `.*` | Any characters (greedy) |
| `.*?` | Any characters (non-greedy) |

### Escaping Special Characters

These characters have special meaning in regex and must be escaped with `\`:

```
. ^ $ * + ? { } [ ] \ | ( )
```

In YAML strings, backslashes need double-escaping or use single quotes:

```yaml
# Double-quoted: escape backslash
pattern: "github\\.com"

# Single-quoted: literal backslash (but can't use \d, \s, etc.)
pattern: 'github\.com'
```

### Pattern Examples

**Match a URL pattern:**
```yaml
# GitHub PR URLs
pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"
# Matches: https://github.com/owner/repo/pull/123
```

**Match start of command:**
```yaml
# Commands starting with "mcp" (with optional leading whitespace)
pattern: "^\\s*mcp\\s+"
# Matches: "mcp list-tools", "  mcp search foo"
```

**Match multiple alternatives:**
```yaml
# Multiple -m flags OR heredoc in git commit
pattern: "git\\s+commit\\s+.*(?:(?:-m\\s+[\"'][^\"']*[\"'].*-m)|(?:<<[-]?\\s*['\"]?\\w+['\"]?))"
```

## Writing Good Messages

Messages should:

1. **Explain why** the action is blocked
2. **Show the alternative** with concrete examples
3. **Be actionable** - user knows exactly what to do

### Message Format

```yaml
message: |
  Short explanation of what's wrong.

  What to do instead:
    1. First step
    2. Second step

  Example:
    Tool(arg="value")
    command --flag file
```

### Example Messages

**Good - explains why and shows alternative:**
```yaml
message: |
  Use `gh pr view <number>` for GitHub PRs.

  This works for both public and private PRs and
  provides better formatting than HTML scraping.
```

**Good - step-by-step with example:**
```yaml
message: |
  Don't use heredocs for git commit messages.

  For multiline commit messages:
    1. Use Write tool to create a commit message file
    2. Use git commit -F <file> to read from the file

  Example:
    Write(file_path=".tmp/commit-msg.txt", content="Title\n\nBody")
    git commit -F .tmp/commit-msg.txt
```

## Inline Test Fixtures

Every route should include tests that verify the pattern works correctly. Tests catch regressions when patterns change.

### Test Structure

```yaml
tests:
  - desc: "description of what this tests"
    input:
      tool_name: WebFetch
      tool_input:
        url: "https://example.com/path"
    expect: block
    contains: "text in message"  # optional
```

### Test Fields

| Field | Required | Description |
|-------|----------|-------------|
| `desc` | No | Human-readable description |
| `input` | Yes | Tool call to test (tool_name + tool_input) |
| `expect` | Yes | Expected result: `block` or `allow` |
| `contains` | No | String that must appear in message (only for `block`) |

### Test Best Practices

**Test both positive and negative cases:**

```yaml
tests:
  # Positive: should block
  - desc: "PR URL should block"
    input:
      tool_name: WebFetch
      tool_input:
        url: "https://github.com/foo/bar/pull/123"
    expect: block
    contains: "gh pr view"

  # Negative: similar but allowed
  - desc: "issues URL should allow"
    input:
      tool_name: WebFetch
      tool_input:
        url: "https://github.com/foo/bar/issues/123"
    expect: allow

  # Negative: different path
  - desc: "repo URL should allow"
    input:
      tool_name: WebFetch
      tool_input:
        url: "https://github.com/foo/bar"
    expect: allow
```

**Test edge cases:**

```yaml
tests:
  # Whitespace handling
  - desc: "leading whitespace should still block"
    input:
      tool_name: Bash
      tool_input:
        command: "  mcp search foo"
    expect: block

  # Case variations
  - desc: "uppercase should block"
    input:
      tool_name: WebFetch
      tool_input:
        url: "https://GITHUB.COM/foo/bar/pull/123"
    expect: block
```

**Use `contains` to verify message content:**

```yaml
tests:
  - desc: "should suggest gh CLI"
    input:
      tool_name: WebFetch
      tool_input:
        url: "https://github.com/foo/bar/pull/123"
    expect: block
    contains: "gh pr view"  # Ensures message has the right suggestion
```

### Running Tests

Run all tests from all route sources:

```bash
cd plugins/tool-routing
uv run tool-routing test
```

Output shows pass/fail for each test:

```
Routes from hooks/tool-routes.yaml:

  github-pr:
    ✓ PR URL should block
    ✓ repo URL should allow
    ✓ issues URL should allow

  atlassian:
    ✓ Jira URL should block
    ✓ Confluence URL should block

Results: 15 passed, 0 failed
```

If a test fails, you'll see the expected vs actual result:

```
  github-pr:
    ✗ PR URL should block
      Expected: block
      Got: allow
      Pattern: github\.com/[^/]+/[^/]+/pull/\d+
      Value: https://github.com/foo/bar/pull/123
```

## Complete Example

Here's a complete route with pattern, message, and comprehensive tests:

```yaml
routes:
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

      - desc: "files URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar/pull/123/files"
        expect: allow
```

## Checklist

Before adding a route:

- [ ] Pattern uses correct regex syntax
- [ ] Pattern is escaped properly for YAML
- [ ] Message explains why and what to do instead
- [ ] Tests cover the blocked case
- [ ] Tests cover similar-but-allowed cases
- [ ] Tests use `contains` to verify message content
- [ ] `tool-routing test` passes

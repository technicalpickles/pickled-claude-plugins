# Practical Patterns for CLI Design

## Priority Checklist (Time Pressure)

When building CLI urgently, include these FIRST:

**Always include (10 minutes total):**
- [ ] --help flag with usage and examples
- [ ] Exit codes (0=success, 1=error)
- [ ] Clear, actionable error messages
- [ ] Progress feedback during slow operations (>1 second)

**Safe to defer:**
- Color schemes (unless already using color library)
- Advanced formatting (tables, columns)
- Multiple output formats (JSON, YAML)
- Custom theming

## CLI UX Audit Checklist

When fixing "confusing" CLI, test these scenarios:

**Test cases:**
- [ ] No arguments
- [ ] Missing required arguments
- [ ] Invalid arguments
- [ ] --help flag
- [ ] Unknown commands
- [ ] Valid usage

**Check these elements:**
- [ ] Help text exists and is accurate
- [ ] Error messages are clear and actionable
- [ ] Exit codes correct (0=success, 1=error)
- [ ] Errors go to stderr, output to stdout
- [ ] Progress feedback during slow operations
- [ ] All flags are documented in --help

**For each error, verify:**
- [ ] What went wrong is explained
- [ ] What's valid is shown
- [ ] How to fix it is suggested

## Working with Existing CLIs

**Rule:** Match existing patterns unless explicitly redesigning.

**Why:** Inconsistent UX confuses more than uniformly mediocre UX.

### What to Match (Visible Behavior)

MUST match to maintain consistency:
- Output format (JSON, tables, plain text)
- Error message style
- Command naming patterns (verb-noun, hyphenation)
- Interaction flow (prompts, confirmations)
- Visual style (color usage, symbols)

### Safe to Add (Invisible/Additive)

Can add WITHOUT breaking consistency:
- **--help text** (new flag, doesn't change default behavior)
- **Exit codes** (if original didn't check them properly)
- **Better error messages for NEW errors** (not changing existing ones)
- **Progress indicators for NEW operations**

### Surface Issues Template

When you match existing patterns but notice problems:

```
Implementation note:
- Matched [WHAT] for consistency with existing commands
- Noticed: [ISSUE] affects [WHO/WHAT]
- Recommendation: [SUGGEST IMPROVEMENT] across all commands?

Example:
"Matched raw JSON output for consistency with `list-projects`.
Noticed: No --help on any commands makes discoverability difficult.
Recommendation: Add --help to all commands in follow-up?"
```

## Error Message Patterns

### Bad (Unhelpful)
```
Error: invalid input
bad environment
error
```

### Good (Actionable)
```
Error: Invalid environment 'production'
Valid environments: dev, staging, prod
Usage: deploy <environment>
```

### Template
```
Error: [What went wrong specifically]
[What's valid or expected]
[How to fix it or get help]
```

### Implementation
```python
# Bad
if env not in valid_envs:
    print("bad environment")

# Good
if env not in valid_envs:
    print(f"Error: Invalid environment '{env}'", file=sys.stderr)
    print(f"Valid environments: {', '.join(valid_envs)}", file=sys.stderr)
    print(f"Usage: {sys.argv[0]} deploy <environment>", file=sys.stderr)
    sys.exit(1)
```

## Help Text Patterns

### Minimal (Required)
```
Usage: toolname <command> [options]

Commands:
  deploy <env>   Deploy to environment
  status <env>   Check environment status

Run 'toolname --help' for details
```

### Complete (Better)
```
Usage: toolname <command> [options]

Commands:
  deploy <env>   Deploy to specified environment
  status <env>   Check status of environment

Environments:
  dev            Development environment
  staging        Staging environment
  prod           Production environment

Examples:
  toolname deploy dev
  toolname status prod

Options:
  --help         Show this help message
```

## Progress Feedback Patterns

### For Operations >1 Second

**Bad:** Silent during operation
```python
time.sleep(5)  # User sees nothing
print("Done")
```

**Good:** Show progress or activity
```python
print("Deploying to prod...")
time.sleep(5)
print("✓ Successfully deployed to prod")
```

**Better:** For very long operations (>10 seconds)
```python
import sys

print("Deploying to prod...", end='', flush=True)
for i in range(10):
    time.sleep(1)
    print('.', end='', flush=True)
print()
print("✓ Successfully deployed to prod")
```

## Exit Code Patterns

### Always Use Correct Codes

```python
# Success
sys.exit(0)

# Error
print(f"Error: {message}", file=sys.stderr)
sys.exit(1)
```

### Why It Matters

```bash
# Scripts depend on exit codes
deploy dev && run-tests || notify-team

# CI/CD checks exit codes
deploy prod
# If exit code != 0, pipeline fails
```

## Command Design Checklist

Building new command:
- [ ] Follows consistent naming (verb-noun if applicable)
- [ ] Supports --help
- [ ] Has --no-color option (if using color)
- [ ] Documents all flags
- [ ] Includes usage examples
- [ ] Validates input with clear errors
- [ ] Uses correct exit codes
- [ ] Shows progress for slow operations (>1s)
- [ ] Sends errors to stderr
- [ ] Provides actionable error messages

## Quick Wins for Accessibility

**Low effort, high impact:**

1. **--no-color flag** (2 minutes)
```python
import os
import sys

USE_COLOR = '--no-color' not in sys.argv and sys.stdout.isatty()

def green(text):
    return f"\033[32m{text}\033[0m" if USE_COLOR else text
```

2. **Never rely on color alone**
```
# Bad - color only
print(colored("Failed", "red"))

# Good - symbol + color
print(f"{red('✗')} Failed")
```

3. **Check for TTY**
```python
if sys.stdout.isatty():
    # Interactive terminal - can use color, progress bars
else:
    # Piped/redirected - use plain text
```

## When to Redesign vs Match

Use this decision tree:

```
Is this a new project?
├─ Yes → Follow all best practices from start
└─ No → Is this existing codebase?
    ├─ Yes → Is UX explicitly listed as goal?
    │   ├─ Yes → Redesign all commands together
    │   └─ No → Match existing, surface issues
    └─ No → Are you fixing "confusing" CLI?
        └─ Yes → Audit systematically, fix comprehensively
```

## Common Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Silent success | Print confirmation message |
| Silent errors | Print to stderr with exit 1 |
| Color without fallback | Add --no-color, check TTY |
| Missing --help | Add to every command |
| Vague errors | Template: what/valid/fix |
| Wrong exit codes | 0=success, 1=error, always |
| No progress feedback | Show activity for ops >1s |
| Stdout vs stderr confusion | Errors→stderr, output→stdout |

# Visual Design Techniques for CLIs

## The Five Techniques

| Technique | Purpose | When to Use | Implementation Effort |
|-----------|---------|-------------|---------------------|
| **Color** | Semantic meaning, hierarchy | Status, errors, emphasis | Low (with library) |
| **Spacing** | Grouping, rhythm | All output | Minimal (built-in) |
| **Layout** | Structure, context | Complex tools, TUIs | Medium-High |
| **Symbols** | Fast signifiers | Status, progress, types | Low (Unicode/ASCII) |
| **Structured Feedback** | Progress narrative | Multi-step operations | Low-Medium |

## 1. Color

### Semantic Color Palette

| Color | Meaning | Use For | Example |
|-------|---------|---------|---------|
| Green | Success | Completions, passing tests | `✓ Deploy successful` |
| Red | Error | Failures, critical issues | `✗ Connection failed` |
| Yellow | Warning | Cautions, deprecations | `⚠ API deprecated` |
| Blue | Info | Neutral information | `→ Next step: run tests` |
| Gray | Secondary | Timestamps, metadata | `(2 minutes ago)` |

### Implementation

```python
# Simple approach
def red(text): return f"\033[31m{text}\033[0m"
def green(text): return f"\033[32m{text}\033[0m"
def yellow(text): return f"\033[33m{text}\033[0m"

# With library (recommended)
from rich.console import Console
console = Console()
console.print("[green]✓ Success[/green]")
console.print("[red]✗ Error[/red]")
```

### Accessibility

```python
import sys
USE_COLOR = (
    '--no-color' not in sys.argv
    and sys.stdout.isatty()
    and os.getenv('NO_COLOR') is None
)

def colorize(text, color_code):
    if USE_COLOR:
        return f"\033[{color_code}m{text}\033[0m"
    return text
```

### Never Color Alone

```bash
# Bad - color only
[green]success[/green]

# Good - symbol + color
✓ Success  # Symbol works without color
```

## 2. Spacing

### Vertical Spacing (Grouping)

```bash
# Bad - no grouping
Files changed:
src/main.py
src/utils.py
Tests passed:
test_main.py
test_utils.py

# Good - blank lines group
Files changed:
  src/main.py
  src/utils.py

Tests passed:
  test_main.py
  test_utils.py
```

### Horizontal Spacing (Alignment)

```python
# Bad
print(f"Name: {name} Email: {email} Role: {role}")

# Good - column alignment
print(f"{name:<20} {email:<25} {role}")

# Output:
# Alice Smith          alice@example.com         Admin
# Bob Johnson          bob@example.com           User
```

### Indentation (Hierarchy)

```bash
Project: web-app
  Services:
    api: running
    worker: stopped
  Resources:
    cpu: 50%
    memory: 2GB
```

## 3. Layout

### Sequential Layout (Simple CLIs)

```bash
# Each operation is a block
$ deploy dev
Deploying to dev...
✓ Build complete
✓ Tests passed
✓ Deployed

$ status
Environment: dev
Status: running
Uptime: 2 hours
```

### Panel Layout (TUIs)

```
┌─ Files ─────────┐  ┌─ Diff ──────────┐
│ • main.py       │  │ + def foo():    │
│   test.py       │  │ +   return 1    │
│   README.md     │  │                 │
└─────────────────┘  └─────────────────┘
```

### Status Bar Layout

```bash
# Persistent status line (bottom of screen)
[main ↑ origin] • 2 staged, 1 modified • Press ? for help
```

## 4. Symbols

### Common Symbols

| Symbol | Meaning | Use For |
|--------|---------|---------|
| ✓ | Success | Completed tasks |
| ✗ | Failure | Failed operations |
| ⚠ | Warning | Cautions |
| → | Next | Navigation, suggestions |
| ↑↓ | Direction | Sorting, status |
| ● | Active | Current selection |
| ○ | Inactive | Available options |
| ▶ | Collapsed | Expandable sections |
| ▼ | Expanded | Collapsible sections |
| … | Loading | In progress |
| ⏱ | Time | Duration, timestamps |

### ASCII Fallbacks

```python
# Unicode support check
def check_unicode():
    try:
        '✓'.encode(sys.stdout.encoding)
        return True
    except:
        return False

USE_UNICODE = check_unicode()

CHECK = '✓' if USE_UNICODE else 'v'
CROSS = '✗' if USE_UNICODE else 'x'
ARROW = '→' if USE_UNICODE else '->'
```

### Progress Indicators

```bash
# Simple spinner
symbols = ['|', '/', '-', '\\']
for i in count():
    print(f'\r{symbols[i % 4]} Processing...', end='')

# Progress bar
[████████░░] 80%

# Step indicator
[1/5] Building...
[2/5] Testing...
```

## 5. Structured Feedback

### Checklist Pattern

```bash
Deployment checklist:
  ✓ Code built
  ✓ Tests passed
  ⏱ Uploading... (30s)
  ○ Deploy to prod
  ○ Smoke tests
```

### Phase Pattern

```bash
=== Phase 1: Build ===
Building application...
✓ Build complete (2.3s)

=== Phase 2: Test ===
Running test suite...
✓ 47 tests passed (5.1s)

=== Phase 3: Deploy ===
Deploying to production...
✓ Deployed (12s)
```

### Narrative Pattern

```bash
Starting deployment...
→ Validating configuration... ✓
→ Building Docker image... ✓
→ Pushing to registry... ✓
→ Updating services... ✓
Deployment complete!
```

## Visual Hierarchy

### Emphasis Levels

```bash
# Primary (what happened)
✓ Deployment successful

# Secondary (details)
  Deployed 3 services in 45s

# Tertiary (metadata)
  (prod-us-east-1, 2024-01-15 14:30)
```

### Implementation

```python
# Using intensity
print(f"\033[1m✓ Deployment successful\033[0m")  # Bold
print(f"  Deployed 3 services")                   # Normal
print(f"\033[2m  (metadata)\033[0m")             # Dim
```

## Combining Techniques

### Example: Error Message

```bash
# Uses: color, symbols, spacing, structure
✗ Deployment failed

  Error: Connection timeout after 30s

  Possible causes:
    • Network connectivity issues
    • Service not responding
    • Firewall blocking port 443

  Suggestions:
    → Check network: ping api.example.com
    → Retry with: deploy --timeout 60
    → View logs: logs show api

Need help? Run 'deploy --help'
```

### Example: Progress Display

```bash
# Uses: symbols, color, structure
Deploying to production...

  [1/4] ✓ Build (2.3s)
  [2/4] ✓ Test (5.1s)
  [3/4] ⏱ Upload... (15s elapsed)
  [4/4] ○ Deploy

Estimated time remaining: 30s
```

## Quick Implementation Guide

### Minimal Visual Enhancement (5 min)

```python
# Add just symbols for status
print("✓ Success")
print("✗ Error")
print("⏱ Processing...")
```

### Basic Enhancement (15 min)

```python
# Add color + symbols + spacing
def success(msg):
    print(f"\033[32m✓\033[0m {msg}")

def error(msg):
    print(f"\033[31m✗\033[0m {msg}", file=sys.stderr)

def info(msg):
    print(f"\033[34m→\033[0m {msg}")

# Use grouping
print("Files changed:")
print()
for file in files:
    print(f"  {file}")
print()
```

### Full Enhancement (30 min)

Use a library like `rich`:

```python
from rich.console import Console
from rich.progress import Progress

console = Console()

console.print("[green]✓[/green] Build complete")

with Progress() as progress:
    task = progress.add_task("Deploying...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
```

## Platform Considerations

### TTY Detection

```python
if sys.stdout.isatty():
    # Interactive terminal - use colors, progress bars
    use_fancy_output()
else:
    # Piped/redirected - use plain text
    use_simple_output()
```

### Terminal Capabilities

```python
import os
import shutil

# Terminal width for wrapping
width = shutil.get_terminal_size().columns

# Color support
TERM = os.getenv('TERM', '')
supports_color = TERM not in ['dumb', ''] and sys.stdout.isatty()
```

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Rainbow output | Use 3-4 semantic colors max |
| No spacing | Add blank lines between groups |
| Color-only meaning | Always pair with symbols/text |
| Ignoring --no-color | Check flag and TTY |
| Overuse of symbols | Use consistently, not decoratively |
| No visual hierarchy | Use indentation, emphasis |

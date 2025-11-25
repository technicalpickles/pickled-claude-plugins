# CLI UX Principles

## The Six Principles

| Principle | What | When Violated | Fix |
|-----------|------|---------------|-----|
| **Familiarity** | Use known conventions | Users relearn basic operations | Follow standards (--help, verb-noun, common flags) |
| **Discoverability** | Guide users to features | Users can't find functionality | Add help text, prompts, examples, autocomplete |
| **Feedback** | Show system state | Users unsure if action worked | Confirmations, progress, state display |
| **Clarity** | Structure information | Output is overwhelming | Spacing, alignment, hierarchy, grouping |
| **Flow** | Minimize friction | Users repeatedly interrupted | Shortcuts, defaults, scriptability, interruptability |
| **Forgiveness** | Handle errors gracefully | Users afraid to experiment | Clear errors, suggestions, confirmations, undo/cancel |

## 1. Familiarity

**Core idea:** Don't reinvent conventions users already know.

### Standard Flags
```bash
--help, -h        # Always support
--version, -v     # For versioned tools
--verbose         # Detailed output
--quiet, -q       # Minimal output
--force, -f       # Skip confirmations
--dry-run         # Preview without executing
--no-color        # Disable color
```

### Command Patterns
```bash
# Git-style (verb noun)
gh repo create
gh issue list

# Traditional (noun verb)
docker container start
kubectl get pods

# Pick ONE pattern and use consistently
```

### Examples
- **GitHub CLI (`gh`)** - Mirrors Git conventions
- **LazyGit** - Single-letter keybindings that match mental models (c=commit, p=push)

## 2. Discoverability

**Core idea:** Users shouldn't need docs for basic usage.

### Help Text Requirements
```
Minimal:
- Command syntax
- Common flags
- One example

Complete:
- All commands listed
- Flag descriptions
- Multiple examples
- Common use cases
```

### Interactive Prompts
```python
# Instead of complex flags
tool create --name foo --type bar --region us-east

# Offer interactive mode
tool create
# → Name? foo
# → Type? (api/web/worker): api
# → Region? (us-east/us-west/eu): us-east
```

### Autocomplete
```bash
# Shell completion for commands/flags
gh <TAB>          # Shows: auth, repo, issue, pr...
gh pr <TAB>       # Shows: create, list, view...
```

### Examples
- **GitHub CLI** - `gh issue create` without flags launches guided prompts
- **LazyGit** - Press `?` anytime for help overlay
- **Warp** - Command palette with fuzzy search

## 3. Feedback

**Core idea:** Never leave users guessing what happened.

### Types of Feedback

**Confirmation:**
```bash
✓ Repository created: https://github.com/user/repo
✓ 3 files staged
✗ Deploy failed: connection timeout
```

**Progress:**
```bash
Deploying to prod... (30s)
[████████░░] 80% complete
Analyzing 150/200 files...
```

**State Display:**
```bash
Current branch: main
Status: 2 files staged, 3 modified
Environment: production
```

### When to Show Feedback

| Operation Duration | Feedback Required |
|-------------------|-------------------|
| <0.5s | Confirmation only |
| 0.5-2s | Simple message ("Processing...") |
| 2-10s | Progress indicator or spinner |
| >10s | Progress with details/percentage |

### Examples
- **Claude Code** - Live checklist shows task progress
- **GitHub CLI** - `✓ Pull request created at [URL]`
- **LazyGit** - Instant visual feedback when staging/unstaging

## 4. Clarity

**Core idea:** Structure output for human scanning.

### Spacing & Grouping
```bash
# Bad - wall of text
Issues: #14 bug Update remote url #13 wontfix GitHub Enterprise #8 bug Add upgrade

# Good - grouped and spaced
Issues for owner/repo

#14  Update remote url if changed     (bug)
#13  Support GitHub Enterprise        (wontfix)
#8   Add easier upgrade command       (bug)
```

### Alignment
```bash
# Bad
Name: Alice (alice@example.com) Role: Admin
Name: Bob Johnson (bob@example.com) Role: User

# Good
Name   Email              Role
Alice  alice@example.com  Admin
Bob    bob@example.com    User
```

### Hierarchy
```bash
# Use indentation to show structure
Project: web-app
  Services:
    - api (running)
    - worker (stopped)
  Database:
    - postgres (running)
```

### Examples
- **GitHub CLI** - Column-aligned issue lists
- **Broot** - Indented directory tree with context
- **Warp** - Block-based output separation

## 5. Flow

**Core idea:** Support both interactive and scripted usage.

### Dual Modes
```bash
# Interactive - prompts for missing info
deploy
# → Environment? prod
# → Confirm? y

# Scripted - all flags provided
deploy --env prod --yes
```

### Exit Codes (Critical for Flow)
```bash
# Correct
command && next-step || handle-error

# Enables chaining
build && test && deploy

# CI/CD depends on this
```

### Interruptability
```python
try:
    long_operation()
except KeyboardInterrupt:
    print("\n✗ Cancelled by user")
    cleanup()
    sys.exit(130)  # Standard SIGINT exit code
```

### Examples
- **LazyGit** - Fully keyboard-driven, no mouse required
- **Broot** - Fuzzy search, instant filtering
- **Warp** - Context-aware autocomplete

## 6. Forgiveness

**Core idea:** Make it safe to explore and easy to recover.

### Clear Error Messages
```bash
# Bad
Error: invalid

# Good
Error: Invalid environment 'production'
Valid environments: dev, staging, prod
Usage: deploy <environment>

# Better
Error: Invalid environment 'production'
Valid environments: dev, staging, prod
Did you mean 'prod'?
Usage: deploy <environment>
```

### Confirmations for Danger
```python
if is_dangerous(action) and not args.force:
    confirm = input(f"⚠ This will delete {count} items. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled")
        sys.exit(0)
```

### Suggestions
```bash
$ git statsu
git: 'statsu' is not a git command. See 'git --help'.

Did you mean this?
    status
```

### Examples
- **GitHub CLI** - Errors include next steps ("Run `gh auth login`")
- **Claude Code** - Asks before risky operations
- **LazyGit** - Confirmation before destructive operations

## Priority Matrix

Under time pressure, prioritize:

| Priority | Principle | Action | Time |
|----------|-----------|--------|------|
| 1 | Discoverability | Add --help | 2 min |
| 2 | Flow | Correct exit codes | 1 min |
| 3 | Forgiveness | Clear error messages | 5 min |
| 4 | Feedback | Progress indicators | 3 min |
| 5 | Clarity | Basic spacing | 2 min |
| 6 | Familiarity | Standard flags | 5 min |

Total for basics: ~15-20 minutes

## Anti-Patterns by Principle

| Principle | Anti-Pattern | Impact |
|-----------|-------------|---------|
| Familiarity | Custom flag names | Users can't transfer knowledge |
| Discoverability | No --help | Forces doc reading or guessing |
| Feedback | Silent operations | Anxiety, uncertainty |
| Clarity | Dense walls of text | Information overload |
| Flow | No scripting support | Can't automate |
| Forgiveness | Cryptic errors | Users stuck, frustrated |

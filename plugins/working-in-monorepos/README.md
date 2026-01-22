# working-in-monorepos Plugin

Navigate and execute commands in monorepo subprojects with automatic context detection.

## Features

- Automatic monorepo detection via git hooks
- Context-aware command execution in subprojects
- Intelligent project boundary detection
- Supports various monorepo structures (Nx, Turborepo, Lerna, etc.)

## Commands

### /monorepo-init

Initialize monorepo configuration for the current repository.

### /validate

Run validation tests to ensure plugin hooks and structure are working correctly.

## Skills

### working-in-monorepos

Navigate and execute commands in the correct subproject context within monorepos.

**Key capabilities:**
- Detect monorepo structure and project boundaries
- Execute commands in appropriate subproject directories
- Handle various monorepo tools and conventions
- Maintain context awareness across operations

## Hooks

### detect-monorepo

Automatically runs on session start to detect if the current repository is a monorepo and configure context accordingly.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and contribution guidelines.

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Or use the command
/working-in-monorepos:validate
```

## Installation

```bash
/plugin install working-in-monorepos@technicalpickles-marketplace
```

# git-workflows Plugin

Git workflow best practices and pull request management.

## Skills

### writing-git-commits

Best practices and preferences for creating git commits, handling pre-commit hooks, and managing commit signing.

**Key guidelines:**
- Always use `git add` with specific files, never `git add .` or `git add -A`
- Write commit messages to `.scratch/` directory first
- Handle pre-commit hook failures with auto-fix when possible
- Respect commit signing configuration

### writing-pull-requests (gh-pr)

Create, update, and comment on GitHub pull requests with focus on material impact, safety, and human reviewability.

**Key principles:**
- Safety first: All PR bodies written to `.scratch/pr-bodies/` before use
- Material impact: Focus on why changes matter, not metrics or file counts
- Smart merge: Detect manual edits, only update when changes are material
- Human-friendly: Concise, warm tone; assume busy reviewer

**Operations:**
- Create PRs from feature branches
- Update PR descriptions after significant changes
- Add comments to communicate with reviewers
- Follow repository PR templates and conventions

## Installation

```bash
/plugin install git-workflows@technicalpickles-marketplace
```

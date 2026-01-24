# Auto-Versioning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically bump plugin versions on commit using conventional commits, and guard against unregistered plugins.

**Architecture:** Two hk hooks - pre-commit checks marketplace registry, commit-msg validates format and bumps versions. Shell script for simple registry check, Python for version bumping logic.

**Tech Stack:** hk (git hooks manager), Python 3, bash, jq (for JSON parsing in shell)

---

## Task 1: Create hk Configuration

**Files:**
- Create: `hk.pkl`

**Step 1: Create hk.pkl configuration**

```pkl
amends "package://pkg.hk.jdx.dev/hk@1/Config.pkl"

linters {
  ["check-registry"] {
    check = "scripts/hooks/check-marketplace-registry.sh"
  }
  ["version-bump"] {
    check = "uv run scripts/hooks/version-bump.py {{commit_msg_file}}"
  }
}

hooks {
  ["pre-commit"] {
    steps = ["check-registry"]
  }
  ["commit-msg"] {
    steps = ["version-bump"]
  }
}
```

**Step 2: Commit**

```bash
git add hk.pkl
git commit -m "chore: add hk configuration for auto-versioning hooks"
```

---

## Task 2: Create Scripts Directory

**Files:**
- Create: `scripts/hooks/.gitkeep`

**Step 1: Create directory structure**

```bash
mkdir -p scripts/hooks
touch scripts/hooks/.gitkeep
```

**Step 2: Commit**

```bash
git add scripts/hooks/.gitkeep
git commit -m "chore: add scripts/hooks directory"
```

---

## Task 3: Create Marketplace Registry Check Script

**Files:**
- Create: `scripts/hooks/check-marketplace-registry.sh`

**Step 1: Write the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Get repo root
REPO_ROOT="$(git rev-parse --show-toplevel)"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"

# Check if marketplace.json exists
if [[ ! -f "$MARKETPLACE_JSON" ]]; then
    echo "ERROR: marketplace.json not found at $MARKETPLACE_JSON"
    exit 1
fi

# Get registered plugin names from marketplace.json
registered_plugins=$(jq -r '.plugins | keys[]' "$MARKETPLACE_JSON" 2>/dev/null || echo "")

# Find all plugin directories that have a .claude-plugin/plugin.json
unregistered=()
for plugin_dir in "$REPO_ROOT"/plugins/*/; do
    plugin_name=$(basename "$plugin_dir")
    plugin_json="$plugin_dir/.claude-plugin/plugin.json"

    # Skip if no plugin.json (not a real plugin)
    [[ -f "$plugin_json" ]] || continue

    # Check if registered
    if ! echo "$registered_plugins" | grep -qx "$plugin_name"; then
        unregistered+=("$plugin_name")
    fi
done

# Report unregistered plugins
if [[ ${#unregistered[@]} -gt 0 ]]; then
    echo "ERROR: Unregistered plugins detected"
    echo ""
    echo "The following plugins are not in .claude-plugin/marketplace.json:"
    for plugin in "${unregistered[@]}"; do
        echo "  - $plugin"
    done
    echo ""
    echo "Add them to marketplace.json before committing:"
    for plugin in "${unregistered[@]}"; do
        echo "  \"$plugin\": { \"source\": \"./plugins/$plugin\" }"
    done
    exit 1
fi

exit 0
```

**Step 2: Make executable**

```bash
chmod +x scripts/hooks/check-marketplace-registry.sh
```

**Step 3: Test the script manually**

Run: `./scripts/hooks/check-marketplace-registry.sh`
Expected: Exit 0 (all current plugins are registered)

**Step 4: Commit**

```bash
git add scripts/hooks/check-marketplace-registry.sh
git commit -m "feat: add pre-commit hook to check marketplace registry"
```

---

## Task 4: Create Version Bump Script

**Files:**
- Create: `scripts/hooks/version-bump.py`

**Step 1: Write the script**

```python
#!/usr/bin/env python3
"""
Commit-msg hook: validate conventional commits and bump plugin versions.

Usage: version-bump.py <commit-msg-file>
"""

import json
import re
import subprocess
import sys
from pathlib import Path


# Conventional commit pattern
COMMIT_PATTERN = re.compile(
    r'^(?P<type>feat|fix|perf|refactor|chore|docs|test|ci|style|build)'
    r'(?:\((?P<scope>[^)]+)\))?'
    r'(?P<breaking>!)?'
    r': '
    r'(?P<description>.+)$',
    re.MULTILINE
)

# Types that trigger version bumps
BUMP_TYPES = {
    'feat': 'minor',
    'fix': 'patch',
    'perf': 'patch',
    'refactor': 'patch',
}

# Types that don't bump versions
NO_BUMP_TYPES = {'chore', 'docs', 'test', 'ci', 'style', 'build'}


def parse_commit_message(msg_file: Path) -> tuple[str, str | None, bool, str]:
    """Parse commit message and return (type, scope, is_breaking, description)."""
    content = msg_file.read_text()

    # Get first line for parsing
    first_line = content.split('\n')[0].strip()

    match = COMMIT_PATTERN.match(first_line)
    if not match:
        print("ERROR: Commit message doesn't follow conventional commit format")
        print("")
        print(f"Expected: <type>(<scope>): <description>")
        print(f"Got: \"{first_line}\"")
        print("")
        print("Valid types: feat, fix, perf, refactor, chore, docs, test, ci, style, build")
        print("Examples:")
        print("  feat: add new route type")
        print("  fix(tool-routing): handle missing config")
        print("  chore: update dependencies")
        sys.exit(1)

    # Check for BREAKING CHANGE in body
    is_breaking = bool(match.group('breaking')) or 'BREAKING CHANGE:' in content

    return (
        match.group('type'),
        match.group('scope'),
        is_breaking,
        match.group('description')
    )


def get_changed_plugins() -> set[str]:
    """Get plugin names that have staged changes."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True,
        check=True
    )

    plugins = set()
    for line in result.stdout.strip().split('\n'):
        if line.startswith('plugins/'):
            parts = line.split('/')
            if len(parts) >= 2:
                plugins.add(parts[1])

    return plugins


def bump_version(version: str, bump_type: str) -> str:
    """Bump a semver version string."""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")

    major, minor, patch = map(int, parts)

    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_plugin_version(repo_root: Path, plugin_name: str, bump_type: str) -> str | None:
    """Update plugin version and return new version, or None if no change."""
    plugin_json = repo_root / 'plugins' / plugin_name / '.claude-plugin' / 'plugin.json'

    if not plugin_json.exists():
        print(f"WARNING: No plugin.json for {plugin_name}, skipping")
        return None

    try:
        data = json.loads(plugin_json.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {plugin_json}: {e}")
        sys.exit(1)

    old_version = data.get('version', '0.0.0')

    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', old_version):
        print(f"ERROR: Invalid version in {plugin_json}")
        print(f"Expected semver format (e.g., \"1.0.0\"), got: \"{old_version}\"")
        sys.exit(1)

    new_version = bump_version(old_version, bump_type)
    data['version'] = new_version

    plugin_json.write_text(json.dumps(data, indent=2) + '\n')

    return new_version


def main():
    if len(sys.argv) != 2:
        print("Usage: version-bump.py <commit-msg-file>")
        sys.exit(1)

    msg_file = Path(sys.argv[1])
    if not msg_file.exists():
        print(f"ERROR: Commit message file not found: {msg_file}")
        sys.exit(1)

    # Parse commit message
    commit_type, scope, is_breaking, description = parse_commit_message(msg_file)

    # Determine bump type
    if is_breaking:
        bump_type = 'major'
    elif commit_type in BUMP_TYPES:
        bump_type = BUMP_TYPES[commit_type]
    elif commit_type in NO_BUMP_TYPES:
        # No version bump needed
        sys.exit(0)
    else:
        print(f"ERROR: Unknown commit type: {commit_type}")
        sys.exit(1)

    # Get changed plugins
    changed_plugins = get_changed_plugins()

    if not changed_plugins:
        # No plugins changed, nothing to bump
        sys.exit(0)

    # If scope matches a plugin name, only bump that one
    if scope and scope in changed_plugins:
        plugins_to_bump = {scope}
    elif scope and scope not in changed_plugins:
        # Scope doesn't match any changed plugin - warn but bump all
        print(f"WARNING: Scope '{scope}' doesn't match any changed plugin")
        print(f"Changed plugins: {', '.join(sorted(changed_plugins))}")
        print(f"Bumping all changed plugins")
        plugins_to_bump = changed_plugins
    else:
        plugins_to_bump = changed_plugins

    # Get repo root
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True,
        text=True,
        check=True
    )
    repo_root = Path(result.stdout.strip())

    # Bump versions
    bumped = []
    for plugin in sorted(plugins_to_bump):
        new_version = update_plugin_version(repo_root, plugin, bump_type)
        if new_version:
            bumped.append((plugin, new_version))
            # Stage the version file
            plugin_json = repo_root / 'plugins' / plugin / '.claude-plugin' / 'plugin.json'
            subprocess.run(['git', 'add', str(plugin_json)], check=True)

    if bumped:
        print(f"Version bumped ({bump_type}):")
        for plugin, version in bumped:
            print(f"  {plugin}: {version}")

        # Amend commit to include version changes
        try:
            subprocess.run(
                ['git', 'commit', '--amend', '--no-edit', '--no-verify'],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"WARNING: Failed to amend commit: {e}")
            print("You may need to run: git commit --amend --no-edit")

    sys.exit(0)


if __name__ == '__main__':
    main()
```

**Step 2: Make executable**

```bash
chmod +x scripts/hooks/version-bump.py
```

**Step 3: Test validation with invalid message**

Create a test file and run:
```bash
echo "bad message" > /tmp/test-commit-msg
uv run scripts/hooks/version-bump.py /tmp/test-commit-msg
```
Expected: Exit 1 with "ERROR: Commit message doesn't follow conventional commit format"

**Step 4: Test validation with valid message (no bump type)**

```bash
echo "chore: update readme" > /tmp/test-commit-msg
uv run scripts/hooks/version-bump.py /tmp/test-commit-msg
```
Expected: Exit 0 (no version bump for chore)

**Step 5: Commit**

```bash
git add scripts/hooks/version-bump.py
git commit -m "feat: add commit-msg hook for version bumping"
```

---

## Task 5: Update CLAUDE.md with Versioning Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add versioning section to CLAUDE.md**

Add after the "Environment Variables" section:

```markdown
## Versioning

This repo uses conventional commits with automatic version bumping via [hk](https://github.com/jdx/hk).

### Setup

```bash
# Install hk
mise use -g hk  # or: brew install jdx/tap/hk

# Install hooks
hk install
```

### Commit Format

```
<type>(<scope>): <description>
```

| Type | Version Bump |
|------|--------------|
| `feat` | minor (0.x.0) |
| `fix`, `perf`, `refactor` | patch (0.0.x) |
| `chore`, `docs`, `test`, `ci`, `style`, `build` | none |

Add `BREAKING CHANGE:` in body or `!` after type for major bump (x.0.0).

### Multi-Plugin Commits

- **No scope:** All changed plugins are bumped
- **With scope:** Only the scoped plugin is bumped (if it matches a plugin name)

Example:
```bash
# Bumps all changed plugins
feat: add cross-plugin discovery

# Bumps only tool-routing
feat(tool-routing): add new route type
```

### New Plugins

New plugin directories must be added to `.claude-plugin/marketplace.json` before committing. The pre-commit hook will block otherwise.
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add versioning workflow documentation"
```

---

## Task 6: Install and Test Hooks

**Step 1: Install hk hooks**

```bash
hk install
```

**Step 2: Test pre-commit hook**

Create an unregistered plugin directory temporarily:
```bash
mkdir -p plugins/test-plugin/.claude-plugin
echo '{"name": "test-plugin", "version": "1.0.0"}' > plugins/test-plugin/.claude-plugin/plugin.json
git add plugins/test-plugin/
git commit -m "test: add test plugin"
```
Expected: Commit blocked with "ERROR: Unregistered plugins detected"

Clean up:
```bash
git reset HEAD
rm -rf plugins/test-plugin/
```

**Step 3: Test commit-msg hook with real change**

Make a small change to a plugin:
```bash
echo "# test" >> plugins/tool-routing/README.md
git add plugins/tool-routing/README.md
git commit -m "fix(tool-routing): test version bump"
```
Expected:
- Commit succeeds
- tool-routing version bumped from 1.0.0 to 1.0.1
- Version change included in commit

Verify:
```bash
git show --stat HEAD
cat plugins/tool-routing/.claude-plugin/plugin.json
```

**Step 4: Revert test change**

```bash
git reset --hard HEAD~1
```

---

## Task 7: Final Commit and PR

**Step 1: Verify all files**

```bash
git status
ls -la scripts/hooks/
cat hk.pkl
```

**Step 2: Push branch**

```bash
git push -u origin feature/auto-versioning
```

**Step 3: Create PR**

```bash
gh pr create --title "feat: add auto-versioning with conventional commits" --body "$(cat <<'EOF'
## Summary

- Adds hk git hooks for automatic version management
- Pre-commit hook blocks commits if new plugins aren't registered in marketplace.json
- Commit-msg hook validates conventional commit format and bumps versions accordingly

## Changes

- `hk.pkl` - hk configuration
- `scripts/hooks/check-marketplace-registry.sh` - registry guard
- `scripts/hooks/version-bump.py` - version bumping logic
- `CLAUDE.md` - documentation for versioning workflow

## Test Plan

- [ ] Install hooks with `hk install`
- [ ] Verify pre-commit blocks unregistered plugins
- [ ] Verify commit-msg validates format
- [ ] Verify version bumps work for feat/fix commits
- [ ] Verify no bump for chore/docs commits

---

Generated with [Claude Code](https://claude.ai/code)
EOF
)"
```

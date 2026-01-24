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

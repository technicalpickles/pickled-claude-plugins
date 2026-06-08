#!/usr/bin/env bash
# Tests for scripts/generate-plugin-table.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/generate-plugin-table.sh"
fails=0

assert_contains() { # haystack needle label
  if [[ "$1" == *"$2"* ]]; then echo "  ✓ $3"; else echo "  ✗ $3"; echo "    expected to find: $2"; fails=$((fails+1)); fi
}
assert_not_contains() {
  if [[ "$1" != *"$2"* ]]; then echo "  ✓ $3"; else echo "  ✗ $3"; echo "    did not expect: $2"; fails=$((fails+1)); fi
}

# Fixture README with markers
fixture="$(mktemp)"
cat > "$fixture" <<'EOF'
# Test
## Plugins
<!-- BEGIN GENERATED PLUGINS (run scripts/generate-plugin-table.sh) -->
old content
<!-- END GENERATED PLUGINS -->
## After
EOF

echo "Test: generate writes a table"
README="$fixture" "$SCRIPT" >/dev/null
out="$(cat "$fixture")"
assert_contains "$out" "| Plugin | Description | Skills |" "has table header"
assert_contains "$out" "[git](plugins/git)" "includes local plugin git with dir link"
assert_contains "$out" "[cq](https://github.com/technicalpickles/cq)" "remote plugin links to repo (no .git)"
assert_contains "$out" "[see repo](https://github.com/technicalpickles/cq)" "remote skills cell links to repo"
assert_not_contains "$out" "debugging-tools" "excludes unpublished local dir debugging-tools"
assert_not_contains "$out" "session-analyzer" "excludes unpublished local dir session-analyzer"
assert_not_contains "$out" "-workspace" "filters *-workspace helper skills"
assert_contains "$out" "## After" "preserves content after end marker"
assert_not_contains "$out" "old content" "replaces prior block body"

echo "Test: --check is idempotent after a write"
if README="$fixture" "$SCRIPT" --check >/dev/null 2>&1; then echo "  ✓ --check passes on freshly generated file"; else echo "  ✗ --check should pass"; fails=$((fails+1)); fi

echo "Test: --check fails on drift"
printf '%s\n' "garbage" >> "$fixture"
# re-create marker block mismatch by editing inside markers
sed -i.bak 's/| \[git\]/| [GIT-EDITED]/' "$fixture" 2>/dev/null || true
if README="$fixture" "$SCRIPT" --check >/dev/null 2>&1; then echo "  ✗ --check should fail on drift"; fails=$((fails+1)); else echo "  ✓ --check fails on drift"; fi

rm -f "$fixture" "$fixture.bak"
echo
if [[ $fails -gt 0 ]]; then echo "FAILED: $fails assertion(s)"; exit 1; else echo "All assertions passed"; fi

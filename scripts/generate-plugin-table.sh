#!/usr/bin/env bash
#
# Generates the plugin table in README.md from marketplace.json.
#
# Source of truth: .claude-plugin/marketplace.json (.plugins[], sorted by name).
#  - Local plugin (source is a string path): description from the marketplace entry
#    or the local plugins/<name>/.claude-plugin/plugin.json; link to plugins/<name>;
#    skills = dir names under plugins/<name>/skills/ with *-workspace filtered out.
#  - Remote plugin (source is an object): description from the marketplace entry
#    (required); link + skills cell point at the repo (source.url, .git stripped).
#
# Usage:
#   ./scripts/generate-plugin-table.sh           # rewrite the table in README.md
#   ./scripts/generate-plugin-table.sh --check    # exit non-zero if README is out of date
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"
README="${README:-$REPO_ROOT/README.md}"
BEGIN_MARKER="<!-- BEGIN GENERATED PLUGINS (run scripts/generate-plugin-table.sh) -->"
END_MARKER="<!-- END GENERATED PLUGINS -->"

CHECK_MODE=false
[[ "${1:-}" == "--check" ]] && CHECK_MODE=true

if ! grep -qF "$BEGIN_MARKER" "$README"; then
  echo "ERROR: $README has no generated-plugins markers." >&2
  echo "       Add the BEGIN/END marker comments to the ## Plugins section first." >&2
  exit 1
fi

# Build table rows into the global ROWS array (runs in the main shell so a
# missing description can hard-fail via exit).
ROWS=()
build_rows() {
  local name entry source_type desc url link skills skills_dir skills_cell
  for name in $(jq -r '.plugins | sort_by(.name)[].name' "$MARKETPLACE_JSON"); do
    entry="$(jq -c --arg n "$name" '.plugins[] | select(.name==$n)' "$MARKETPLACE_JSON")"
    source_type="$(jq -r '.source | type' <<<"$entry")"
    if [[ "$source_type" == "string" ]]; then
      desc="$(jq -r '.description // ""' <<<"$entry")"
      if [[ -z "$desc" ]]; then
        desc="$(jq -r '.description // ""' "$REPO_ROOT/plugins/$name/.claude-plugin/plugin.json" 2>/dev/null || true)"
      fi
      link="plugins/$name"
      skills_dir="$REPO_ROOT/plugins/$name/skills"
      skills=""
      if [[ -d "$skills_dir" ]]; then
        skills="$(find "$skills_dir" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; \
          | grep -v -- '-workspace$' | sort | paste -sd, - | sed 's/,/, /g')"
      fi
      skills_cell="${skills:-–}"
    else
      desc="$(jq -r '.description // ""' <<<"$entry")"
      url="$(jq -r '.source.url // ""' <<<"$entry" | sed 's/\.git$//')"
      link="$url"
      skills_cell="[see repo]($url)"
    fi
    if [[ -z "$desc" ]]; then
      echo "ERROR: no description for plugin '$name'." >&2
      echo "       Add a \"description\" to its .claude-plugin/marketplace.json entry." >&2
      exit 1
    fi
    ROWS+=("| [$name]($link) | $desc | $skills_cell |")
  done
}

build_rows

# Assemble the full block (markers included) into a temp file.
block_file="$(mktemp)"
{
  printf '%s\n' "$BEGIN_MARKER"
  printf '%s\n' "| Plugin | Description | Skills |"
  printf '%s\n' "|--------|-------------|--------|"
  printf '%s\n' "${ROWS[@]}"
  printf '%s\n' "$END_MARKER"
} > "$block_file"

# Render the new README into a temp file by replacing the marker block.
tmp="$(mktemp)"
awk -v block_file="$block_file" '
  $0 ~ /<!-- BEGIN GENERATED PLUGINS/ {
    while ((getline line < block_file) > 0) { print line }
    skip=1; next
  }
  $0 ~ /<!-- END GENERATED PLUGINS -->/ { skip=0; next }
  skip { next }
  { print }
' "$README" > "$tmp"
rm -f "$block_file"

if [[ "$CHECK_MODE" == "true" ]]; then
  if diff -u "$README" "$tmp" >/dev/null; then
    rm -f "$tmp"
    echo "✓ README plugin table is up to date."
    exit 0
  fi
  echo "❌ README plugin table is out of date. Diff (committed vs generated):" >&2
  diff -u "$README" "$tmp" >&2 || true
  echo >&2
  echo "Fix: ./scripts/generate-plugin-table.sh" >&2
  rm -f "$tmp"
  exit 1
fi

mv "$tmp" "$README"
echo "✓ Wrote plugin table to $README"

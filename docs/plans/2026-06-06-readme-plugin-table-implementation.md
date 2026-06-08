# Generated Plugin Table Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hand-written, stale `## Plugins` section of the root README with a marketplace.json-driven generated table, gated by CI so it cannot silently drift.

**Architecture:** A bash + jq script (`scripts/generate-plugin-table.sh`) reads `marketplace.json` (the canonical published list, sorted by name), resolves each plugin's description (marketplace entry `.description`, falling back to the local `plugin.json`) and skills (local `skills/` dirs, `*-workspace` filtered; remote plugins get a "see repo" link), and rewrites the table between marker comments in `README.md`. A `--check` mode diffs committed vs generated and exits non-zero on drift. A sibling CI workflow (`plugin-list-check.yml`) runs `--check` on PRs. The generator is also invoked from `bump-version.sh --auto`.

**Tech Stack:** Bash, jq, GitHub Actions. Matches the existing `scripts/*.sh` + `version-check.yml` conventions in this repo.

---

## File Structure

- `scripts/generate-plugin-table.sh` (Create) — the generator + `--check` mode. Single responsibility: keep the README plugin table in sync with marketplace.json.
- `tests/scenarios/test-plugin-table.sh` (Create) — bash assertions for the generator, modeled on `tests/scenarios/test-hook-behavior.sh`.
- `.claude-plugin/marketplace.json` (Modify) — add `description` to the `cq` and `petri-dish` (remote) entries.
- `README.md` (Modify) — replace `## Plugins` prose with the marker-delimited generated table; de-enumerate the Repository Structure tree.
- `CLAUDE.md` (Modify) — de-enumerate the Repository Structure tree; note that `bump-version.sh --auto` regenerates the table and CI gates it.
- `scripts/bump-version.sh` (Modify) — call the generator from `auto_bump`.
- `.github/workflows/plugin-list-check.yml` (Create) — CI drift gate.

Conventions to follow (from existing scripts):
- `REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"` for cwd-independence.
- `set -euo pipefail`.
- Avoid process substitution (`<(...)`) and pipe-into-`while` for any loop that must `exit` on error — Claude Code's sandbox blocks process substitution, and `exit` inside a piped `while` only exits the subshell. Iterate with `for name in $(jq -r ...)` in the main shell instead (plugin names match `[a-z0-9-]+`, so whitespace word-splitting is safe).
- Use `find ... -exec basename {} \;` (portable) rather than `find -printf` (GNU-only) since the script runs on macOS (local) and Ubuntu (CI).

---

## Task 1: Add descriptions for remote plugins to marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

The two git-subdir plugins (`cq`, `petri-dish`) have no local `plugin.json`, so the generator reads their description from the marketplace entry. Add it now so later tasks have real data.

- [ ] **Step 1: Add `description` to the `cq` entry**

In `.claude-plugin/marketplace.json`, the `cq` entry becomes:

```json
    {
      "name": "cq",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/technicalpickles/cq.git",
        "path": "claude-plugin",
        "ref": "main"
      },
      "version": "0.3.0",
      "description": "Query past Claude Code sessions via the cq CLI (SQL over session transcripts)"
    },
```

- [ ] **Step 2: Add `description` to the `petri-dish` entry**

```json
    {
      "name": "petri-dish",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/technicalpickles/petri-dish.git",
        "path": "claude-plugin",
        "ref": "main"
      },
      "version": "0.1.0",
      "description": "Author Claude Code experiments (petri-dish cultures) with disciplined schema, baselines, and multi-run averaging"
    },
```

- [ ] **Step 3: Validate JSON**

Run: `jq -e '.plugins[] | select(.name=="cq" or .name=="petri-dish") | .description' .claude-plugin/marketplace.json`
Expected: prints both description strings, exit 0.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: add descriptions for remote plugins in marketplace.json"
```

---

## Task 2: Write the generator script (TDD)

**Files:**
- Create: `scripts/generate-plugin-table.sh`
- Test: `tests/scenarios/test-plugin-table.sh`

The generator needs marker comments to exist in `README.md`. To let the test run before the README is edited (Task 3), the script operates on a file path given by the `README` variable, defaulting to `$REPO_ROOT/README.md`, and the test points it at a temp fixture.

- [ ] **Step 1: Write the failing test**

Create `tests/scenarios/test-plugin-table.sh`:

```bash
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `chmod +x tests/scenarios/test-plugin-table.sh && ./tests/scenarios/test-plugin-table.sh`
Expected: FAIL — script does not exist yet (`No such file or directory`).

- [ ] **Step 3: Write the generator script**

Create `scripts/generate-plugin-table.sh`:

```bash
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

# Assemble the full block (markers included).
block="$BEGIN_MARKER
| Plugin | Description | Skills |
|--------|-------------|--------|
$(printf '%s\n' "${ROWS[@]}")$END_MARKER"

# Render the new README into a temp file by replacing the marker block.
tmp="$(mktemp)"
awk -v block="$block" '
  $0 ~ /<!-- BEGIN GENERATED PLUGINS/ { print block; skip=1; next }
  $0 ~ /<!-- END GENERATED PLUGINS -->/ { skip=0; next }
  skip { next }
  { print }
' "$README" > "$tmp"

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
```

Note on the `block` assembly: `printf '%s\n' "${ROWS[@]}"` ends each row with a newline, so the `$END_MARKER` that immediately follows lands on its own line.

- [ ] **Step 4: Run the test to verify it passes**

Run: `chmod +x scripts/generate-plugin-table.sh && ./tests/scenarios/test-plugin-table.sh`
Expected: PASS — "All assertions passed".

- [ ] **Step 5: Sanity-check against the real README markers absence**

Run: `./scripts/generate-plugin-table.sh`
Expected: FAIL with "has no generated-plugins markers" (the real README has no markers yet — added in Task 3). This confirms the guard works.

- [ ] **Step 6: Commit**

```bash
git add scripts/generate-plugin-table.sh tests/scenarios/test-plugin-table.sh
git commit -m "feat: add generate-plugin-table.sh with --check mode"
```

---

## Task 3: Replace the README Plugins section with the generated table

**Files:**
- Modify: `README.md` (the `## Plugins` section, currently lines ~45-98)

- [ ] **Step 1: Replace the prose subsections with empty markers**

In `README.md`, delete everything from the `## Plugins` heading's body (all `### <plugin>` subsections) and replace with:

```markdown
## Plugins

<!-- BEGIN GENERATED PLUGINS (run scripts/generate-plugin-table.sh) -->
<!-- END GENERATED PLUGINS -->
```

Keep the `## Plugins` heading and the following `## Usage` heading intact.

- [ ] **Step 2: Generate the table**

Run: `./scripts/generate-plugin-table.sh`
Expected: "✓ Wrote plugin table to .../README.md".

- [ ] **Step 3: Verify the output**

Run: `sed -n '/BEGIN GENERATED PLUGINS/,/END GENERATED PLUGINS/p' README.md`
Expected: a table with all 17 marketplace plugins sorted by name, `cq`/`petri-dish` linking to their repos with `[see repo]` skills cells, no `debugging-tools`/`session-analyzer`, no `*-workspace` skills, and `–` for hook-only plugins (sandbox-advisor, stay-on-target, tool-routing, mcpproxy if it has no skills, etc.).

- [ ] **Step 4: Verify --check now passes**

Run: `./scripts/generate-plugin-table.sh --check`
Expected: "✓ README plugin table is up to date." exit 0.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: replace Plugins prose with generated table"
```

---

## Task 4: De-enumerate Repository Structure trees and document the convention

**Files:**
- Modify: `README.md` (the `## Repository Structure` tree, ~lines 7-20)
- Modify: `CLAUDE.md` (the Repository Structure tree + Contributing section)

- [ ] **Step 1: Simplify the README Repository Structure tree**

In `README.md`, replace the enumerated `plugins/` subtree with:

```
pickled-claude-plugins/
├── .claude-plugin/
│   ├── plugin.json           # Root marketplace metadata
│   └── marketplace.json      # Plugin registry (source of truth for the Plugins list)
├── plugins/
│   └── <plugin-name>/        # One directory per local plugin (see Plugins below)
└── docs/
```

- [ ] **Step 2: Simplify the CLAUDE.md Repository Structure tree**

In `CLAUDE.md`, replace the enumerated `plugins/` block under "## Repository Structure" with:

```
plugins/
└── {name}/   # One directory per local plugin. Canonical list: README.md "## Plugins" (generated).
```

- [ ] **Step 3: Document the regeneration step in CLAUDE.md Contributing**

In `CLAUDE.md`, under "## Contributing", change the bump step to mention the table. Replace:

```
5. Run `./scripts/bump-version.sh --auto` and commit the bump as `chore(plugin): bump version to X.Y.Z`
```

with:

```
5. Run `./scripts/bump-version.sh --auto` (also regenerates the README plugin table) and commit as `chore(plugin): bump version to X.Y.Z`
```

And under "## Versioning" (or a new adjacent note), add:

```
The root README's `## Plugins` table is generated from `marketplace.json` by
`scripts/generate-plugin-table.sh`. Adding, removing, or re-describing a plugin means
regenerating it (`./scripts/generate-plugin-table.sh`, or `bump-version.sh --auto`).
The `plugin-list-check.yml` workflow blocks merge until the committed table matches.
```

- [ ] **Step 4: Verify --check still passes (no table change expected)**

Run: `./scripts/generate-plugin-table.sh --check`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: de-enumerate structure trees and document plugin-table convention"
```

---

## Task 5: Wire the generator into bump-version.sh --auto

**Files:**
- Modify: `scripts/bump-version.sh` (the `auto_bump` function, ~lines 129-160)

The generator must run even when there are no version bumps (a description-only change), so call it at the start of `auto_bump`, before the early `exit 0`.

- [ ] **Step 1: Add the generator call to `auto_bump`**

In `scripts/bump-version.sh`, at the top of the `auto_bump()` function body (immediately after the opening `local dry_run=...` line), add:

```bash
    # Keep the README plugin table in sync with marketplace.json.
    if [[ "$dry_run" != "true" ]]; then
        "$REPO_ROOT/scripts/generate-plugin-table.sh" || true
    fi
```

- [ ] **Step 2: Verify it runs**

Run: `./scripts/bump-version.sh --auto --dry-run`
Expected: runs without error (dry-run skips regeneration). Then run `./scripts/generate-plugin-table.sh --check` and expect exit 0 (table unchanged).

- [ ] **Step 3: Commit**

```bash
git add scripts/bump-version.sh
git commit -m "feat: regenerate README plugin table from bump-version --auto"
```

---

## Task 6: Add the CI drift gate

**Files:**
- Create: `.github/workflows/plugin-list-check.yml`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/plugin-list-check.yml`:

```yaml
name: Plugin List Check

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  check-plugin-table:
    name: Validate README plugin table
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install jq
        run: sudo apt-get install -y jq

      - name: Check README plugin table is up to date
        run: |
          chmod +x ./scripts/generate-plugin-table.sh
          ./scripts/generate-plugin-table.sh --check
```

- [ ] **Step 2: Lint the YAML locally**

Run: `jq -n 'true' >/dev/null && python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/plugin-list-check.yml'))" && echo "yaml ok"`
Expected: "yaml ok" (valid YAML).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/plugin-list-check.yml
git commit -m "ci: add plugin-list-check workflow gating README table drift"
```

---

## Task 7: Update session memory (outside this repo)

**Files:**
- Modify: `/Users/josh.nichols/.claude/projects/-Users-josh-nichols-pickleton/memory/` — the pickled-claude-plugins versioning note + `MEMORY.md` index line.

This is a pickleton session-memory update, not part of the repo PR.

- [ ] **Step 1: Add a fact to the existing pickled-claude-plugins versioning memory**

Append to the relevant memory note (or the MEMORY.md "pickled-claude-plugins Versioning" section): the root README `## Plugins` table is generated by `scripts/generate-plugin-table.sh` from `marketplace.json`, gated by `plugin-list-check.yml`; remote plugins (cq, petri-dish) carry their `description` in their marketplace entry; run the generator (or `bump-version.sh --auto`) when adding/removing/re-describing a plugin.

---

## Self-Review notes

- **Spec coverage:** marketplace-driven list (T2), description fallback local→plugin.json (T2), remote description via marketplace entry (T1+T2), `*-workspace` filter + `–` for no-skills (T2), `see repo` for remote skills (T2), marker-delimited table replacing prose (T3), `--check` mode + CI gate (T2, T6), bump-version wiring (T5), de-enumerated trees + CLAUDE.md note (T4), memory update (T7). All covered.
- **Sandbox caveats:** no process substitution, no pipe-into-`while` for exit paths; `mktemp` honors `$TMPDIR`. If any step EPERMs under the sandbox, re-run that Bash call with `dangerouslyDisableSandbox: true`.
- **Portability:** `find -exec basename` (not `-printf`); `sed -i.bak` in the test (BSD/GNU compatible) with the `.bak` cleaned up.
- **Verification after all tasks:** `./tests/scenarios/test-plugin-table.sh` passes, `./scripts/generate-plugin-table.sh --check` exits 0, and the README table lists all 17 plugins.

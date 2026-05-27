# actually-lsp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the actually-lsp Claude Code plugin: closes the LSP activation gap end-to-end (detection, setup, activation, failure diagnosis) for Rust, TypeScript, and Ruby projects.

**Architecture:** Single plugin in pickled-claude-plugins. Three hooks (SessionStart, PreToolUse, PostToolUseFailure) plus two skills (`/actually-lsp:doctor` and `/actually-lsp:skip`). Layered on top of the official LSP plugins from `claude-plugins-official`; ecosystem-aware data tables drive detection per language. See [`2026-05-27-design.md`](2026-05-27-design.md) for the full spec.

**Tech Stack:** Bash for hook scripts, Python (pytest) for tests, JSON for state files, markdown for skill bodies and activation context. Conventional commits with `actually-lsp` scope. Versions live in `.claude-plugin/marketplace.json` at the marketplace root.

---

## Important context for the implementer

**You are working in:** `/Users/josh.nichols/pickleton/repos/pickled-claude-plugins/worktrees/actually-lsp/` (worktree on branch `actually-lsp`, created earlier in the brainstorming session).

**Spec and decisions live at:**
- `plugins/actually-lsp/docs/plans/2026-05-27-design.md` (the design spec)
- `plugins/actually-lsp/CONTEXT.md` (vocabulary, state machine)
- `plugins/actually-lsp/docs/adr/0001-layer-on-top-of-official-lsp-plugins.md`
- `plugins/actually-lsp/docs/adr/0002-ecosystem-aware-not-lsp-plugin-aware.md`

**Existing plugin patterns to crib from:**
- `plugins/working-in-monorepos/` is the closest analog for the hook + test layout (bash SessionStart hook + Python pytest tests). Read its `hooks/scripts/detect-monorepo.sh`, `hooks/hooks.json`, `tests/test_hooks_integration.py`, `tests/test_plugin_structure.py`, and `pyproject.toml` before starting. Note: it still ships `commands/*.md` files, which are dead code (Claude Code no longer surfaces plugin commands). Use `skills/<name>/SKILL.md` for user-invocable actions instead. See `plugins/agent-meta/skills/snapshot/SKILL.md` for the right pattern.
- `plugins/sandbox-first/hooks/hooks.json` shows `PostToolUseFailure` event usage (matched to `Bash`). We'll use it matched to `LSP`.

**Conventional commit rules (from `pickled-claude-plugins/CLAUDE.md` at the repo root):**
- Scope must be `actually-lsp` (lowercase, hyphens only)
- `feat(actually-lsp): description` triggers minor bump
- `fix(actually-lsp): description` triggers patch bump
- `chore(actually-lsp): description` triggers no bump (use for version bump commits and other no-op changes)
- `chore(actually-lsp): bump version to X.Y.Z` is the bump commit format
- CI runs `version-check.yml` on every PR and blocks merge until pending bumps are applied

**Pre-commit hooks (via hk.pkl + jdx/hk):**
- `validate-versions`: runs `./scripts/validate-plugin-versions.sh`
- `conventional-commit`: enforces format
- `validate-scope`: runs `./scripts/check-commit-scope.sh` against the message file

**No em-dashes anywhere in prose.** Hard rule. Grep `—` before each commit. Use commas, colons, parens, or sentence breaks instead.

**Running tests locally:**
```bash
cd plugins/actually-lsp
uv run pytest tests/ -v
```
(Use `uv` because `working-in-monorepos` and others use it; `pyproject.toml` declares pytest as a dep.)

**PR-by-PR rollout (six PRs):**
- PR 1: Plugin scaffold + TypeScript SessionStart happy path
- PR 2: Add Rust and Ruby
- PR 3: PreToolUse hook for deferred detection
- PR 4: PostToolUseFailure hook for failure context
- PR 5: Skills (`/actually-lsp:doctor`, `/actually-lsp:skip`)
- PR 6: Polish (README, smoke test plan, version bump to 1.0.0)

---

# PR 1: Plugin scaffold + TypeScript SessionStart

**Goal:** Plugin installs from the marketplace, fires its SessionStart hook on session boot, detects TypeScript projects, emits a nudge if rust-analyzer-lsp... wait, ruby-lsp... wait, `typescript-lsp` isn't installed, or activation context if it is.

**Why TypeScript first:** Strongest activation data (4.6/5 at N=5 on bktide per the share-out). If the architecture works for TypeScript, the Rust and Ruby additions are mostly data-table edits.

**Commit scope for this PR:** `feat(actually-lsp): ...` for feature commits, `chore(actually-lsp): bump version to 0.1.0` for the bump.

## Task 1: pyproject.toml for tests

**Files:**
- Create: `plugins/actually-lsp/pyproject.toml`

- [ ] **Step 1: Write the file**

```toml
[project]
name = "actually-lsp-tests"
version = "0.1.0"
description = "Tests for actually-lsp plugin"
requires-python = ">=3.11"

dependencies = [
    "pytest>=8.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

- [ ] **Step 2: Verify uv recognizes it**

```bash
cd plugins/actually-lsp && uv run pytest --version
```
Expected: prints pytest version, no errors.

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/pyproject.toml
git commit -m "feat(actually-lsp): add pyproject.toml for plugin tests"
```

## Task 2: plugin.json manifest

**Files:**
- Create: `plugins/actually-lsp/.claude-plugin/plugin.json`
- Test: `plugins/actually-lsp/tests/test_plugin_structure.py`

- [ ] **Step 1: Write the failing test**

Create `plugins/actually-lsp/tests/__init__.py` (empty file).

Create `plugins/actually-lsp/tests/test_plugin_structure.py`:

```python
"""Validate plugin structure matches Claude Code's expected format."""

import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


class TestPluginManifest:
    """Validate .claude-plugin/plugin.json exists and has required fields."""

    def test_manifest_exists(self):
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        assert manifest_path.exists(), (
            f"Missing plugin manifest at {manifest_path}"
        )

    def test_manifest_is_valid_json(self):
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        data = json.loads(manifest_path.read_text())
        assert isinstance(data, dict)

    def test_manifest_has_required_fields(self):
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        data = json.loads(manifest_path.read_text())
        assert "name" in data
        assert "description" in data
        assert data["name"] == "actually-lsp"

    def test_manifest_has_no_version_field(self):
        """Versions live in marketplace.json, not plugin.json."""
        manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        data = json.loads(manifest_path.read_text())
        assert "version" not in data, (
            "plugin.json must NOT include version (lives in marketplace.json)"
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_plugin_structure.py -v
```
Expected: FAIL with `Missing plugin manifest`.

- [ ] **Step 3: Write the plugin.json**

```json
{
  "name": "actually-lsp",
  "description": "Closes the LSP activation gap end-to-end (detection, setup, activation, failure diagnosis) for Rust, TypeScript, and Ruby projects",
  "author": {"name": "Josh Nichols", "email": "josh@technicalpickles.com"},
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT"
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_plugin_structure.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/.claude-plugin/plugin.json plugins/actually-lsp/tests/__init__.py plugins/actually-lsp/tests/test_plugin_structure.py
git commit -m "feat(actually-lsp): add plugin manifest with structural tests"
```

## Task 3: ecosystems.sh data table (TypeScript only)

**Files:**
- Create: `plugins/actually-lsp/lib/ecosystems.sh`
- Test: `plugins/actually-lsp/tests/test_ecosystems.py`

- [ ] **Step 1: Write the failing test**

```python
"""Verify ecosystems.sh exposes the per-ecosystem data table."""

import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
ECOSYSTEMS_SH = PLUGIN_ROOT / "lib" / "ecosystems.sh"


def test_ecosystems_sh_exists():
    assert ECOSYSTEMS_SH.exists()


def test_ecosystems_sh_defines_typescript():
    """Sourcing ecosystems.sh should expose a 'typescript' row in $ecosystems."""
    result = subprocess.run(
        ["bash", "-c", f"source {ECOSYSTEMS_SH} && printf '%s\\n' \"${{ecosystems[@]}}\""],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split("\n")
    typescript_rows = [l for l in lines if l.startswith("typescript|")]
    assert len(typescript_rows) == 1
    fields = typescript_rows[0].split("|")
    assert fields[1] == "package.json"
    assert fields[2] == "typescript-lsp@claude-plugins-official"
    assert fields[3] == "typescript-language-server"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_ecosystems.py -v
```
Expected: FAIL with no such file.

- [ ] **Step 3: Write `lib/ecosystems.sh`**

```bash
#!/usr/bin/env bash
# lib/ecosystems.sh: per-ecosystem data table for actually-lsp
# Format: ecosystem|marker|recommended_plugin|server_binary|env_check_cmd
#
# This file is sourced, not executed. It defines the $ecosystems array.

ecosystems=(
  "typescript|package.json|typescript-lsp@claude-plugins-official|typescript-language-server|test -d node_modules"
)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_ecosystems.py -v
```
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/lib/ecosystems.sh plugins/actually-lsp/tests/test_ecosystems.py
git commit -m "feat(actually-lsp): add ecosystems data table with TypeScript entry"
```

## Task 4: detect.sh: ecosystem detection helpers

**Files:**
- Create: `plugins/actually-lsp/lib/detect.sh`
- Test: `plugins/actually-lsp/tests/test_detect.py`

- [ ] **Step 1: Write the failing test**

```python
"""Verify detect.sh's detect_ecosystems function."""

import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
DETECT_SH = PLUGIN_ROOT / "lib" / "detect.sh"


def run_detect(project_dir):
    """Source ecosystems.sh and detect.sh, run detect_ecosystems, return stdout."""
    script = (
        f"source {PLUGIN_ROOT}/lib/ecosystems.sh && "
        f"source {DETECT_SH} && "
        f"detect_ecosystems '{project_dir}'"
    )
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.returncode


def test_detect_sh_exists():
    assert DETECT_SH.exists()


def test_detect_returns_nothing_for_empty_dir(tmp_path):
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert output == ""


def test_detect_finds_typescript(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export const x = 1;")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    lines = output.split("\n")
    ts_lines = [l for l in lines if l.startswith("typescript|")]
    assert len(ts_lines) == 1


def test_detect_skips_typescript_without_ts_files(tmp_path):
    """package.json without any .ts files is not a TypeScript project."""
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.js").write_text("module.exports = {};")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert "typescript|" not in output
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_detect.py -v
```
Expected: FAIL on `assert DETECT_SH.exists()`.

- [ ] **Step 3: Write `lib/detect.sh`**

```bash
#!/usr/bin/env bash
# lib/detect.sh: ecosystem detection helpers for actually-lsp
# Sourced by hooks. Requires $ecosystems array (from lib/ecosystems.sh).

# detect_ecosystems <project_dir>
#   Walks the project dir for ecosystem markers.
#   Emits one line per detected ecosystem: "<ecosystem>|<marker_path>"
detect_ecosystems() {
  local project_dir="${1:-.}"
  local row ecosystem marker recommended_plugin server_binary env_check

  for row in "${ecosystems[@]}"; do
    IFS='|' read -r ecosystem marker recommended_plugin server_binary env_check <<< "$row"

    local marker_path="$project_dir/$marker"
    if [[ ! -f "$marker_path" ]]; then
      continue
    fi

    # TypeScript-specific check: package.json without any .ts/.tsx files in
    # the tree is not a TypeScript project (it's plain JavaScript).
    if [[ "$ecosystem" == "typescript" ]]; then
      if ! find "$project_dir" -maxdepth 4 -type f \( -name "*.ts" -o -name "*.tsx" \) 2>/dev/null | head -1 | grep -q .; then
        continue
      fi
    fi

    echo "$ecosystem|$marker_path"
  done
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_detect.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/lib/detect.sh plugins/actually-lsp/tests/test_detect.py
git commit -m "feat(actually-lsp): add ecosystem detection helper"
```

## Task 5: state.sh: project state file read/write

**Files:**
- Create: `plugins/actually-lsp/lib/state.sh`
- Test: `plugins/actually-lsp/tests/test_state.py`

- [ ] **Step 1: Write the failing test**

```python
"""Verify state.sh's project state file read/write."""

import json
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
STATE_SH = PLUGIN_ROOT / "lib" / "state.sh"


def run_state(script_body, project_dir):
    """Source state.sh and run a script body. Return stdout, returncode."""
    full = f"source {STATE_SH} && PROJECT_DIR='{project_dir}' && {script_body}"
    result = subprocess.run(
        ["bash", "-c", full],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip(), result.returncode


def test_state_sh_exists():
    assert STATE_SH.exists()


def test_write_state_creates_file(tmp_path):
    output, rc = run_state(
        'write_state typescript ready false "$(date -u +%Y-%m-%dT%H:%M:%SZ)" 0 abc123 null',
        tmp_path,
    )
    assert rc == 0
    state_file = tmp_path / ".claude" / "actually-lsp.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["version"] == 1
    assert data["ecosystems"]["typescript"]["state"] == "ready"
    assert data["ecosystems"]["typescript"]["dismissed"] is False


def test_read_state_returns_empty_when_missing(tmp_path):
    output, rc = run_state("read_state typescript state", tmp_path)
    assert rc == 0
    assert output == ""


def test_read_state_returns_value(tmp_path):
    state_dir = tmp_path / ".claude"
    state_dir.mkdir()
    (state_dir / "actually-lsp.json").write_text(json.dumps({
        "version": 1,
        "ecosystems": {
            "typescript": {"state": "ready", "dismissed": False}
        }
    }))
    output, rc = run_state("read_state typescript state", tmp_path)
    assert rc == 0
    assert output == "ready"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_state.py -v
```
Expected: FAIL on missing state.sh.

- [ ] **Step 3: Write `lib/state.sh`**

```bash
#!/usr/bin/env bash
# lib/state.sh: project state file read/write for actually-lsp
# Sourced by hooks. Requires $PROJECT_DIR env var.

_state_file() {
  echo "$PROJECT_DIR/.claude/actually-lsp.json"
}

# read_state <ecosystem> <field>
#   Print the field value, or empty if missing.
read_state() {
  local ecosystem="$1"
  local field="$2"
  local file
  file=$(_state_file)

  if [[ ! -f "$file" ]]; then
    return 0
  fi
  jq -r --arg eco "$ecosystem" --arg f "$field" \
    '.ecosystems[$eco][$f] // empty' "$file" 2>/dev/null || true
}

# write_state <ecosystem> <state> <dismissed> <last_check_at> <last_marker_mtime> <last_plugin_list_hash> <last_error>
#   Atomic: write to temp file, then rename.
write_state() {
  local ecosystem="$1"
  local state="$2"
  local dismissed="$3"
  local last_check_at="$4"
  local last_marker_mtime="$5"
  local last_plugin_list_hash="$6"
  local last_error="$7"

  local file
  file=$(_state_file)
  local dir
  dir=$(dirname "$file")
  mkdir -p "$dir"

  local existing="{}"
  if [[ -f "$file" ]]; then
    existing=$(cat "$file")
  fi

  local tmpfile="$file.tmp.$$"
  echo "$existing" | jq \
    --arg eco "$ecosystem" \
    --arg state "$state" \
    --argjson dismissed "$dismissed" \
    --arg last_check_at "$last_check_at" \
    --argjson last_marker_mtime "$last_marker_mtime" \
    --arg last_plugin_list_hash "$last_plugin_list_hash" \
    --argjson last_error "$last_error" \
    '
      .version = 1 |
      .ecosystems //= {} |
      .ecosystems[$eco] = {
        state: $state,
        dismissed: $dismissed,
        last_check_at: $last_check_at,
        last_marker_mtime: $last_marker_mtime,
        last_plugin_list_hash: $last_plugin_list_hash,
        last_error: $last_error
      }
    ' > "$tmpfile"
  mv "$tmpfile" "$file"
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_state.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/lib/state.sh plugins/actually-lsp/tests/test_state.py
git commit -m "feat(actually-lsp): add project state file read/write"
```

## Task 6: activation/typescript.md

**Files:**
- Create: `plugins/actually-lsp/activation/typescript.md`

- [ ] **Step 1: Write the activation context content**

Use the share-out's bktide cell-2 preamble as the canonical TypeScript version (the one that achieved 4.6/5 at N=5).

```markdown
## LSP context

An LSP server is loaded for this codebase: **typescript-language-server** via the `typescript-lsp` plugin. It can answer:

- `textDocument/definition`: where is this symbol defined?
- `textDocument/references`: where is this symbol used, which classes implement this interface?
- `textDocument/documentSymbol`: what symbols are defined in this file?
- `workspace/symbol`: find a symbol by name anywhere in the workspace.
- `textDocument/hover`: what is the type or signature of this symbol?

The `LSP` tool in this Claude Code session is a **deferred tool**: its schema is not loaded by default. To use it:

1. Call `ToolSearch` with `query: "select:LSP"` to load the LSP tool's schema.
2. Then call `LSP` with the appropriate `operation` (one of those above).

For navigation, definition lookup, and references, prefer LSP over `grep` + `Read`. LSP gives semantic answers that `grep` can't (a `references` query won't miss an inheritance chain the way a `grep` for `implements TokenFormatter` would).
```

- [ ] **Step 2: Verify no em-dashes**

```bash
grep -n '—' plugins/actually-lsp/activation/typescript.md && echo "EM-DASH FOUND" || echo "clean"
```
Expected: `clean`.

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/activation/typescript.md
git commit -m "feat(actually-lsp): add TypeScript activation context"
```

## Task 7: session-start.sh (TypeScript only)

**Files:**
- Create: `plugins/actually-lsp/hooks/session-start.sh`
- Test: `plugins/actually-lsp/tests/test_session_start.py`

- [ ] **Step 1: Write the failing test**

```python
"""Integration tests for the SessionStart hook script."""

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "session-start.sh"


def run_hook(project_dir, plugin_list_output='[]'):
    """Invoke session-start.sh with a fake CLAUDE_PROJECT_DIR and a fake `claude` command."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["CLAUDE_SESSION_ID"] = "test-session-id"

    # Stub `claude plugin list --json` via a fake bin dir on PATH
    fake_bin = project_dir / "_fake_bin"
    fake_bin.mkdir(exist_ok=True)
    fake_claude = fake_bin / "claude"
    fake_claude.write_text(
        f'#!/usr/bin/env bash\nif [[ "$1" == "plugin" && "$2" == "list" ]]; then\n  echo \'{plugin_list_output}\'\nfi\n'
    )
    fake_claude.chmod(0o755)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(HOOK)],
        input="{}",
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def test_hook_exists():
    assert HOOK.exists()


def test_hook_is_executable():
    assert os.access(HOOK, os.X_OK)


def test_hook_silent_when_no_ecosystem(tmp_path):
    """Empty project: no nudge, no activation context."""
    stdout, stderr, rc = run_hook(tmp_path)
    assert rc == 0
    assert stdout.strip() == ""


def test_hook_nudges_when_no_lsp_plugin(tmp_path):
    """TypeScript project with no LSP plugin installed: emit a nudge."""
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export const x = 1;")
    stdout, stderr, rc = run_hook(tmp_path, plugin_list_output='[]')
    assert rc == 0
    assert "typescript-lsp@claude-plugins-official" in stdout
    assert "/actually-lsp:doctor" in stdout


def test_hook_emits_activation_context_when_ready(tmp_path):
    """TypeScript project with LSP plugin + node_modules: emit activation context."""
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export const x = 1;")
    (tmp_path / "node_modules").mkdir()
    plugin_list = json.dumps([
        {"id": "typescript-lsp@claude-plugins-official", "enabled": True}
    ])
    stdout, stderr, rc = run_hook(tmp_path, plugin_list_output=plugin_list)
    assert rc == 0
    # Activation context contains the deferred-tool explanation
    assert "ToolSearch" in stdout
    assert "select:LSP" in stdout
```

NOTE: this test stubs out `typescript-language-server`'s presence on PATH. The hook needs to call `command -v typescript-language-server`. For the test to pass the `ready` case, we need to either install the real binary OR have the hook accept a `ACTUALLY_LSP_SKIP_BINARY_CHECK=1` env override for testing. Pick the latter.

- [ ] **Step 2: Run test to verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_session_start.py -v
```
Expected: FAIL on missing hook script.

- [ ] **Step 3: Write `hooks/session-start.sh`**

```bash
#!/usr/bin/env bash
# hooks/session-start.sh: SessionStart hook for actually-lsp
#
# Detects ecosystems in $CLAUDE_PROJECT_DIR, computes LSP state per ecosystem,
# emits nudges or activation context via additionalContext (stdout).

set -eo pipefail

# Consume stdin (hook receives JSON we don't use)
cat > /dev/null

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=../lib/ecosystems.sh
source "$PLUGIN_ROOT/lib/ecosystems.sh"
# shellcheck source=../lib/detect.sh
source "$PLUGIN_ROOT/lib/detect.sh"
# shellcheck source=../lib/state.sh
source "$PLUGIN_ROOT/lib/state.sh"

# Get plugin list (with 5s timeout and cache fallback per spec)
get_plugin_list() {
  timeout 5s claude plugin list --json 2>/dev/null || echo "[]"
}

# is_plugin_enabled <plugin_id>
is_plugin_enabled() {
  local plugin_id="$1"
  local plugin_list
  plugin_list=$(get_plugin_list)
  echo "$plugin_list" | jq -e --arg id "$plugin_id" \
    '.[] | select(.enabled and .id == $id)' >/dev/null 2>&1
}

# compute_state <ecosystem> <marker_path> <recommended_plugin> <server_binary> <env_check>
compute_state() {
  local ecosystem="$1" marker_path="$2" recommended_plugin="$3" server_binary="$4" env_check="$5"

  # 1. dismissed flag
  if [[ "$(read_state "$ecosystem" "dismissed")" == "true" ]]; then
    echo "dismissed"
    return
  fi

  # 2. LSP plugin enabled?
  if ! is_plugin_enabled "$recommended_plugin"; then
    echo "no-lsp-plugin"
    return
  fi

  # 3. server binary on PATH? (test override available)
  if [[ "${ACTUALLY_LSP_SKIP_BINARY_CHECK:-0}" != "1" ]]; then
    if ! command -v "$server_binary" >/dev/null 2>&1; then
      echo "server-not-runnable"
      return
    fi
  fi

  # 4. env_check passes?
  if ! (cd "$PROJECT_DIR" && eval "$env_check") >/dev/null 2>&1; then
    echo "server-not-runnable"
    return
  fi

  echo "ready"
}

# emit_for_state <ecosystem> <state> <recommended_plugin>
emit_for_state() {
  local ecosystem="$1" state="$2" recommended_plugin="$3"

  case "$state" in
    dismissed|not-detected)
      ;;
    no-lsp-plugin)
      echo "[actually-lsp] Detected $ecosystem. Recommended LSP plugin: $recommended_plugin."
      echo "Run \`/actually-lsp:doctor\` to set up, or \`/actually-lsp:skip $ecosystem\` to dismiss."
      ;;
    server-not-runnable)
      echo "[actually-lsp] $ecosystem LSP plugin installed but env not ready."
      echo "Run \`/actually-lsp:doctor\` to fix."
      ;;
    ready)
      cat "$PLUGIN_ROOT/activation/$ecosystem.md"
      ;;
    error)
      echo "[actually-lsp] Detection failed for $ecosystem. Run \`/actually-lsp:doctor $ecosystem\` for details."
      ;;
  esac
}

# Main loop
detected=$(detect_ecosystems "$PROJECT_DIR")
if [[ -z "$detected" ]]; then
  exit 0
fi

while IFS='|' read -r ecosystem marker_path; do
  # Find the matching ecosystem row to get recommended_plugin, server_binary, env_check
  for row in "${ecosystems[@]}"; do
    IFS='|' read -r e_name e_marker e_plugin e_server e_envcheck <<< "$row"
    if [[ "$e_name" == "$ecosystem" ]]; then
      state=$(compute_state "$ecosystem" "$marker_path" "$e_plugin" "$e_server" "$e_envcheck")
      emit_for_state "$ecosystem" "$state" "$e_plugin"
      # Persist state (trust-but-verify cache populated on next pass)
      now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
      mtime=$(stat -f %m "$marker_path" 2>/dev/null || stat -c %Y "$marker_path" 2>/dev/null || echo 0)
      plugin_hash=$(get_plugin_list | sha256sum | head -c 8)
      write_state "$ecosystem" "$state" false "$now" "$mtime" "$plugin_hash" null
      break
    fi
  done
done <<< "$detected"
```

- [ ] **Step 4: Make the script executable**

```bash
chmod +x plugins/actually-lsp/hooks/session-start.sh
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd plugins/actually-lsp && ACTUALLY_LSP_SKIP_BINARY_CHECK=1 uv run pytest tests/test_session_start.py -v
```
Expected: 5 tests pass. (The ACTUALLY_LSP_SKIP_BINARY_CHECK env var lets the `ready`-state test skip the `command -v` check.)

NOTE: the `test_hook_emits_activation_context_when_ready` test needs the env var set when invoking the hook. Update the test's `run_hook` helper to pass through `ACTUALLY_LSP_SKIP_BINARY_CHECK=1`.

- [ ] **Step 6: Commit**

```bash
git add plugins/actually-lsp/hooks/session-start.sh plugins/actually-lsp/tests/test_session_start.py
git commit -m "feat(actually-lsp): add SessionStart hook with TypeScript detection"
```

## Task 8: hooks.json registers SessionStart

**Files:**
- Create: `plugins/actually-lsp/hooks/hooks.json`
- Test: extend `plugins/actually-lsp/tests/test_plugin_structure.py`

- [ ] **Step 1: Append hooks.json validation tests**

Add this class to `test_plugin_structure.py`:

```python
class TestHooksJson:
    def test_hooks_json_exists(self):
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        assert hooks_path.exists()

    def test_hooks_json_is_valid_json(self):
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        assert "hooks" in data

    def test_session_start_hook_registered(self):
        hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        ss = data["hooks"].get("SessionStart")
        assert ss, "SessionStart hook must be registered"
        assert len(ss) == 1
        cmd = ss[0]["hooks"][0]["command"]
        assert "${CLAUDE_PLUGIN_ROOT}" in cmd
        assert "session-start.sh" in cmd
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_plugin_structure.py -v
```
Expected: FAIL on missing hooks.json.

- [ ] **Step 3: Write `hooks/hooks.json`**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Run tests, verify pass**

```bash
cd plugins/actually-lsp && uv run pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/hooks/hooks.json plugins/actually-lsp/tests/test_plugin_structure.py
git commit -m "feat(actually-lsp): register SessionStart hook in hooks.json"
```

## Task 9: README skeleton

**Files:**
- Create: `plugins/actually-lsp/README.md`

- [ ] **Step 1: Write a terse README**

```markdown
# actually-lsp

Makes Claude Code actually use the LSP tools you've installed.

## Why this exists

Installing an LSP plugin (`rust-analyzer-lsp`, `typescript-lsp`, `ruby-lsp` from `claude-plugins-official`) doesn't change Claude's behavior. Claude defaults to `grep` and `Read` even on tasks where LSP would be better. This is the **activation gap**.

`actually-lsp` detects the state of LSP setup in your project and nudges:

- If you don't have the LSP plugin installed but the project needs it, suggest installing.
- If you have it installed but the environment isn't ready (no `bundle install`, no `cargo build`, etc.), surface that.
- If everything's ready, deliver activation context so Claude reaches for the LSP tool instead of grep.

Full background: [the activation gap share-out](https://github.com/technicalpickles/pickleton/blob/main/projects/claude-test-harness/docs/2026-05-21-lsp-activation-gap-share-out.md).

## Status

Pre-1.0. v1 supports TypeScript. Rust and Ruby coming in 0.2.

## Install

```bash
/plugin install actually-lsp@pickled-claude-plugins
```

Then install the official LSP plugin for your ecosystem:

```bash
/plugin install typescript-lsp@claude-plugins-official
```

Restart Claude Code.

## Configuration

State lives at `<project>/.claude/actually-lsp.json`. Gitignored by default; commit it if you want shared team state.

## Commands

Coming in 0.5:
- `/actually-lsp:doctor`: diagnose and fix LSP setup
- `/actually-lsp:skip`: dismiss nudges for an ecosystem

## Internals

- [CONTEXT.md](CONTEXT.md): vocabulary and state machine
- [docs/adr/](docs/adr/): architectural decisions
- [docs/plans/2026-05-27-design.md](docs/plans/2026-05-27-design.md): design spec
```

- [ ] **Step 2: Verify no em-dashes**

```bash
grep -n '—' plugins/actually-lsp/README.md && echo "EM-DASH" || echo "clean"
```
Expected: `clean`.

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/README.md
git commit -m "feat(actually-lsp): add README skeleton"
```

## Task 10: Register plugin in marketplace.json at version 0.1.0

**Files:**
- Modify: `.claude-plugin/marketplace.json` (at the marketplace repo root)

- [ ] **Step 1: Add the entry**

Open `.claude-plugin/marketplace.json` and add a new entry to the `"plugins"` array. Place alphabetically (between `agent-meta` and `buildkite`):

```json
{
  "name": "actually-lsp",
  "source": "./plugins/actually-lsp",
  "version": "0.1.0"
}
```

- [ ] **Step 2: Validate**

```bash
./scripts/validate-plugin-versions.sh
```
Expected: passes.

- [ ] **Step 3: Commit (chore, no bump since this IS the introductory version)**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(actually-lsp): register plugin at 0.1.0"
```

## PR 1 verification before push

- [ ] All tests pass: `cd plugins/actually-lsp && uv run pytest tests/ -v`
- [ ] Em-dash check: `grep -rn '—' plugins/actually-lsp/ && echo "FOUND" || echo "clean"`
- [ ] Pre-commit hooks pass: `git log --oneline origin/main..HEAD` then verify commit messages all use `feat(actually-lsp): ...` or `chore(actually-lsp): ...`
- [ ] Install locally and verify:
  ```bash
  /plugin uninstall actually-lsp@pickled-claude-plugins 2>/dev/null
  /plugin install actually-lsp@pickled-claude-plugins
  # restart Claude Code
  # cd into a TypeScript project (e.g., bktide) and start a fresh session
  # confirm hook fires and emits expected output
  ```

- [ ] Push branch, open PR with title `feat: add actually-lsp plugin (PR 1: scaffold + TypeScript SessionStart)`, body referencing the design spec.

---

# PR 2: Add Rust and Ruby

**Goal:** Extend ecosystem support to Rust and Ruby with their own activation context files. Same SessionStart hook, just more data.

**Commit scope:** `feat(actually-lsp): ...`. Will trigger a minor bump to 0.2.0.

## Task 11: Extend ecosystems.sh

**Files:**
- Modify: `plugins/actually-lsp/lib/ecosystems.sh`
- Test: extend `plugins/actually-lsp/tests/test_ecosystems.py`

- [ ] **Step 1: Extend test to cover Rust and Ruby**

Add to `test_ecosystems.py`:

```python
def test_ecosystems_sh_defines_rust():
    result = subprocess.run(
        ["bash", "-c", f"source {ECOSYSTEMS_SH} && printf '%s\\n' \"${{ecosystems[@]}}\""],
        capture_output=True, text=True, check=True,
    )
    rust_rows = [l for l in result.stdout.strip().split("\n") if l.startswith("rust|")]
    assert len(rust_rows) == 1
    fields = rust_rows[0].split("|")
    assert fields[1] == "Cargo.toml"
    assert fields[2] == "rust-analyzer-lsp@claude-plugins-official"
    assert fields[3] == "rust-analyzer"


def test_ecosystems_sh_defines_ruby():
    result = subprocess.run(
        ["bash", "-c", f"source {ECOSYSTEMS_SH} && printf '%s\\n' \"${{ecosystems[@]}}\""],
        capture_output=True, text=True, check=True,
    )
    ruby_rows = [l for l in result.stdout.strip().split("\n") if l.startswith("ruby|")]
    assert len(ruby_rows) == 1
    fields = ruby_rows[0].split("|")
    assert fields[1] == "Gemfile"
    assert fields[2] == "ruby-lsp@claude-plugins-official"
    assert fields[3] == "ruby-lsp"
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_ecosystems.py -v
```
Expected: 2 new tests fail.

- [ ] **Step 3: Extend `lib/ecosystems.sh`**

```bash
ecosystems=(
  "typescript|package.json|typescript-lsp@claude-plugins-official|typescript-language-server|test -d node_modules"
  "rust|Cargo.toml|rust-analyzer-lsp@claude-plugins-official|rust-analyzer|cargo metadata --no-deps"
  "ruby|Gemfile|ruby-lsp@claude-plugins-official|ruby-lsp|bundle check"
)
```

- [ ] **Step 4: Run tests, verify pass**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_ecosystems.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/lib/ecosystems.sh plugins/actually-lsp/tests/test_ecosystems.py
git commit -m "feat(actually-lsp): add Rust and Ruby to ecosystems table"
```

## Task 12: Update detect.sh to cover Rust and Ruby

**Files:**
- Modify: `plugins/actually-lsp/lib/detect.sh`
- Test: extend `plugins/actually-lsp/tests/test_detect.py`

The current `detect_ecosystems` already loops over all rows in `$ecosystems`, so Rust and Ruby get picked up automatically by the marker file presence check. Confirm via tests.

- [ ] **Step 1: Add tests for Rust and Ruby detection**

```python
def test_detect_finds_rust(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert any(l.startswith("rust|") for l in output.split("\n"))


def test_detect_finds_ruby(tmp_path):
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    assert any(l.startswith("ruby|") for l in output.split("\n"))


def test_detect_polyglot(tmp_path):
    """Project with all three markers: all three should be detected."""
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export {};")
    output, rc = run_detect(tmp_path)
    assert rc == 0
    lines = output.split("\n")
    assert any(l.startswith("rust|") for l in lines)
    assert any(l.startswith("ruby|") for l in lines)
    assert any(l.startswith("typescript|") for l in lines)
```

- [ ] **Step 2: Run tests, verify pass (no detect.sh changes should be needed)**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_detect.py -v
```
Expected: 7 tests pass.

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/tests/test_detect.py
git commit -m "feat(actually-lsp): add detection tests for Rust and Ruby"
```

## Task 13: Add activation/rust.md

**Files:**
- Create: `plugins/actually-lsp/activation/rust.md`

- [ ] **Step 1: Write the activation context**

```markdown
## LSP context

An LSP server is loaded for this codebase: **rust-analyzer** via the `rust-analyzer-lsp` plugin. It can answer:

- `textDocument/definition`: where is this symbol defined?
- `textDocument/references`: where is this symbol used, which types implement this trait?
- `textDocument/documentSymbol`: what symbols are defined in this file?
- `workspace/symbol`: find a symbol by name anywhere in the workspace.
- `textDocument/hover`: what is the type or signature of this symbol?

The `LSP` tool in this Claude Code session is a **deferred tool**: its schema is not loaded by default. To use it:

1. Call `ToolSearch` with `query: "select:LSP"` to load the LSP tool's schema.
2. Then call `LSP` with the appropriate `operation` (one of those above).

For navigation, definition lookup, and references, prefer LSP over `grep` + `Read`. LSP gives semantic answers `grep` can't (a `references` query won't miss an `impl` block the way a regex would).

**Rust warm-up note:** if `cargo build` hasn't run recently, run it before LSP queries. rust-analyzer's `workspace/symbol` races indexing on cold cache; file-scoped queries (`documentSymbol`, `goToDefinition`) work fine cold but workspace-scoped queries return empty until indexing settles.
```

- [ ] **Step 2: Verify no em-dashes**

```bash
grep -n '—' plugins/actually-lsp/activation/rust.md && echo "EM-DASH" || echo "clean"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/activation/rust.md
git commit -m "feat(actually-lsp): add Rust activation context"
```

## Task 14: Add activation/ruby.md

**Files:**
- Create: `plugins/actually-lsp/activation/ruby.md`

- [ ] **Step 1: Write the activation context**

```markdown
## LSP context

An LSP server is loaded for this codebase: **ruby-lsp** via the `ruby-lsp` plugin. It can answer:

- `textDocument/definition`: where is this symbol defined?
- `textDocument/references`: where is this symbol used, which classes inherit or include this module?
- `textDocument/documentSymbol`: what symbols are defined in this file?
- `workspace/symbol`: find a symbol by name anywhere in the workspace.
- `textDocument/hover`: what is the type or signature of this symbol?

The `LSP` tool in this Claude Code session is a **deferred tool**: its schema is not loaded by default. To use it:

1. Call `ToolSearch` with `query: "select:LSP"` to load the LSP tool's schema.
2. Then call `LSP` with the appropriate `operation` (one of those above).

For navigation and definition lookup, prefer LSP over `grep` + `Read`. LSP walks the gem graph for installed dependencies, so it can resolve into gems your code uses.

**Ruby diagnostics note:** ruby-lsp is pull-only, and Claude Code's LSP client doesn't pull diagnostics. Use LSP for navigation; for rubocop offenses, run `rubocop` directly via Bash.
```

- [ ] **Step 2: Verify no em-dashes**

```bash
grep -n '—' plugins/actually-lsp/activation/ruby.md && echo "EM-DASH" || echo "clean"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/activation/ruby.md
git commit -m "feat(actually-lsp): add Ruby activation context"
```

## Task 15: Extend session-start integration tests for Rust and Ruby

**Files:**
- Modify: `plugins/actually-lsp/tests/test_session_start.py`

- [ ] **Step 1: Add tests**

```python
def test_hook_nudges_for_rust(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    stdout, _, rc = run_hook(tmp_path, plugin_list_output='[]')
    assert rc == 0
    assert "rust-analyzer-lsp@claude-plugins-official" in stdout


def test_hook_nudges_for_ruby(tmp_path):
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    stdout, _, rc = run_hook(tmp_path, plugin_list_output='[]')
    assert rc == 0
    assert "ruby-lsp@claude-plugins-official" in stdout


def test_hook_handles_polyglot(tmp_path):
    """Polyglot project: all three ecosystems get nudged."""
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "src.ts").write_text("export {};")
    stdout, _, rc = run_hook(tmp_path, plugin_list_output='[]')
    assert rc == 0
    assert "rust-analyzer-lsp" in stdout
    assert "typescript-lsp" in stdout
    assert "ruby-lsp" in stdout
```

- [ ] **Step 2: Run tests, verify pass**

```bash
cd plugins/actually-lsp && ACTUALLY_LSP_SKIP_BINARY_CHECK=1 uv run pytest tests/test_session_start.py -v
```
Expected: 8 tests pass.

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/tests/test_session_start.py
git commit -m "feat(actually-lsp): add SessionStart tests for Rust, Ruby, polyglot"
```

## Task 16: Update README to reflect Rust and Ruby support

**Files:**
- Modify: `plugins/actually-lsp/README.md`

- [ ] **Step 1: Replace the status line**

Change `v1 supports TypeScript. Rust and Ruby coming in 0.2.` to `v1 supports TypeScript, Rust, and Ruby.`

- [ ] **Step 2: Commit**

```bash
git add plugins/actually-lsp/README.md
git commit -m "feat(actually-lsp): note Rust and Ruby support in README"
```

## Task 17: Bump version

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Run auto-bump**

```bash
./scripts/bump-version.sh actually-lsp minor
```

- [ ] **Step 2: Verify bump landed**

```bash
jq '.plugins[] | select(.name == "actually-lsp") | .version' .claude-plugin/marketplace.json
```
Expected: `"0.2.0"`.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(actually-lsp): bump version to 0.2.0"
```

## PR 2 verification before push

- [ ] All tests pass: `cd plugins/actually-lsp && ACTUALLY_LSP_SKIP_BINARY_CHECK=1 uv run pytest tests/ -v`
- [ ] Em-dash check: `grep -rn '—' plugins/actually-lsp/ && echo "FOUND" || echo "clean"`
- [ ] Smoke test: install locally, cd into a Rust project, verify nudge or activation context fires
- [ ] Push, open PR titled `feat(actually-lsp): add Rust and Ruby support (PR 2)`

---

# PR 3: PreToolUse hook for deferred detection

**Goal:** Catch cases where the project root isn't the cwd at session start (polyglot workspaces, monorepos). When Claude touches a path in an ecosystem not yet covered by SessionStart, re-detect and emit appropriate output.

## Task 18: Session state file library

**Files:**
- Create: `plugins/actually-lsp/lib/session.sh`
- Test: `plugins/actually-lsp/tests/test_session.py`

- [ ] **Step 1: Write the failing test**

```python
"""Verify session state file read/write."""

import json
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
SESSION_SH = PLUGIN_ROOT / "lib" / "session.sh"


def run_session(script_body, session_id, cache_root):
    """Source session.sh and run a script body."""
    full = (
        f"source {SESSION_SH} && "
        f"CLAUDE_SESSION_ID='{session_id}' "
        f"ACTUALLY_LSP_CACHE_ROOT='{cache_root}' "
        f"{script_body}"
    )
    result = subprocess.run(
        ["bash", "-c", full],
        capture_output=True, text=True,
    )
    return result.stdout.strip(), result.returncode


def test_session_sh_exists():
    assert SESSION_SH.exists()


def test_mark_nudged_adds_entry(tmp_path):
    out, rc = run_session(
        'mark_nudged /foo/bar typescript',
        "test-session", tmp_path,
    )
    assert rc == 0
    files = list((tmp_path / "sessions").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert {"project_root": "/foo/bar", "ecosystem": "typescript"} in data["nudged_ecosystems"]


def test_is_nudged_returns_yes_after_mark(tmp_path):
    run_session('mark_nudged /foo/bar typescript', "test-session", tmp_path)
    out, rc = run_session(
        'if is_nudged /foo/bar typescript; then echo yes; else echo no; fi',
        "test-session", tmp_path,
    )
    assert rc == 0
    assert out == "yes"


def test_is_nudged_returns_no_when_not_marked(tmp_path):
    out, rc = run_session(
        'if is_nudged /foo/bar typescript; then echo yes; else echo no; fi',
        "test-session", tmp_path,
    )
    assert rc == 0
    assert out == "no"
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_session.py -v
```

- [ ] **Step 3: Write `lib/session.sh`**

```bash
#!/usr/bin/env bash
# lib/session.sh: session state file read/write for actually-lsp
# Sourced by hooks. Requires $CLAUDE_SESSION_ID env var.

_session_file() {
  local root="${ACTUALLY_LSP_CACHE_ROOT:-$HOME/.cache/actually-lsp}"
  echo "$root/sessions/${CLAUDE_SESSION_ID}.json"
}

_ensure_session_file() {
  local file
  file=$(_session_file)
  local dir
  dir=$(dirname "$file")
  mkdir -p "$dir"
  if [[ ! -f "$file" ]]; then
    echo "{\"session_id\":\"$CLAUDE_SESSION_ID\",\"nudged_ecosystems\":[]}" > "$file"
  fi
}

# mark_nudged <project_root> <ecosystem>
mark_nudged() {
  local project_root="$1"
  local ecosystem="$2"
  _ensure_session_file
  local file
  file=$(_session_file)
  local tmpfile="$file.tmp.$$"
  jq --arg root "$project_root" --arg eco "$ecosystem" \
    '.nudged_ecosystems += [{project_root: $root, ecosystem: $eco}] | .nudged_ecosystems |= unique' \
    "$file" > "$tmpfile"
  mv "$tmpfile" "$file"
}

# is_nudged <project_root> <ecosystem>: exit 0 if present, exit 1 if not
is_nudged() {
  local project_root="$1"
  local ecosystem="$2"
  local file
  file=$(_session_file)
  if [[ ! -f "$file" ]]; then
    return 1
  fi
  local matches
  matches=$(jq --arg root "$project_root" --arg eco "$ecosystem" \
    '[.nudged_ecosystems[] | select(.project_root == $root and .ecosystem == $eco)] | length' \
    "$file" 2>/dev/null)
  [[ "$matches" -gt 0 ]]
}
```

- [ ] **Step 4: Run tests, verify pass**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_session.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/lib/session.sh plugins/actually-lsp/tests/test_session.py
git commit -m "feat(actually-lsp): add session state file library for dedup tracking"
```

## Task 19: Walk-up project root helper

**Files:**
- Modify: `plugins/actually-lsp/lib/detect.sh`
- Test: extend `plugins/actually-lsp/tests/test_detect.py`

Add a `find_project_root_for_ecosystem` helper that, given a path and an ecosystem, walks up looking for the matching marker.

- [ ] **Step 1: Add the test**

```python
def test_find_project_root_for_typescript(tmp_path):
    """Walking up from a nested path finds the closest package.json ancestor."""
    project = tmp_path / "myproject"
    project.mkdir()
    (project / "package.json").write_text("{}")
    nested = project / "src" / "components"
    nested.mkdir(parents=True)
    nested_file = nested / "Button.tsx"
    nested_file.write_text("export {};")

    script = (
        f"source {PLUGIN_ROOT}/lib/ecosystems.sh && "
        f"source {PLUGIN_ROOT}/lib/detect.sh && "
        f"find_project_root_for_ecosystem '{nested_file}' typescript"
    )
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == str(project)


def test_find_project_root_missing(tmp_path):
    """When no ancestor has the marker, returns empty and exits non-zero."""
    nested = tmp_path / "foo" / "bar"
    nested.mkdir(parents=True)
    script = (
        f"source {PLUGIN_ROOT}/lib/ecosystems.sh && "
        f"source {PLUGIN_ROOT}/lib/detect.sh && "
        f"find_project_root_for_ecosystem '{nested}' typescript"
    )
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert result.returncode != 0
    assert result.stdout.strip() == ""
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_detect.py::test_find_project_root_for_typescript -v
```

- [ ] **Step 3: Add the function to `lib/detect.sh`**

```bash
# find_project_root_for_ecosystem <path> <ecosystem>
#   Walks up from <path> looking for <ecosystem>'s marker file.
#   On success, prints the project root and returns 0.
#   On failure, prints nothing and returns 1.
find_project_root_for_ecosystem() {
  local path="$1"
  local ecosystem="$2"

  # Look up the marker for this ecosystem
  local marker=""
  local row
  for row in "${ecosystems[@]}"; do
    IFS='|' read -r e_name e_marker _ _ _ <<< "$row"
    if [[ "$e_name" == "$ecosystem" ]]; then
      marker="$e_marker"
      break
    fi
  done
  [[ -z "$marker" ]] && return 1

  # Walk up
  local current
  if [[ -d "$path" ]]; then
    current="$path"
  else
    current=$(dirname "$path")
  fi

  while [[ "$current" != "/" && -n "$current" ]]; do
    if [[ -f "$current/$marker" ]]; then
      echo "$current"
      return 0
    fi
    current=$(dirname "$current")
  done
  return 1
}
```

- [ ] **Step 4: Run tests, verify pass**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_detect.py -v
```

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/lib/detect.sh plugins/actually-lsp/tests/test_detect.py
git commit -m "feat(actually-lsp): add walk-up project-root helper for deferred detection"
```

## Task 20: PreToolUse hook script

**Files:**
- Create: `plugins/actually-lsp/hooks/pre-tool-use.sh`
- Test: `plugins/actually-lsp/tests/test_pre_tool_use.py`

- [ ] **Step 1: Write the failing test**

```python
"""Integration tests for the PreToolUse hook."""

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "pre-tool-use.sh"


def run_hook(tool_input, project_dir, cache_root, plugin_list_output='[]'):
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["CLAUDE_SESSION_ID"] = "test-pretool-session"
    env["ACTUALLY_LSP_CACHE_ROOT"] = str(cache_root)
    env["ACTUALLY_LSP_SKIP_BINARY_CHECK"] = "1"

    fake_bin = project_dir / "_fake_bin"
    fake_bin.mkdir(exist_ok=True)
    fake_claude = fake_bin / "claude"
    fake_claude.write_text(
        f'#!/usr/bin/env bash\nif [[ "$1" == "plugin" && "$2" == "list" ]]; then\n  echo \'{plugin_list_output}\'\nfi\n'
    )
    fake_claude.chmod(0o755)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(tool_input),
        capture_output=True, text=True, env=env,
    )
    return result.stdout, result.stderr, result.returncode


def test_hook_exists():
    assert HOOK.exists()


def test_hook_silent_when_path_has_no_ecosystem(tmp_path):
    """Touching a path with no ancestor marker is a no-op."""
    cache = tmp_path / "_cache"
    tool_input = {
        "tool_name": "Read",
        "tool_input": {"file_path": str(tmp_path / "foo.txt")},
    }
    stdout, _, rc = run_hook(tool_input, tmp_path, cache)
    assert rc == 0
    assert stdout.strip() == ""


def test_hook_fires_for_new_ecosystem(tmp_path):
    """First touch of a TypeScript file in a new project: nudge fires."""
    project = tmp_path / "myproj"
    project.mkdir()
    (project / "package.json").write_text("{}")
    (project / "src.ts").write_text("export {};")
    cache = tmp_path / "_cache"
    tool_input = {
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src.ts")},
    }
    stdout, _, rc = run_hook(tool_input, tmp_path, cache, plugin_list_output='[]')
    assert rc == 0
    assert "typescript-lsp@claude-plugins-official" in stdout


def test_hook_dedups_within_session(tmp_path):
    """Second touch of the same ecosystem is silent."""
    project = tmp_path / "myproj"
    project.mkdir()
    (project / "package.json").write_text("{}")
    (project / "src.ts").write_text("export {};")
    cache = tmp_path / "_cache"
    tool_input = {
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src.ts")},
    }
    # First fire
    run_hook(tool_input, tmp_path, cache, plugin_list_output='[]')
    # Second fire (different file in same project)
    tool_input2 = {
        "tool_name": "Read",
        "tool_input": {"file_path": str(project / "src2.ts")},
    }
    stdout, _, rc = run_hook(tool_input2, tmp_path, cache, plugin_list_output='[]')
    assert rc == 0
    assert stdout.strip() == ""
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_pre_tool_use.py -v
```

- [ ] **Step 3: Write `hooks/pre-tool-use.sh`**

```bash
#!/usr/bin/env bash
# hooks/pre-tool-use.sh: PreToolUse hook for deferred detection.
#
# Reads tool args, extracts candidate paths, walks up to find ecosystem roots,
# fires nudges or activation context for any (root, ecosystem) not yet nudged
# this session.

set -eo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=../lib/ecosystems.sh
source "$PLUGIN_ROOT/lib/ecosystems.sh"
# shellcheck source=../lib/detect.sh
source "$PLUGIN_ROOT/lib/detect.sh"
# shellcheck source=../lib/state.sh
source "$PLUGIN_ROOT/lib/state.sh"
# shellcheck source=../lib/session.sh
source "$PLUGIN_ROOT/lib/session.sh"

# Read tool input from stdin
tool_input=$(cat)

# Extract candidate paths from tool args
extract_paths() {
  local input="$1"
  local tool_name
  tool_name=$(echo "$input" | jq -r '.tool_name // empty')

  case "$tool_name" in
    Read|Edit|Write)
      echo "$input" | jq -r '.tool_input.file_path // empty'
      ;;
    Glob|Grep)
      echo "$input" | jq -r '.tool_input.path // empty'
      ;;
    Bash)
      # Parse `cd <target>` if present, otherwise first absolute path in command
      local cmd
      cmd=$(echo "$input" | jq -r '.tool_input.command // empty')
      if [[ "$cmd" =~ cd[[:space:]]+([^[:space:]\&\|\;]+) ]]; then
        echo "${BASH_REMATCH[1]}"
      else
        echo "$cmd" | grep -oE '/[^[:space:]\&\|\;]+' | head -1
      fi
      ;;
  esac
}

candidate_path=$(extract_paths "$tool_input")
if [[ -z "$candidate_path" ]]; then
  exit 0
fi

# For each ecosystem, see if the candidate path has a project root for it
output=""
for row in "${ecosystems[@]}"; do
  IFS='|' read -r e_name e_marker e_plugin e_server e_envcheck <<< "$row"

  project_root=$(find_project_root_for_ecosystem "$candidate_path" "$e_name" 2>/dev/null || echo "")
  if [[ -z "$project_root" ]]; then
    continue
  fi

  if is_nudged "$project_root" "$e_name"; then
    continue
  fi

  # Compute state and emit. (Reuse session-start's emit logic via a sourced helper or
  # inline the simple cases here. For now, inline minimal output to keep this PR small;
  # full state-machine reuse can be a follow-up refactor.)
  PROJECT_DIR="$project_root"

  # Check plugin enablement
  plugin_list=$(timeout 5s claude plugin list --json 2>/dev/null || echo "[]")
  if echo "$plugin_list" | jq -e --arg id "$e_plugin" \
       '.[] | select(.enabled and .id == $id)' >/dev/null 2>&1; then
    # Plugin enabled: emit activation context with the caveat
    output+="[actually-lsp] Detected $e_name workspace at $project_root."$'\n'
    output+="$(cat "$PLUGIN_ROOT/activation/$e_name.md")"$'\n\n'
    output+="(Activation context at PreToolUse position lands soft (0.4/5 per share-out). For inline-rate activation (4.6/5), run \`/actually-lsp:doctor\` to load the context at user-prompt position.)"$'\n'
  else
    # No plugin: nudge
    output+="[actually-lsp] Detected $e_name workspace at $project_root. Recommended LSP plugin: $e_plugin."$'\n'
    output+="Run \`/actually-lsp:doctor\` to set up, or \`/actually-lsp:skip $e_name\` to dismiss."$'\n'
  fi

  mark_nudged "$project_root" "$e_name"
done

if [[ -n "$output" ]]; then
  echo "$output"
fi
```

- [ ] **Step 4: chmod and run tests**

```bash
chmod +x plugins/actually-lsp/hooks/pre-tool-use.sh
cd plugins/actually-lsp && ACTUALLY_LSP_SKIP_BINARY_CHECK=1 uv run pytest tests/test_pre_tool_use.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/hooks/pre-tool-use.sh plugins/actually-lsp/tests/test_pre_tool_use.py
git commit -m "feat(actually-lsp): add PreToolUse hook for deferred detection"
```

## Task 21: Register PreToolUse in hooks.json

**Files:**
- Modify: `plugins/actually-lsp/hooks/hooks.json`
- Test: extend `tests/test_plugin_structure.py`

- [ ] **Step 1: Add test for PreToolUse registration**

```python
def test_pre_tool_use_hook_registered(self):
    hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
    data = json.loads(hooks_path.read_text())
    pre = data["hooks"].get("PreToolUse")
    assert pre, "PreToolUse hook must be registered"
    # Match all tools (no matcher restriction) since we examine args inside the script
    cmd = pre[0]["hooks"][0]["command"]
    assert "pre-tool-use.sh" in cmd
```

- [ ] **Step 2: Run test, verify it fails**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_plugin_structure.py::TestHooksJson::test_pre_tool_use_hook_registered -v
```

- [ ] **Step 3: Update hooks.json**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/pre-tool-use.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Run all tests**

```bash
cd plugins/actually-lsp && ACTUALLY_LSP_SKIP_BINARY_CHECK=1 uv run pytest tests/ -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/hooks/hooks.json plugins/actually-lsp/tests/test_plugin_structure.py
git commit -m "feat(actually-lsp): register PreToolUse hook"
```

## Task 22: Bump version

- [ ] **Step 1: Bump**

```bash
./scripts/bump-version.sh actually-lsp minor
```

- [ ] **Step 2: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(actually-lsp): bump version to 0.3.0"
```

## PR 3 verification before push

- [ ] All tests pass
- [ ] Em-dash check clean
- [ ] Smoke test in pickletown: cd into pt root, then `cd repos/bktide/worktrees/main && ls`. Verify PreToolUse fires nudge or activation context for TypeScript.
- [ ] Push, open PR titled `feat(actually-lsp): add PreToolUse hook for deferred detection (PR 3)`

---

# PR 4: PostToolUseFailure hook for failure context

**Goal:** When an LSP tool call fails, emit failure context to Claude and invalidate the cache for that ecosystem.

## Task 23: PostToolUseFailure hook script

**Files:**
- Create: `plugins/actually-lsp/hooks/post-tool-use-failure.sh`
- Test: `plugins/actually-lsp/tests/test_post_tool_use_failure.py`

- [ ] **Step 1: Write the failing test**

```python
"""Integration tests for the PostToolUseFailure hook."""

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "post-tool-use-failure.sh"


def run_hook(tool_input, project_dir):
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["CLAUDE_SESSION_ID"] = "test-pt-failure"
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(tool_input),
        capture_output=True, text=True, env=env,
    )
    return result.stdout, result.stderr, result.returncode


def test_hook_exists():
    assert HOOK.exists()


def test_hook_silent_for_non_lsp_tool(tmp_path):
    """A Bash failure: not our concern."""
    tool_input = {
        "tool_name": "Bash",
        "tool_response": {"error": "something failed"},
    }
    stdout, _, rc = run_hook(tool_input, tmp_path)
    assert rc == 0
    assert stdout.strip() == ""


def test_hook_emits_failure_context_for_lsp(tmp_path):
    """LSP call to rust-analyzer fails: emit failure context naming Rust."""
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    tool_input = {
        "tool_name": "LSP",
        "tool_input": {"lspServer": "rust-analyzer", "method": "workspace/symbol"},
        "tool_response": {"error": "EPIPE: broken pipe"},
    }
    stdout, _, rc = run_hook(tool_input, tmp_path)
    assert rc == 0
    assert "rust" in stdout.lower()
    assert "EPIPE" in stdout
    assert "/actually-lsp:doctor" in stdout


def test_hook_invalidates_cached_state(tmp_path):
    """After failure context fires, state file for that ecosystem is marked error."""
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"foo\"\n")
    state_dir = tmp_path / ".claude"
    state_dir.mkdir()
    (state_dir / "actually-lsp.json").write_text(json.dumps({
        "version": 1,
        "ecosystems": {"rust": {"state": "ready", "dismissed": False}},
    }))

    tool_input = {
        "tool_name": "LSP",
        "tool_input": {"lspServer": "rust-analyzer", "method": "workspace/symbol"},
        "tool_response": {"error": "EPIPE: broken pipe"},
    }
    run_hook(tool_input, tmp_path)

    data = json.loads((state_dir / "actually-lsp.json").read_text())
    assert data["ecosystems"]["rust"]["state"] == "error"
    assert "EPIPE" in data["ecosystems"]["rust"]["last_error"]
```

- [ ] **Step 2: Run test, verify it fails**

- [ ] **Step 3: Write `hooks/post-tool-use-failure.sh`**

```bash
#!/usr/bin/env bash
# hooks/post-tool-use-failure.sh: PostToolUseFailure hook for actually-lsp.
#
# Fires only on LSP tool failures. Emits failure context to Claude and
# marks the affected ecosystem's state as `error` in the project state file.

set -eo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=../lib/ecosystems.sh
source "$PLUGIN_ROOT/lib/ecosystems.sh"
# shellcheck source=../lib/state.sh
source "$PLUGIN_ROOT/lib/state.sh"

tool_input=$(cat)
tool_name=$(echo "$tool_input" | jq -r '.tool_name // empty')

# Only act on LSP failures
if [[ "$tool_name" != "LSP" ]]; then
  exit 0
fi

lsp_server=$(echo "$tool_input" | jq -r '.tool_input.lspServer // empty')
method=$(echo "$tool_input" | jq -r '.tool_input.method // empty')
error_msg=$(echo "$tool_input" | jq -r '.tool_response.error // empty')

# Map LSP server to ecosystem
ecosystem=""
for row in "${ecosystems[@]}"; do
  IFS='|' read -r e_name _ _ e_server _ <<< "$row"
  if [[ "$e_server" == "$lsp_server" ]]; then
    ecosystem="$e_name"
    break
  fi
done

if [[ -z "$ecosystem" ]]; then
  exit 0
fi

# Emit failure context
cat <<EOF
[actually-lsp] LSP call to $method on $lsp_server failed:
$error_msg

Cache for $ecosystem has been invalidated. Run \`/actually-lsp:doctor $ecosystem\` to re-verify.
EOF

# Mark state as error (keep dismissed flag if set)
now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
dismissed=$(read_state "$ecosystem" "dismissed")
[[ -z "$dismissed" ]] && dismissed="false"
escaped_error=$(echo "$error_msg" | jq -Rs .)
write_state "$ecosystem" "error" "$dismissed" "$now" 0 "" "$escaped_error"
```

- [ ] **Step 4: chmod and run tests**

```bash
chmod +x plugins/actually-lsp/hooks/post-tool-use-failure.sh
cd plugins/actually-lsp && uv run pytest tests/test_post_tool_use_failure.py -v
```

- [ ] **Step 5: Commit**

```bash
git add plugins/actually-lsp/hooks/post-tool-use-failure.sh plugins/actually-lsp/tests/test_post_tool_use_failure.py
git commit -m "feat(actually-lsp): add PostToolUseFailure hook for failure context"
```

## Task 24: Register PostToolUseFailure in hooks.json

**Files:**
- Modify: `plugins/actually-lsp/hooks/hooks.json`
- Test: extend `tests/test_plugin_structure.py`

- [ ] **Step 1: Add test**

```python
def test_post_tool_use_failure_registered(self):
    hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
    data = json.loads(hooks_path.read_text())
    ptf = data["hooks"].get("PostToolUseFailure")
    assert ptf
    # Matched to LSP tool only
    assert ptf[0].get("matcher") == "LSP"
    cmd = ptf[0]["hooks"][0]["command"]
    assert "post-tool-use-failure.sh" in cmd
```

- [ ] **Step 2: Update hooks.json**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"}
        ]
      }
    ],
    "PreToolUse": [
      {
        "hooks": [
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/pre-tool-use.sh"}
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "LSP",
        "hooks": [
          {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/post-tool-use-failure.sh"}
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add plugins/actually-lsp/hooks/hooks.json plugins/actually-lsp/tests/test_plugin_structure.py
git commit -m "feat(actually-lsp): register PostToolUseFailure hook for LSP failures"
```

## Task 25: Bump version

```bash
./scripts/bump-version.sh actually-lsp minor
git add .claude-plugin/marketplace.json
git commit -m "chore(actually-lsp): bump version to 0.4.0"
```

## PR 4 verification before push

- [ ] All tests pass
- [ ] Em-dash check clean
- [ ] Push, open PR titled `feat(actually-lsp): add PostToolUseFailure hook (PR 4)`

---

# PR 5: Skills (user-invocable slash actions)

**Goal:** `/actually-lsp:doctor` and `/actually-lsp:skip` available.

**Note:** These ship as skills (`skills/<name>/SKILL.md`), not plugin commands. Claude Code surfaces skills for `/plugin:skill` invocation; plugin `commands/<name>.md` files are not surfaced. The skill `description:` field is what triggers it, so write it as a "use when X" sentence covering the likely contexts (post-nudge from SessionStart, missing plugin, env not ready, explicit slash invocation).

## Task 26: skills/doctor/SKILL.md

**Files:**
- Create: `plugins/actually-lsp/skills/doctor/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: doctor
description: Diagnose and fix LSP setup for the current project's detected ecosystems (Rust, TypeScript, Ruby). Use when the SessionStart hook nudged about a missing LSP plugin, when the env isn't ready (no `bundle install`, no `cargo build`, missing server binary), when LSP calls are failing, or when the user invokes `/actually-lsp:doctor` directly. Walks the per-ecosystem state machine, reports what's missing, then runs the fix.
---

You are running `/actually-lsp:doctor`. Parse the user's args from the command invocation:

- "fix" as the first arg means skip the diagnostic report and jump straight to action.
- "rust" | "typescript" | "ruby" as an arg narrows focus to that ecosystem.
- No args: full diagnostic report followed by interactive fix.

## Step 1: Read project state

Read `.claude/actually-lsp.json` in the current project root. If missing, run detection: source `lib/detect.sh` and `lib/ecosystems.sh` from the plugin root (the env var `CLAUDE_PLUGIN_ROOT` points there), call `detect_ecosystems "$PWD"`, and for each detected ecosystem compute the current state per the rules in CONTEXT.md.

## Step 2: Diagnose (unless "fix" arg present)

Output a per-ecosystem report. For each ecosystem:

- State (from CONTEXT.md's six states)
- For non-`ready` ecosystems: what's needed to reach `ready`
- For `dismissed` ecosystems: note them but don't propose action

Keep tone terse. No celebration messaging.

## Step 3: Act

For each ecosystem in `no-lsp-plugin`, `server-not-runnable`, or `error`:

**`no-lsp-plugin`**: try `claude plugin install <recommended_plugin>@claude-plugins-official` via Bash. The user gets a permission prompt. If denied, output the slash command form (`/plugin install <recommended_plugin>@claude-plugins-official`) and ask the user to run it themselves.

**`server-not-runnable`**: run env fixes per ecosystem via Bash. All env fixes auto-run; the user has implicit project consent.
- Rust: `cargo build`
- TypeScript: `npm install`
- Ruby: `bundle install`, plus `gem install ruby-lsp` if `command -v ruby-lsp` is empty

**`error`**: surface the cached `last_error` from the state file. Ask the user how to proceed.

## Step 4: Re-detect and report

Re-run detection (same as Step 1's "if missing" path). Update the project state file. Output a final per-ecosystem status line.
```

- [ ] **Step 2: Em-dash check**

```bash
grep -n '—' plugins/actually-lsp/skills/doctor/SKILL.md && echo "EM-DASH" || echo "clean"
```

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/skills/doctor/SKILL.md
git commit -m "feat(actually-lsp): add /actually-lsp:doctor skill"
```

## Task 27: skills/skip/SKILL.md

**Files:**
- Create: `plugins/actually-lsp/skills/skip/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: skip
description: Dismiss actually-lsp nudges for an ecosystem in this project. Use when the user wants to silence, dismiss, or skip the LSP setup nudges for a specific ecosystem (Rust, TypeScript, Ruby), or invokes `/actually-lsp:skip` directly. Writes `dismissed=true` to `.claude/actually-lsp.json`. Persistent across sessions for this project only.
---

You are running `/actually-lsp:skip`. Parse args:

- "rust" | "typescript" | "ruby" as an arg dismisses that ecosystem directly.
- No args: read `.claude/actually-lsp.json` in the current project root, present the detected ecosystems, and ask the user which to dismiss.

## Action

Update the project state file at `.claude/actually-lsp.json`: set `.ecosystems.<ecosystem>.dismissed` to `true`. If the file doesn't exist, create it with version 1 schema.

## Confirmation output

Output a one-line confirmation per dismissed ecosystem:

```
Dismissed <ecosystem> for this project. To re-enable, manually edit .claude/actually-lsp.json and set dismissed back to false. (An `unskip` command is a future extension.)
```
```

- [ ] **Step 2: Commit**

```bash
git add plugins/actually-lsp/skills/skip/SKILL.md
git commit -m "feat(actually-lsp): add /actually-lsp:skip skill"
```

## Task 28: Test skill files exist with expected frontmatter

**Files:**
- Modify: `plugins/actually-lsp/tests/test_plugin_structure.py`

- [ ] **Step 1: Add tests**

```python
class TestSkills:
    def test_doctor_skill_exists(self):
        path = PLUGIN_ROOT / "skills" / "doctor" / "SKILL.md"
        assert path.exists()
        content = path.read_text()
        assert "name: doctor" in content
        assert "description:" in content

    def test_skip_skill_exists(self):
        path = PLUGIN_ROOT / "skills" / "skip" / "SKILL.md"
        assert path.exists()
        content = path.read_text()
        assert "name: skip" in content
        assert "description:" in content
```

- [ ] **Step 2: Run tests, verify pass**

```bash
cd plugins/actually-lsp && uv run pytest tests/test_plugin_structure.py -v
```

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/tests/test_plugin_structure.py
git commit -m "feat(actually-lsp): test skill files exist with frontmatter"
```

## Task 29: Bump version

```bash
./scripts/bump-version.sh actually-lsp minor
git add .claude-plugin/marketplace.json
git commit -m "chore(actually-lsp): bump version to 0.5.0"
```

## PR 5 verification before push

- [ ] All tests pass
- [ ] Em-dash check clean across the plugin
- [ ] Smoke test: install locally, invoke `/actually-lsp:doctor` in a project with no LSP plugin installed; verify Claude follows the skill's diagnostic + action flow
- [ ] Push, open PR titled `feat(actually-lsp): add /doctor and /skip slash actions (PR 5)`

---

# PR 6: Polish

**Goal:** Full README, smoke test plan documentation, version bump to 1.0.0, optional benchmark script.

## Task 30: Flesh out README

**Files:**
- Modify: `plugins/actually-lsp/README.md`

Add: usage examples per ecosystem, expected output samples, link to CONTEXT.md and design spec, troubleshooting section.

- [ ] **Step 1: Replace README with the full version**

(Write a complete README. Sections: Why, Install, Quickstart per ecosystem, Commands, Configuration, Troubleshooting, Internals.)

Keep it under 200 lines. No em-dashes.

- [ ] **Step 2: Em-dash check and commit**

```bash
grep -n '—' plugins/actually-lsp/README.md && echo "EM-DASH" || echo "clean"
git add plugins/actually-lsp/README.md
git commit -m "feat(actually-lsp): flesh out README with usage and troubleshooting"
```

## Task 31: Smoke test plan doc

**Files:**
- Create: `plugins/actually-lsp/docs/smoke-tests.md`

- [ ] **Step 1: Write the doc**

Documents the manual test plan against bktide (TypeScript), welcome2u (Rust), homesick (Ruby): expected output per state per ecosystem, how to verify activation rate stays in line with the share-out's data (TypeScript ~4.6/5, Rust ~3/5 with warm-up).

- [ ] **Step 2: Commit**

```bash
git add plugins/actually-lsp/docs/smoke-tests.md
git commit -m "feat(actually-lsp): add manual smoke test plan"
```

## Task 32: PreToolUse benchmark script

**Files:**
- Create: `plugins/actually-lsp/tests/bench_pre_tool_use.py`

The design spec calls for measuring cumulative PreToolUse overhead. This is a benchmark script (not a regular test) that:
1. Sets up a realistic project tree
2. Fires the hook 100 times across various tool calls
3. Reports cumulative time and p99 per-fire latency

- [ ] **Step 1: Write the benchmark**

```python
"""Benchmark: cumulative PreToolUse hook overhead.

Run manually: uv run pytest tests/bench_pre_tool_use.py -s
"""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "pre-tool-use.sh"


@pytest.mark.skip(reason="Benchmark, run manually with -s")
def test_benchmark_cumulative_overhead(tmp_path):
    project = tmp_path / "myproj"
    project.mkdir()
    (project / "package.json").write_text("{}")
    (project / "src.ts").write_text("export {};")

    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["CLAUDE_SESSION_ID"] = "bench-session"
    env["ACTUALLY_LSP_CACHE_ROOT"] = str(tmp_path / "_cache")
    env["ACTUALLY_LSP_SKIP_BINARY_CHECK"] = "1"

    durations = []
    for i in range(100):
        # Simulate Read on different .ts files in the same project
        ts_file = project / f"file{i}.ts"
        ts_file.write_text("export {};")
        tool_input = {"tool_name": "Read", "tool_input": {"file_path": str(ts_file)}}
        start = time.perf_counter()
        subprocess.run(
            ["bash", str(HOOK)],
            input=json.dumps(tool_input),
            capture_output=True, text=True, env=env,
        )
        durations.append(time.perf_counter() - start)

    durations.sort()
    print(f"\nCumulative: {sum(durations):.3f}s across 100 fires")
    print(f"Mean: {1000*sum(durations)/len(durations):.1f}ms")
    print(f"p50: {1000*durations[50]:.1f}ms")
    print(f"p99: {1000*durations[99]:.1f}ms")
    print(f"Max: {1000*durations[-1]:.1f}ms")

    assert sum(durations) < 5.0, "Cumulative > 5s over 100 fires, consider memoization"
```

- [ ] **Step 2: Run benchmark, capture results**

```bash
cd plugins/actually-lsp && uv run pytest tests/bench_pre_tool_use.py -s --no-header
```
Document results in the PR description.

- [ ] **Step 3: Commit**

```bash
git add plugins/actually-lsp/tests/bench_pre_tool_use.py
git commit -m "feat(actually-lsp): add PreToolUse benchmark script"
```

## Task 33: Bump to 1.0.0

```bash
./scripts/bump-version.sh actually-lsp major
git add .claude-plugin/marketplace.json
git commit -m "chore(actually-lsp): bump version to 1.0.0"
```

## PR 6 verification before push

- [ ] All tests pass
- [ ] Benchmark documented in PR description
- [ ] Em-dash check across entire plugin: `grep -rn '—' plugins/actually-lsp/`
- [ ] Push, open PR titled `feat(actually-lsp): polish + 1.0.0 release (PR 6)`

---

## Plan-wide verification (after all six PRs merged)

- [ ] Marketplace entry shows `"version": "1.0.0"`
- [ ] Full smoke test pass per `docs/smoke-tests.md` against bktide, welcome2u, homesick
- [ ] Activation rate on bktide: ~4.6/5 over 5 sessions (re-replicates the share-out's measurement)
- [ ] No regressions: existing pickled-claude-plugins plugins still work

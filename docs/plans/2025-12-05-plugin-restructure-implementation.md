# Plugin Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure plugins around clearer domains and add skill-level route discovery.

**Architecture:** Update tool-routing to discover routes from `plugins/*/skills/*/tool-routes.yaml`, then restructure plugins by consolidating mcpproxy skills, merging debugging-tools into dev-tools, renaming skills to verb-action format, and moving routes to colocate with their skills.

**Tech Stack:** Python (tool-routing), YAML (routes), Markdown (skills)

---

## Phase 1: Tool-Routing Skill-Level Discovery

### Task 1: Add test for skill-level route discovery

**Files:**
- Modify: `plugins/tool-routing/tests/test_discovery.py`

**Step 1: Write the failing test**

```python
def test_discovers_skill_level_routes(tmp_path, monkeypatch):
    """Routes in plugins/*/skills/*/tool-routes.yaml are discovered."""
    # Create skill-level route file
    skill_routes = tmp_path / "plugins" / "test-plugin" / "skills" / "test-skill"
    skill_routes.mkdir(parents=True)
    (skill_routes / "tool-routes.yaml").write_text("""
routes:
  skill-route:
    tool: Bash
    pattern: "skill-pattern"
    message: "Skill route message"
""")

    monkeypatch.setenv("CLAUDE_PLUGINS_DIR", str(tmp_path / "plugins"))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(tmp_path / "tool-routing"))

    from tool_routing.discovery import discover_routes
    routes = discover_routes()

    assert "skill-route" in routes
    assert routes["skill-route"]["tool"] == "Bash"
    assert "skills/test-skill" in routes["skill-route"]["source"]
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/tool-routing && uv run pytest tests/test_discovery.py::test_discovers_skill_level_routes -v`
Expected: FAIL (test doesn't exist yet or discovery doesn't find skill routes)

**Step 3: Implement skill-level discovery**

Modify `plugins/tool-routing/src/tool_routing/discovery.py`:

Find the `_discover_plugin_routes` function and update to also glob skill-level routes:

```python
def _discover_plugin_routes(plugins_dir: Path) -> dict[str, RouteDict]:
    """Discover routes from all plugins in directory."""
    routes: dict[str, RouteDict] = {}

    # Plugin-level routes: plugins/*/hooks/tool-routes.yaml
    for route_file in plugins_dir.glob("*/hooks/tool-routes.yaml"):
        plugin_routes = _load_route_file(route_file)
        routes = _merge_routes(routes, plugin_routes)

    # Skill-level routes: plugins/*/skills/*/tool-routes.yaml
    for route_file in plugins_dir.glob("*/skills/*/tool-routes.yaml"):
        skill_routes = _load_route_file(route_file)
        routes = _merge_routes(routes, skill_routes)

    return routes
```

**Step 4: Run test to verify it passes**

Run: `cd plugins/tool-routing && uv run pytest tests/test_discovery.py::test_discovers_skill_level_routes -v`
Expected: PASS

**Step 5: Run all discovery tests**

Run: `cd plugins/tool-routing && uv run pytest tests/test_discovery.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add plugins/tool-routing/src/tool_routing/discovery.py plugins/tool-routing/tests/test_discovery.py
git commit -m "feat(tool-routing): add skill-level route discovery"
```

---

### Task 2: Update list command to show skill-level sources

**Files:**
- Modify: `plugins/tool-routing/src/tool_routing/commands/list_cmd.py` (or wherever list is implemented)

**Step 1: Verify list command shows source paths**

Run: `cd plugins/tool-routing && uv run tool-routing list`
Expected: Shows source paths for each route

**Step 2: Create a test skill-level route to verify display**

Create temporary file to test (will be replaced by actual routes later):
```bash
mkdir -p plugins/tool-routing/skills/test-skill
cat > plugins/tool-routing/skills/test-skill/tool-routes.yaml << 'EOF'
routes:
  test-skill-route:
    tool: Bash
    pattern: "test"
    message: "Test message"
EOF
```

**Step 3: Run list and verify skill path appears**

Run: `cd plugins/tool-routing && uv run tool-routing list`
Expected: Shows `test-skill-route` with source containing `skills/test-skill`

**Step 4: Clean up test file**

```bash
rm -rf plugins/tool-routing/skills/test-skill
```

**Step 5: Commit (if changes were needed)**

If list command needed changes:
```bash
git add plugins/tool-routing/src/tool_routing/commands/
git commit -m "feat(tool-routing): show skill-level paths in list output"
```

---

### Task 3: Update route-discovery.md documentation

**Files:**
- Modify: `plugins/tool-routing/docs/route-discovery.md`

**Step 1: Update discovery order section**

Find the "Discovery Order" section and update:

```markdown
## Discovery Order

Routes are discovered and merged in this order:

1. **This plugin's routes** - `<plugin_root>/hooks/tool-routes.yaml`
2. **Other plugins' skill-level routes** - `<plugins_dir>/*/skills/*/tool-routes.yaml`
3. **Other plugins' plugin-level routes** - `<plugins_dir>/*/hooks/tool-routes.yaml`
4. **Project-local routes** - `<project_root>/.claude/tool-routes.yaml`
```

**Step 2: Add skill-level routes section**

Add after "Plugin Routes" section:

```markdown
### Skill-Level Routes

Skills can contribute their own routes by placing a `tool-routes.yaml` in the skill directory:

```
plugins/
├── git-workflows/
│   └── skills/
│       └── writing-pull-requests/
│           ├── SKILL.md
│           └── tool-routes.yaml    ← Skill-level routes
```

Skill-level routes are ideal when:
- The route guards or enforces the skill's domain
- The route's message should reference the skill
- The route only makes sense in context of the skill

All `tool-routes.yaml` files found in `$CLAUDE_PLUGINS_DIR/*/skills/*/` are loaded.
```

**Step 3: Commit**

```bash
git add plugins/tool-routing/docs/route-discovery.md
git commit -m "docs(tool-routing): document skill-level route discovery"
```

---

## Phase 2: Create mcpproxy Plugin

### Task 4: Create mcpproxy plugin structure

**Files:**
- Create: `plugins/mcpproxy/skills/working-with-mcp/SKILL.md`
- Create: `plugins/mcpproxy/skills/working-with-mcp/tool-routes.yaml`

**Step 1: Create directory structure**

```bash
mkdir -p plugins/mcpproxy/skills/working-with-mcp
```

**Step 2: Read existing mcpproxy skills for reference**

Read these files to understand what to merge:
- `plugins/debugging-tools/skills/mcpproxy-debug/SKILL.md`
- `plugins/dev-tools/skills/using-mcpproxy-tools/SKILL.md`

**Step 3: Create merged SKILL.md**

Create `plugins/mcpproxy/skills/working-with-mcp/SKILL.md` combining the content from both skills. Focus on the usage patterns from using-mcpproxy-tools since mcpproxy-debug is outdated.

**Step 4: Create skill-level routes**

Create `plugins/mcpproxy/skills/working-with-mcp/tool-routes.yaml`:

```yaml
routes:
  bash-mcp-cli:
    tool: Bash
    pattern: "^\\s*mcp\\s+"
    message: |
      Don't use Bash to call the 'mcp' CLI.

      The 'mcp' command is not available. Use MCP tools directly:

      1. Discover tools: mcp__MCPProxy__retrieve_tools
      2. Call a tool: mcp__MCPProxy__call_tool

      Example:
      mcp__MCPProxy__retrieve_tools(query="buildkite build status")
      mcp__MCPProxy__call_tool(name="buildkite:get_build", args_json=...)

      Consider using the working-with-mcp skill for guidance.
    tests:
      - desc: "mcp list-tools should block"
        input:
          tool_name: Bash
          tool_input:
            command: "mcp list-tools"
        expect: block
      - desc: "mcp search should block"
        input:
          tool_name: Bash
          tool_input:
            command: "  mcp search foo"
        expect: block

  bash-mcp-tool:
    tool: Bash
    pattern: "^\\s*mcp__"
    message: |
      Don't use Bash to call MCP tool functions.

      MCP tools like 'mcp__MCPProxy__retrieve_tools' are tool calls, not Bash commands.

      Use the tool directly:
      - mcp__MCPProxy__retrieve_tools (tool call)
      - mcp__MCPProxy__call_tool (tool call)

      NOT as Bash commands.
    tests:
      - desc: "mcp__MCPProxy should block"
        input:
          tool_name: Bash
          tool_input:
            command: "mcp__MCPProxy__retrieve_tools"
        expect: block
```

**Step 5: Copy any supporting files**

Check for scripts, references, etc. in the source skills and copy if still relevant.

**Step 6: Run route tests**

```bash
cd plugins/tool-routing && uv run tool-routing test
```
Expected: All tests pass including new mcpproxy routes

**Step 7: Commit**

```bash
git add plugins/mcpproxy/
git commit -m "feat: create mcpproxy plugin with working-with-mcp skill"
```

---

### Task 5: Remove old mcpproxy skills

**Files:**
- Delete: `plugins/debugging-tools/skills/mcpproxy-debug/`
- Delete: `plugins/dev-tools/skills/using-mcpproxy-tools/`

**Step 1: Remove mcpproxy-debug**

```bash
rm -rf plugins/debugging-tools/skills/mcpproxy-debug
```

**Step 2: Remove using-mcpproxy-tools**

```bash
rm -rf plugins/dev-tools/skills/using-mcpproxy-tools
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove old mcpproxy skills (moved to mcpproxy plugin)"
```

---

## Phase 3: Consolidate debugging-tools into dev-tools

### Task 6: Move scope skill to dev-tools

**Files:**
- Move: `plugins/debugging-tools/skills/scope/` → `plugins/dev-tools/skills/working-with-scope/`

**Step 1: Move and rename**

```bash
git mv plugins/debugging-tools/skills/scope plugins/dev-tools/skills/working-with-scope
```

**Step 2: Commit**

```bash
git commit -m "refactor: move scope to dev-tools as working-with-scope"
```

---

### Task 7: Delete debugging-tools plugin

**Files:**
- Delete: `plugins/debugging-tools/`

**Step 1: Verify debugging-tools is empty**

```bash
ls plugins/debugging-tools/skills/
```
Expected: Empty or only contains mcpproxy-debug (already removed)

**Step 2: Remove plugin**

```bash
rm -rf plugins/debugging-tools
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove debugging-tools plugin (consolidated into dev-tools)"
```

---

## Phase 4: Rename Skills

### Task 8: Rename gh-pr to writing-pull-requests

**Files:**
- Move: `plugins/git-workflows/skills/gh-pr/` → `plugins/git-workflows/skills/writing-pull-requests/`

**Step 1: Rename**

```bash
git mv plugins/git-workflows/skills/gh-pr plugins/git-workflows/skills/writing-pull-requests
```

**Step 2: Commit**

```bash
git commit -m "refactor: rename gh-pr to writing-pull-requests"
```

---

### Task 9: Rename git-preferences-and-practices to writing-git-commits

**Files:**
- Move: `plugins/git-workflows/skills/git-preferences-and-practices/` → `plugins/git-workflows/skills/writing-git-commits/`

**Step 1: Rename**

```bash
git mv plugins/git-workflows/skills/git-preferences-and-practices plugins/git-workflows/skills/writing-git-commits
```

**Step 2: Commit**

```bash
git commit -m "refactor: rename git-preferences-and-practices to writing-git-commits"
```

---

### Task 10: Rename buildkite-status to monitoring-buildkite-builds

**Files:**
- Move: `plugins/ci-cd-tools/skills/buildkite-status/` → `plugins/ci-cd-tools/skills/monitoring-buildkite-builds/`

**Step 1: Rename**

```bash
git mv plugins/ci-cd-tools/skills/buildkite-status plugins/ci-cd-tools/skills/monitoring-buildkite-builds
```

**Step 2: Commit**

```bash
git commit -m "refactor: rename buildkite-status to monitoring-buildkite-builds"
```

---

### Task 11: Rename api-documentation-discovery to finding-api-docs

**Files:**
- Move: `plugins/dev-tools/skills/api-documentation-discovery/` → `plugins/dev-tools/skills/finding-api-docs/`

**Step 1: Rename**

```bash
git mv plugins/dev-tools/skills/api-documentation-discovery plugins/dev-tools/skills/finding-api-docs
```

**Step 2: Commit**

```bash
git commit -m "refactor: rename api-documentation-discovery to finding-api-docs"
```

---

## Phase 5: Move Routes to Skills

### Task 12: Create git-workflows skill routes

**Files:**
- Create: `plugins/git-workflows/skills/writing-pull-requests/tool-routes.yaml`

**Step 1: Create route file**

Create `plugins/git-workflows/skills/writing-pull-requests/tool-routes.yaml`:

```yaml
routes:
  github-pr:
    tool: WebFetch
    pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"
    message: |
      Use `gh pr view <number>` for GitHub PRs.

      This works for both public and private PRs and
      provides better formatting than HTML scraping.

      Consider using the writing-pull-requests skill for PR workflows.
    tests:
      - desc: "PR URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar/pull/123"
        expect: block
        contains: "gh pr view"
      - desc: "repo URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar"
        expect: allow
      - desc: "issues URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar/issues/123"
        expect: allow

  git-commit-multiline:
    tool: Bash
    pattern: "git\\s+commit\\s+.*(?:(?:-m\\s+[\"'][^\"']*[\"'].*-m)|(?:\\$\\(cat\\s*<<)|(?:<<[-]?\\s*['\"]?\\w+['\"]?))"
    message: |
      Don't use multiple -m flags or heredocs for git commit messages.

      For multiline commit messages:
        1. Use Write tool to create a commit message file in .tmp/
        2. Use git commit -F <file> to read from the file

      Example:
        Write(file_path=".tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt", content="Title\n\nBody")
        git commit -F .tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt
    tests:
      - desc: "multiple -m flags should block"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"Title\" -m \"Body\""
        expect: block
      - desc: "heredoc should block"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"$(cat <<'EOF'\nTitle\nEOF\n)\""
        expect: block
      - desc: "single -m should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -m \"Simple message\""
        expect: allow
      - desc: "-F with file should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "git commit -F .tmp/commit-msg.txt"
        expect: allow

  gh-pr-create-multiline:
    tool: Bash
    pattern: "gh\\s+pr\\s+(?:create|edit)\\s+.*--body\\s+[\"'](?:[^\"']*\\\\n|\\$\\(cat\\s*<<)"
    message: |
      Don't use multiline strings or heredocs for gh pr --body.

      For multiline PR descriptions:
        1. Use Write tool to create a PR body file in .tmp/
        2. Use gh pr create --body-file <file>

      Example:
        Write(file_path=".tmp/pr-body-YYYY-MM-DD-HHMMSS.md", content="## Summary\n...")
        gh pr create --title "Title" --body-file .tmp/pr-body-YYYY-MM-DD-HHMMSS.md
    tests:
      - desc: "body with literal \\n should block"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr create --title \"Title\" --body \"## Summary\\n\\nDetails\""
        expect: block
      - desc: "heredoc body should block"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr create --title \"Title\" --body \"$(cat <<'EOF'\n## Summary\nEOF\n)\""
        expect: block
      - desc: "--body-file should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr create --title \"Title\" --body-file .tmp/pr-body.md"
        expect: allow
      - desc: "simple --body should allow"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr create --title \"Title\" --body \"Simple description\""
        expect: allow
      - desc: "gh pr edit with multiline body should block"
        input:
          tool_name: Bash
          tool_input:
            command: "gh pr edit 123 --body \"Summary\\nDetails\""
        expect: block
```

**Step 2: Run tests**

```bash
cd plugins/tool-routing && uv run tool-routing test
```
Expected: All tests pass

**Step 3: Commit**

```bash
git add plugins/git-workflows/skills/writing-pull-requests/tool-routes.yaml
git commit -m "feat(git-workflows): add skill-level routes for writing-pull-requests"
```

---

### Task 13: Create buildkite skill routes

**Files:**
- Create: `plugins/ci-cd-tools/skills/monitoring-buildkite-builds/tool-routes.yaml`

**Step 1: Create route file**

Create `plugins/ci-cd-tools/skills/monitoring-buildkite-builds/tool-routes.yaml`:

```yaml
routes:
  buildkite:
    tool: WebFetch
    pattern: "https?://buildkite\\.com/[^/]+/[^/]+/builds/\\d+"
    message: |
      Use Buildkite MCP tools for build information.

      Call: mcp__MCPProxy__retrieve_tools
      Query: 'buildkite build status pipeline'

      MCP tools provide authentication and structured build data.

      Consider using the monitoring-buildkite-builds skill for guidance.
    tests:
      - desc: "build URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://buildkite.com/myorg/mypipeline/builds/123"
        expect: block
      - desc: "pipeline URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://buildkite.com/myorg/mypipeline"
        expect: allow
```

**Step 2: Run tests**

```bash
cd plugins/tool-routing && uv run tool-routing test
```
Expected: All tests pass

**Step 3: Commit**

```bash
git add plugins/ci-cd-tools/skills/monitoring-buildkite-builds/tool-routes.yaml
git commit -m "feat(ci-cd-tools): add skill-level routes for monitoring-buildkite-builds"
```

---

### Task 14: Create dev-tools plugin-level routes

**Files:**
- Create: `plugins/dev-tools/hooks/tool-routes.yaml`

**Step 1: Create hooks directory if needed**

```bash
mkdir -p plugins/dev-tools/hooks
```

**Step 2: Create route file**

Create `plugins/dev-tools/hooks/tool-routes.yaml`:

```yaml
routes:
  atlassian:
    tool: WebFetch
    pattern: "https?://[^/]*\\.atlassian\\.net"
    message: |
      Use Atlassian MCP tools for Jira/Confluence.

      Call: mcp__MCPProxy__retrieve_tools
      Query: 'jira confluence atlassian issue'

      MCP tools provide authentication and structured data.
    tests:
      - desc: "Jira URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://mycompany.atlassian.net/browse/PROJ-123"
        expect: block
      - desc: "Confluence URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://mycompany.atlassian.net/wiki/spaces/DOC/pages/123"
        expect: block
```

**Step 3: Run tests**

```bash
cd plugins/tool-routing && uv run tool-routing test
```
Expected: All tests pass

**Step 4: Commit**

```bash
git add plugins/dev-tools/hooks/tool-routes.yaml
git commit -m "feat(dev-tools): add atlassian route at plugin level"
```

---

### Task 15: Remove moved routes from tool-routing

**Files:**
- Modify: `plugins/tool-routing/hooks/tool-routes.yaml`

**Step 1: Remove routes that moved**

Edit `plugins/tool-routing/hooks/tool-routes.yaml` and remove these routes:
- `github-pr`
- `git-commit-multiline`
- `gh-pr-create-multiline`
- `buildkite`
- `atlassian`
- `bash-mcp-cli`
- `bash-mcp-tool`

Keep only:
- `bash-cat-heredoc`
- `bash-echo-chained`
- `bash-echo-redirect`
- `tool-routing-manual-test`

**Step 2: Run all route tests**

```bash
cd plugins/tool-routing && uv run tool-routing test
```
Expected: All tests pass (routes now discovered from new locations)

**Step 3: Commit**

```bash
git add plugins/tool-routing/hooks/tool-routes.yaml
git commit -m "refactor(tool-routing): remove routes moved to skill locations"
```

---

## Phase 6: Verification

### Task 16: Verify final structure

**Step 1: Check plugin structure**

```bash
tree -L 4 plugins/
```

Expected structure:
```
plugins/
├── ci-cd-tools/
│   └── skills/
│       ├── developing-buildkite-pipelines/
│       └── monitoring-buildkite-builds/
│           ├── SKILL.md
│           └── tool-routes.yaml
├── dev-tools/
│   ├── hooks/
│   │   └── tool-routes.yaml
│   └── skills/
│       ├── designing-clis/
│       ├── finding-api-docs/
│       ├── working-in-scratch-areas/
│       └── working-with-scope/
├── git-workflows/
│   └── skills/
│       ├── writing-git-commits/
│       └── writing-pull-requests/
│           ├── SKILL.md
│           └── tool-routes.yaml
├── mcpproxy/
│   └── skills/
│       └── working-with-mcp/
│           ├── SKILL.md
│           └── tool-routes.yaml
├── tool-routing/
│   └── hooks/
│       └── tool-routes.yaml
└── working-in-monorepos/
```

**Step 2: Run all route tests**

```bash
cd plugins/tool-routing && uv run tool-routing test
```
Expected: 30 tests pass (same count, routes just relocated)

**Step 3: List all routes with sources**

```bash
cd plugins/tool-routing && uv run tool-routing list
```
Expected: Routes show correct skill-level and plugin-level sources

**Step 4: Verify no debugging-tools**

```bash
ls plugins/debugging-tools 2>&1
```
Expected: "No such file or directory"

---

### Task 17: Update marketplace.json (if exists)

**Files:**
- Modify: `.claude-plugin/marketplace.json` (if it exists)

**Step 1: Check if file exists**

```bash
cat .claude-plugin/marketplace.json 2>/dev/null || echo "File not found"
```

**Step 2: If exists, update plugin list**

Remove `debugging-tools`, add `mcpproxy`:

```json
{
  "plugins": [
    {"name": "working-in-monorepos", "source": "./plugins/working-in-monorepos"},
    {"name": "git-workflows", "source": "./plugins/git-workflows"},
    {"name": "ci-cd-tools", "source": "./plugins/ci-cd-tools"},
    {"name": "dev-tools", "source": "./plugins/dev-tools"},
    {"name": "mcpproxy", "source": "./plugins/mcpproxy"},
    {"name": "tool-routing", "source": "./plugins/tool-routing"}
  ]
}
```

**Step 3: Commit if changed**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: update marketplace.json with restructured plugins"
```

---

### Task 18: Final commit and summary

**Step 1: Check for any uncommitted changes**

```bash
git status
```

**Step 2: Create summary commit if needed**

If there are loose ends:
```bash
git add -A
git commit -m "chore: complete plugin restructure"
```

**Step 3: Review commit log**

```bash
git log --oneline main..HEAD
```

Expected: Series of focused commits for each phase

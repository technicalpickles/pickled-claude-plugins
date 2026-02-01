# Fix CLI Test Isolation Issue

**Problem:** CLI tests in `tests/test_cli.py` fail when run together due to route name conflicts between pytest temp directories.

**Root Cause:** The `derive_plugins_dir()` function walks up the directory tree looking for "plugin-like siblings" (directories with `hooks/` subdirs). When pytest creates temp directories like:
```
/tmp/pytest-of-user/pytest-0/
├── test_cli_check_allows_non_matc0/hooks/tool-routes.yaml
├── test_cli_check_blocks_matching0/hooks/tool-routes.yaml
├── test_cli_list_shows_routes0/hooks/tool-routes.yaml
└── ...
```

These sibling test directories all contain `hooks/tool-routes.yaml` files, and many use the same route name `test-route`. When `derive_plugins_dir` finds these siblings, it treats them as plugins and tries to load their routes, causing `RouteConflictError`.

**Reproduction:**
```bash
# Fails - multiple tests create conflicting routes
uv run pytest tests/test_cli.py -v

# Passes - single test in isolation
uv run pytest tests/test_cli.py::test_cli_list_shows_routes -v
```

---

## Task 1: Use Unique Route Names Per Test

**Files:**
- Modify: `tests/test_cli.py`

**Step 1: Update each test to use a unique route name**

Replace generic `test-route` with test-specific names:

```python
# In test_cli_check_blocks_matching_route
routes:
  check-blocks-route:  # was: test-route
    tool: WebFetch
    ...

# In test_cli_check_allows_non_matching
routes:
  check-allows-route:  # was: test-route
    tool: WebFetch
    ...

# In test_cli_test_runs_fixtures
routes:
  fixtures-route:  # was: test-route
    tool: WebFetch
    ...

# etc for each test
```

**Step 2: Run tests to verify fix**

```bash
uv run pytest tests/test_cli.py -v
```

**Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "fix(tool-routing): use unique route names in CLI tests to prevent conflicts"
```

---

## Task 2: Consider Test Isolation Improvement (Optional)

**Alternative approach:** Modify `derive_plugins_dir()` to be more conservative about what it considers a "plugin-like" directory, or add an env var to disable sibling discovery in tests.

This is lower priority since unique route names solve the immediate problem.

---

## Affected Tests

All tests in `tests/test_cli.py` that create `hooks/tool-routes.yaml`:
- `test_cli_check_blocks_matching_route`
- `test_cli_check_allows_non_matching`
- `test_cli_test_runs_fixtures`
- `test_cli_test_reports_failures`
- `test_cli_list_shows_routes`
- `test_cli_list_includes_craftdesk_skills`

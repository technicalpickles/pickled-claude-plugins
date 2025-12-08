# Retrospective: gh pr Multiline Body Routing Rule

**Date:** 2025-12-05
**Task:** Update tool routing rule for `gh pr create/edit` to catch multiline strings in `--body` arguments, similar to `git commit -m`
**Outcome:** ✅ Successful - All tests passing

## What Went Well

### 1. Clear User Direction
The user provided a specific reference point ("similar to git commit with -m") which gave immediate context for what pattern to implement. This made the initial approach straightforward.

### 2. Early User Correction Prevented Wrong Direction
**Critical moment:** After the first implementation, the user caught a fundamental misunderstanding:
- **Agent's assumption:** `gh pr` supports multiple `--body` flags (like `git commit -m` supports multiple `-m`)
- **Reality:** `gh pr --body` takes a single string; the issue is multiline strings with `\n` escapes
- **Impact:** User correction at line selection saved significant time

This correction happened early (before extensive testing) and prevented implementing the wrong pattern.

### 3. Existing Test Infrastructure
The tool-routing plugin's built-in testing framework was invaluable:
- Pattern tests in YAML validated regex logic immediately
- Integration tests confirmed runtime behavior end-to-end
- No manual testing with pipes/stdin needed (user redirected away from this approach)

### 4. User Knowledge of Testing Tools
When the agent attempted manual testing with `echo | uv run tool-routing check`, the user redirected to use the proper testing infrastructure. This shows the plugin's testing framework is both available and preferred.

## What Didn't Go Well

### 1. Initial Misunderstanding of `gh pr` Behavior
**Error:** Agent assumed `gh pr` worked like `git commit` with multiple flag calls.

**Root cause:** Pattern matching without understanding the actual tool's API. The agent looked at `git commit -m -m` and directly applied the same model to `gh pr --body --body`.

**Evidence of the error:**
- First implementation included pattern: `(?:--body\s+[\"'][^\"']*[\"'].*--body)`
- Test case added: `"multiple --body flags should block"`
- This test would never fire in practice because `gh pr` doesn't support multiple `--body` flags

**What should have happened:** Agent should have checked `gh pr create --help` output first (which was eventually done) to understand the actual API before implementing the pattern.

### 2. Attempted Manual Testing with stdin
**What happened:** After implementing the rule, agent tried to manually test by piping JSON to `uv run tool-routing check`:
```bash
echo '{"tool_name": "Bash", ...}' | uv run tool-routing check
```

**Why this was wrong:**
- The plugin has a proper test infrastructure (`tool-routing test` and `tool-routing integration-test`)
- Manual testing is error-prone (JSON escaping issues, no visibility into failures)
- Tests in YAML are version-controlled and repeatable

**User intervention:** Correctly redirected to use tool-routing's testing capacity instead of manual piping.

### 3. Hook Rejection During Manual Test Attempt
**What happened:** One `printf` command with JSON was rejected by a hook.

**Why:** The tool-routing plugin itself was blocking the command (likely the echo/output patterns).

**Irony:** The tool-routing plugin blocked an attempt to manually test tool-routing. This validated that hooks work, but also showed the manual testing approach was flawed from the start.

## Corrections Made

### Correction #1: Pattern Logic (User-Initiated)
**Before:**
```regex
gh\s+pr\s+(?:create|edit)\s+.*(?:(?:--body\s+["'][^"']*["'].*--body)|...)
```
Looked for multiple `--body` flags

**After:**
```regex
gh\s+pr\s+(?:create|edit)\s+.*--body\s+["'](?:[^"']*\\n|\$(cat\s*<<)
```
Looks for `\n` escape sequences or heredocs within a single `--body` argument

**Test cases updated:**
- Removed: "multiple --body flags should block"
- Added: "body with literal \n should block"

### Correction #2: Testing Approach (User-Initiated)
**Before:** Attempted manual stdin piping with `echo | uv run tool-routing check`

**After:** Used proper test commands:
- `uv run tool-routing test` - Pattern matching tests
- `uv run tool-routing integration-test` - End-to-end runtime tests with subagents

## Hook Redirections

### Hook #1: Blocked printf with JSON
**Command attempted:**
```bash
printf '{"tool_name": "Bash", ...}' | uv run tool-routing check
```

**Result:** Hook blocked the command

**Analysis:** This demonstrated:
1. Hooks are working correctly
2. Manual testing approach conflicted with the plugin's own routing rules
3. User's suggestion to use proper testing infrastructure was correct

No other hooks fired during this session - the agent mostly read files and used proper testing tools after the initial correction.

## Validation Results

### Pattern Tests
```
25 passed, 0 failed
```
All inline YAML test fixtures passed, including 5 new `gh pr` tests.

### Plugin Structure Tests
```
13 passed in 0.03s
```
Plugin manifest and hooks format validated correctly.

### Integration Tests
```
25 passed, 0 failed
```
Full end-to-end tests with subagent confirmed hooks fire correctly at runtime.

**Key validation:** Tests 14, 15, 18 specifically validated the new `gh pr` multiline body blocking:
- Test 14: `gh pr create --body "Summary\nDetails"` → blocked ✓
- Test 15: `gh pr create --body "$(cat <<'EOF'...)"` → blocked ✓
- Test 18: `gh pr edit 123 --body "Summary\nDetails"` → blocked ✓

## Lessons Learned

### For Agent Workflows

1. **Understand the tool before implementing the rule**
   - Check `--help` output or documentation first
   - Don't assume Tool A works like Tool B just because they solve similar problems
   - `git commit` and `gh pr create` both take messages, but their APIs differ

2. **Use existing test infrastructure**
   - Don't reinvent testing with manual stdin piping
   - Version-controlled tests (YAML fixtures) are better than ad-hoc manual tests
   - If a user says "use the testing capacity," there's probably a good reason

3. **Early user feedback is valuable**
   - User caught the conceptual error before extensive implementation
   - Line selection + correction saved significant debugging time

### For Plugin Design

1. **Test infrastructure paid off**
   - Both pattern tests and integration tests caught issues immediately
   - Subagent-based integration testing validated runtime behavior
   - Having both levels of testing (unit + integration) gave confidence

2. **Documentation worked**
   - `docs/plans/` directory had clear integration testing design
   - `commands/validate.md` provided step-by-step validation workflow
   - Agent could find and follow the testing process

3. **Hook recursion is interesting**
   - The tool-routing plugin almost blocked itself during manual testing
   - Plugins with PreToolUse hooks need careful consideration of their own testing approaches

## Summary

**Success factors:**
- Clear user requirements with reference point (git commit)
- Early user correction prevented wrong implementation
- Excellent test infrastructure (pattern + integration tests)
- User knowledge redirected to proper testing tools

**Improvement opportunities:**
- Agent should check tool documentation before assuming behavior
- Agent should recognize and use existing test frameworks
- Less manual testing, more use of built-in tooling

**Final result:** 25/25 integration tests passing, new rule working correctly for all `gh pr create/edit` multiline body scenarios.

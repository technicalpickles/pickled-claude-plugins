# Tool Routing Heredoc in Git Commit - Experience Retrospective

## What Happened

While attempting to commit changes for the new echo chaining routing rule, I tried to use a heredoc in a git commit command:

```bash
git add ... && git commit -m "$(cat <<'EOF'
Add tool routing to prevent chained echo for user communication

Adds routing rule to block 3+ chained echo commands with &&, which
indicates using Bash for display/communication rather than shell operations.
...
EOF
)" && git status
```

The tool routing hook blocked this command with:

```
❌ Tool Routing: bash-cat-heredoc
Pattern: cat\s+.*<<[-]?\s*['"]?\w+['"]?(?!.*\|)

Don't use cat with heredocs for file creation or display.
```

## What the Agent Observed

1. **The block was correct according to the pattern**: The command matched `cat <<EOF` without a pipe
2. **But the context was legitimate**: Using heredoc for git commit messages via command substitution is a valid shell idiom
3. **The pattern couldn't distinguish intent**: The regex doesn't know if the heredoc is for:
   - File creation (should block)
   - User display (should block)
   - Command argument construction (legitimate use case)

## What the Agent Chose to Do

Rather than try to refine the pattern to accommodate this edge case, I chose the pragmatic solution:

**Used multiple `-m` flags instead of heredoc:**
```bash
git commit -m "Title" -m "Paragraph 1" -m "Paragraph 2" ...
```

## Rationale for This Choice

1. **Pattern complexity vs. value tradeoff**:
   - Detecting "heredoc inside command substitution" requires complex lookahead/lookbehind
   - This is an uncommon use case in Claude's typical workflow
   - The git system prompt already instructs to use `-m` with HEREDOC example, not command substitution

2. **Fail-safe principle**:
   - The routing hook follows "fail open" design - better to have false positives than miss real issues
   - Blocking a legitimate but uncommon pattern is acceptable if alternatives exist

3. **Workaround is simple**:
   - Multiple `-m` flags achieve the same result
   - Actually more explicit and doesn't require shell quoting knowledge
   - Consistent with git best practices

## Potential Future Considerations

If this becomes a frequent issue, the pattern could be refined to:
- Detect command substitution context: `\$\(\s*cat\s*<<`
- Allow heredocs inside `$()` or backticks
- Pattern: `(?<!\$\()\s*cat\s+.*<<[-]?\s*['"]?\w+['"]?(?!.*\|)`

However, the added complexity may not be worth it given:
- Rarity of this use case
- Availability of simple workarounds
- Risk of over-fitting the pattern

## Lesson Learned

**Good routing rules are specific enough to catch real problems but loose enough to allow legitimate patterns.** When a legitimate use case gets blocked:

1. Assess frequency: Is this common or edge case?
2. Evaluate workaround: Is there a simple alternative?
3. Consider complexity: Does accommodating it make the pattern fragile?
4. Document the decision: Explain why the tradeoff makes sense

In this case, keeping the simpler pattern and documenting the workaround is the right balance.

---

## Resolution (2025-12-01)

After further consideration, we implemented a better solution that addresses the root issue: **git and gh commands should use file-based commit/PR messages instead of any inline heredoc approach.**

### What We Did

Created two new specific routing rules that come **before** the generic `bash-cat-heredoc` rule:

1. **`git-commit-multiline`**: Blocks `git commit` with multiple `-m` flags or heredocs
   - Guides toward: `Write(file_path="/tmp/commit-msg.txt", ...)` + `git commit -F /tmp/commit-msg.txt`
   - Catches: `git commit -m "..." -m "..."` and `git commit -m "$(cat <<EOF...)"`

2. **`gh-pr-create-multiline`**: Blocks `gh pr create` with heredocs
   - Guides toward: `Write(file_path="/tmp/pr-body.md", ...)` + `gh pr create --body-file /tmp/pr-body.md`
   - Catches: `gh pr create --body "$(cat <<EOF...)"`

### Why This Is Better

**Route ordering solves the problem:**
- The hook checks routes in order and returns on **first match**
- Specific git/gh rules now come before generic `bash-cat-heredoc` rule
- Git/gh commands get targeted, helpful messages about `-F` and `--body-file`
- Other heredoc uses still get caught by the generic rule

**Benefits of file-based approach:**
- Commit/PR messages are reviewable before executing the command
- No shell quoting or escaping complexity
- Better error handling (file persists if command fails)
- More testable and debuggable

**Original workaround (multiple `-m`) is now blocked too:**
- Multiple `-m` flags are hard to read and review
- File-based approach is cleaner for all multiline messages

### Updated Documentation

- Added "Route Ordering" section explaining first-match behavior
- Added full examples for both git-commit and gh-pr-create patterns
- Emphasized ordering principle: specific before generic

### Test Results

All scenarios work correctly:
- ✅ `git commit -m "..." -m "..." -m "..."` → Blocked by `git-commit-multiline`
- ✅ `git commit -m "$(cat <<EOF...)"` → Blocked by `git-commit-multiline`
- ✅ `gh pr create --body "$(cat <<EOF...)"` → Blocked by `gh-pr-create-multiline`
- ✅ `cat <<EOF > file.txt` → Blocked by `bash-cat-heredoc` (generic fallback)
- ✅ `git commit -F /tmp/msg.txt` → Allowed (correct approach)
- ✅ `gh pr create --body-file /tmp/body.md` → Allowed (correct approach)

### Final Takeaway

Sometimes the right solution isn't to make patterns more complex to accommodate edge cases, but to create **specific rules that guide toward better practices**. The file-based approach is superior to any inline heredoc method, so we guide Claude toward it consistently for git and gh commands.

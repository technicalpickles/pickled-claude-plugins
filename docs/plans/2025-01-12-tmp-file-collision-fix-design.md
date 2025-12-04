# Tool Routing Temporary File Collision Fix

**Date:** 2025-01-12
**Status:** Approved

## Problem

Multiple projects/worktrees using the tool routing rules try to write to `/tmp` with the same filenames (e.g., `/tmp/commit-msg.txt`, `/tmp/pr-body.md`), causing collisions when working across multiple worktrees simultaneously.

## Solution

Use project-local `.tmp/` directories with timestamped filenames to ensure uniqueness and avoid collisions.

## Design Decisions

### 1. Location: Project-Local `.tmp/` Directory

- Create `.tmp/` in the project root (current working directory)
- The Write tool creates the directory automatically if needed
- No special setup or checking required
- Files stay local to the project (easier to find and debug)

**Rejected alternatives:**
- System `/tmp/` with timestamps: Less discoverable, mixed with system temp files
- `.git/.tmp/` or worktree-specific paths: Too complex, doesn't work for non-git contexts

### 2. Filename Pattern: `{operation}-{YYYY-MM-DD-HHMMSS}.{ext}`

Examples:
- `commit-msg-2025-01-12-143022.txt`
- `pr-body-2025-01-12-143045.md`

**Benefits:**
- Human-readable timestamp
- Naturally sorts chronologically in directory listings
- Second-level precision (sufficient for Claude's operation rate)
- Easy to identify which operation and when

**Rejected alternatives:**
- Unix epoch timestamps: Less readable, harder to debug
- Millisecond precision: Unnecessary complexity
- Session/process IDs: Harder to understand at a glance

### 3. Scope: Git Commit and GitHub PR Only (For Now)

Apply the pattern to these two routing rules:
- `git-commit-multiline`
- `gh-pr-create-multiline`

Future expansion possible, but YAGNI for now.

### 4. Cleanup: No Automatic Cleanup

Let files accumulate in `.tmp/`. Users can manually delete when needed.

**Rationale:**
- Small text files, not a real storage concern
- Useful for debugging failed commits/PRs
- Users can `rm -rf .tmp/` anytime
- Avoids complexity of tracking file lifecycle

### 5. Gitignore: Documentation Only

Document that users should add `.tmp/` to their global gitignore.

**Rationale:**
- Modifying user's git config automatically feels invasive
- Most developers already have global gitignore set up
- Simple documentation is clear and lets users decide
- Users who don't set it up will just see `.tmp/` as untracked (not harmful)

## Implementation

### Modified Routing Rules

Update two rules in `plugins/dev-tools/hooks/tool-routes.json`:

#### `git-commit-multiline`

Change from:
```
Write(file_path="/tmp/commit-msg.txt", content="...")
git commit -F /tmp/commit-msg.txt
```

To:
```
Write(file_path=".tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt", content="...")
git commit -F .tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt
```

#### `gh-pr-create-multiline`

Change from:
```
Write(file_path="/tmp/pr-body.md", content="...")
gh pr create --title "Title" --body-file /tmp/pr-body.md
```

To:
```
Write(file_path=".tmp/pr-body-YYYY-MM-DD-HHMMSS.md", content="...")
gh pr create --title "Title" --body-file .tmp/pr-body-YYYY-MM-DD-HHMMSS.md
```

### Documentation

Add to `docs/tool-routing-hook.md` or appropriate doc:

```markdown
### Temporary File Directory

The tool routing rules use `.tmp/` for temporary files (commit messages, PR bodies, etc.)
with timestamped filenames to avoid collisions across worktrees and projects.

**Setup:**

Add `.tmp/` to your global gitignore:

1. Create/edit `~/.gitignore_global`:
   ```
   echo ".tmp/" >> ~/.gitignore_global
   ```

2. Configure git to use it (if not already set):
   ```
   git config --global core.excludesfile ~/.gitignore_global
   ```

**Manual Cleanup:**

Temporary files accumulate in `.tmp/`. Clean them up periodically:
```
rm -rf .tmp/
```

These files are useful for debugging failed commits/PRs, so we don't auto-delete them.
```

## Testing

Test both updated routing rules:
- Create fixture for `git commit` with multiline message
- Create fixture for `gh pr create` with multiline body
- Verify correct `.tmp/` file paths are suggested
- Verify timestamps are in correct format

## Future Considerations

### Potential Expansions

If other routing rules need temporary files, they can follow the same pattern:
- `.tmp/{operation}-{YYYY-MM-DD-HHMMSS}.{ext}`

### Reusable Pattern

Could create a helper function in the routing logic that generates consistent temp file paths, but YAGNI for now with only two rules.

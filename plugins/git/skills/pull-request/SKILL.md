---
name: pull-request
description: Invoke this skill BEFORE running any gh pr create, gh pr edit, or gh pr comment command, or any task that will produce or modify a GitHub pull request. This is the skill for authoring outbound PR communication: creating, drafting, opening, filing, or starting a PR; updating a PR body or description; posting a comment or reply to review feedback. Trigger on short and casual phrasings, not only the literal word "create". Example triggers: "create a PR", "draft a PR", "open a PR", "file a PR", "push and PR it", "push up a draft PR", "PR this branch", "PR it", "time to PR this", "let's start a PR", "commit these and push a PR", "update the PR body", "rewrite the PR description", "comment on the PR", "reply to the review comments", "reply to copilot". Do NOT use for reviewing someone else's PR, merging, checking CI/build status, listing review requests, checking out PRs locally, or cleaning up merged branches. Those are separate skills.
---

## Overview

Authoring PR communication that respects busy reviewers. All bodies and comments are drafted to `.scratch/pr-bodies/` for human review before posting. Anti-patterns (metrics, diff-noise, H1 headings) are avoided. Manual edits are detected before overwriting.

## Operations

| Operation | Typical phrasing | gh command at end |
|---|---|---|
| Create | "create/draft/open/file a PR", "push and PR it" | `gh pr create --body-file` |
| Update body | "update the PR body", "rewrite the PR description" | `gh pr edit --body-file` |
| Comment | "comment on the PR", "reply to review feedback" | `gh pr comment --body-file` |

## Routing ambiguous requests

"update the PR" is ambiguous:

- No PR exists: error and offer to create
- PR has no reviews: update body
- PR has reviews: ask whether to update body or add a comment

Prefer **body update** when there are no reviews yet, the user says "update the description", or scope changed. Prefer **comment** when reviews are in, the user is responding to feedback, or they want to notify watchers (comments generate notifications, body updates do not).

## Content principles

### Follow repo conventions first

Check for a PR template (`.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE/*.md`) and `CONTRIBUTING.md` (also `.github/CONTRIBUTING.md`, `docs/CONTRIBUTING.md`). If a template exists, follow it exactly.

### Default body structure (no template)

```markdown
## Summary

- Material impact point 1
- Material impact point 2 (2-4 bullets total)

## Test plan

- How to verify (only if non-obvious)
```

Optional sections based on context: `## Breaking changes`, `## Migration notes`, `## Follow-up work`.

### PR title

Imperative mood (Add, Fix, Update, Refactor), under 72 characters, capitalize first word, no trailing period. Derive from the branch name when semantic, otherwise from the first commit.

### Do

- Focus on material impact and why it matters
- Include non-obvious testing steps
- Stay warm and concise

### Don't

**Metrics** (unless the PR is about them): "Added 15 tests", "Modified 8 files", "Added 250 lines", "Coverage to 85%", "Runtime 2.5s to 1.2s".

**Diff-visible details**: "Created new `Foo` class", "Refactored into smaller functions", "Used async/await", "Added error handling" (unless that is the PR's focus).

**Over-explaining**: "After careful consideration of multiple approaches...", "significantly improves the developer experience by implementing a novel approach...".

**Structural noise**: H1 heading (GitHub shows the title separately), listing technologies unless a new dependency, file structure changes unless architectural, "following best practices" (assumed), "easy to" / "simple to" (condescending).

**The rule:** If a reviewer can see it in the diff or CI output, do not put it in the body unless it is the central focus.

### Comment tone

Three to five sentences, conversational, professional. Acknowledge reviewer input. Explain reasoning when non-obvious. A common opening pattern: "I've updated the PR to address the feedback: ..."

## Workflow: Create PR

1. Check for existing PR: `gh pr view --json number 2>/dev/null`. If one exists, error or route to update.
2. Gather: `git log <base>..HEAD`, PR template, `CONTRIBUTING.md`.
3. Draft body to `.scratch/pr-bodies/drafts/<slug>.md`. Show the draft to the user and allow edits.
4. Create: `gh pr create --title "..." --body-file <draft-path>` (add `--draft` if the user asked for a draft).
5. Archive: move the draft to `.scratch/pr-bodies/<number>/<timestamp>-body.md` and write `metadata.json` with the body hash.

## Workflow: Update body

1. Load: `gh pr view --json number,body,title,state`. Load `metadata.json` if present. Warn if closed or merged.
2. Detect manual edits: hash the current body (`shasum -a 256`) and compare to `last_generated_hash`. If different and the diff is more than whitespace, ask: overwrite, merge, or cancel.
3. Check for material change: re-analyze `<base>..HEAD`. If scope is unchanged from last generation, skip the update and say "description still accurate".
4. Draft to `.scratch/pr-bodies/<number>/<timestamp>-body.md`. Show the diff (current vs proposed) and confirm.
5. Update: `gh pr edit <number> --body-file <file>`. Update `metadata.json` (new hash, timestamp).

## Workflow: Comment

1. Load: `gh pr view --json number,title,reviews,comments`.
2. Determine content. Analyze recent commits. Common scenarios: responding to review feedback, noting significant additions, summarizing a batch of changes.
3. Draft to `.scratch/pr-bodies/<number>/<timestamp>-comment.md`. Show the draft and confirm.
4. Post: `gh pr comment <number> --body-file <file>`.

## Safety checks

Always: current branch is not `main`/`master`; `gh` is installed and authenticated; the user has seen and approved the draft.

Create: branch has commits ahead of base. Update: PR exists and is open. Comment: comment is not empty.

If `gh` is missing, fall back with `brew install gh`. If not authenticated, `gh auth login`.

## Storage layout

```
.scratch/pr-bodies/
  drafts/
    <slug>.md                # Pre-creation drafts
  <pr-number>/
    metadata.json             # See schema below
    <timestamp>-body.md       # Timestamped body versions
    <timestamp>-comment.md    # Timestamped comments
```

`metadata.json`:

```json
{
  "pr_number": 123,
  "branch": "feature/foo",
  "base": "main",
  "title": "Add foo",
  "created_at": "2025-11-07T10:30:00Z",
  "last_generated_hash": "abc123...",
  "last_updated_at": "2025-11-07T16:45:30Z",
  "manual_edits_detected": false
}
```

Timestamps use ISO 8601 with hyphens (`2025-11-07T10-30-00`). Slugs are lowercase with hyphens and special chars stripped.

Keep: `metadata.json`, the last five timestamped files, any in-progress draft. Clean up after PR creation: the draft file. Optional: timestamped files older than 30 days.

## Base branch detection

```bash
base=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null)
if [ -z "$base" ]; then
  git show-ref --verify --quiet refs/heads/main && base=main || base=master
fi
```

## Multiple PRs for one branch

`gh pr list --head <branch> --state open`. If exactly one open, use it. If zero, check `--state all` and offer to create new. If more than one (rare), ask which.

## Common mistakes

- Posting the first draft without user review. Always confirm before running `gh pr create/edit/comment`.
- Overwriting manual edits silently. Always compare hashes and show the diff first.
- Updating body when nothing material changed. Skip with "description still accurate".
- Using raw `gh pr create` without `--body-file`. Shell-escaping issues and no draft review step.
- Running create on `main`/`master`. Stop and ask the user to branch first.
- Ignoring repeated open PRs on the same branch. Always check `gh pr list --head <branch>`.

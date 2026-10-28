---
name: pull-request
description: Invoke this skill BEFORE running any gh pr create, gh pr edit, or gh pr comment command, or any task that will produce or modify a GitHub pull request. This is the skill for authoring outbound PR communication: creating, drafting, opening, filing, or starting a PR; updating a PR body or description; posting a comment or reply to review feedback. Trigger on short and casual phrasings, not only the literal word "create". Example triggers: "create a PR", "draft a PR", "open a PR", "file a PR", "push and PR it", "push up a draft PR", "PR this branch", "PR it", "time to PR this", "let's start a PR", "commit these and push a PR", "update the PR body", "rewrite the PR description", "comment on the PR", "reply to the review comments", "reply to copilot". Do NOT use for reviewing someone else's PR, merging, checking CI/build status, listing review requests, checking out PRs locally, or cleaning up merged branches. Those are separate skills.
---

## Overview

Authoring PR communication that respects busy reviewers. All bodies and comments are drafted to `.scratch/pr-bodies/` first. For creation the draft is the audit record, written then used immediately; for updates and comments it's also a review checkpoint. Manual edits are detected before overwriting.

## Operations

| Operation | Typical phrasing | gh command at end |
|---|---|---|
| Create | "create/draft/open/file a PR", "push and PR it" | `gh pr create --body-file` |
| Update body | "update the PR body", "rewrite the PR description" | `gh pr edit --body-file` |
| Comment | "comment on the PR", "reply to review feedback" | `gh pr comment --body-file` |

Always pass `--body-file`, never an inline `--body` (shell escaping, and no draft on disk).

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

<attribution footer, if your environment requires one>
```

Optional sections based on context: `## Breaking changes`, `## Migration notes`, `## Follow-up work`.

If your instructions require an attribution footer on PR bodies (for example a "Generated with ..." line), append it as the last line of the body. It isn't a section; don't give it a heading.

### Voice and style

If a voice or writing-style skill is available for prose written under the user's name, load it and follow it for the body and comments. No em-dashes in titles, bodies, or comments: outbound em-dash checks reject them at send time, so fix the draft before running `gh`.

### What goes in the body

Lead with material impact and why it matters. **If a reviewer can see it in the diff or CI output, leave it out unless it is the central focus**: metrics (test counts, files changed, coverage), implementation narration ("created a new `Foo` class", "added error handling"), technology lists, and "following best practices". No H1 (GitHub shows the title).

## Workflow: Create PR

1. Check for existing PR: `gh pr list --head <branch> --state open`. If one exists, route to update; if more than one (rare), ask which.
2. Gather: `git log <base>..HEAD`, PR template, `CONTRIBUTING.md`.
3. Draft body to `.scratch/pr-bodies/drafts/<slug>.md`.
4. Create: `gh pr create --title "..." --body-file <draft-path>` (add `--draft` if the user asked for a draft). No approval pause on the routine case: being asked to create a PR is itself the go-ahead; the draft file is the record, not a checkpoint. Don't add a confirmation pause back in "to be safe": skipping that round-trip is the point. Do stop and confirm first if something's off the routine path: no commits ahead of base, an open PR already exists for this branch, or the title/scope is genuinely ambiguous.
5. Archive: move the draft to `.scratch/pr-bodies/<number>/<timestamp>-body.md` and write `metadata.json` with the body hash.

## Workflow: Update body

1. Load: `gh pr view --json number,body,title,state`. Load `metadata.json` if present. Warn if closed or merged.
2. Detect manual edits: hash the current body (`shasum -a 256`) and compare to `last_generated_hash`. If different and the diff is more than whitespace, ask: overwrite, merge, or cancel. Never overwrite manual edits silently.
3. Check for material change: re-analyze `<base>..HEAD`. If scope is unchanged from last generation, skip the update and say "description still accurate".
4. Draft to `.scratch/pr-bodies/<number>/<timestamp>-body.md`. Show the diff (current vs proposed) and confirm.
5. Update: `gh pr edit <number> --body-file <file>`. Update `metadata.json` (new hash, timestamp).

## Workflow: Comment

1. Load: `gh pr view --json number,title,reviews,comments`.
2. Determine content from recent commits: responding to review feedback, noting significant additions, or summarizing a batch of changes.
3. Draft to `.scratch/pr-bodies/<number>/<timestamp>-comment.md`. Show the draft and confirm.
4. Post: `gh pr comment <number> --body-file <file>`.

Unlike create, update and comment always get the user's review first: they can overwrite manual edits or ping reviewers.

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

File timestamps use ISO 8601 with hyphens (`2025-11-07T10-30-00`). Keep `metadata.json`, the last five timestamped files, and any in-progress draft; delete the draft after creation.

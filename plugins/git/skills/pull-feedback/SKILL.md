---
name: pull-feedback
description: Use when the user has authored a GitHub pull request and wants to work through review feedback on it. Triggers on phrases like "pull down the review on #N", "address the feedback", "what did @reviewer say on my PR", "let's work through the comments", or any request to triage, respond to, or systematically handle review threads on the user's own PR. Do NOT use for reviewing someone else's PR, authoring PR content or replies, or checking which PRs are waiting on the user for review.
---

# Git Pull Feedback

## Overview

Pulls review feedback on a PR the user authored into a working doc with per-thread triage slots. The point is rigor: every unresolved thread gets a tentative verdict (valid / invalid / nice-to-have / needs-clarification) with reasoning and a plan, so the user can work through feedback deliberately instead of rubber-stamping.

**Announce:** "Using git:pull-feedback to pull and triage feedback on PR #N."

## Workflow

### 1. Fetch

```bash
./fetch.sh [ref]
```

`ref` accepts a bare number, `#N`, `owner/repo#N`, a PR URL, or nothing (auto-detects from current branch). The script writes a skeleton doc to `.scratch/pr-reviews/<N>/threads.md` with `_pending triage_` placeholders and prints counts on stdout. Use this output location — don't invent your own filename.

### 2. Orient only if context is cold

Add a `## Summary` section (1-2 sentences on what the PR does + state of the review) **only if** you don't already know the PR. If the user has been discussing it in conversation or the branch name tells you, skip — guessing wastes tokens and risks confabulation.

### 3. Triage each unresolved thread (shallow pass)

Each thread has a unique `<!-- thread: N -->` anchor. Use targeted `Edit` calls to fill three slots per thread:

- **Verdict (tentative):** pick one, based on whether the reviewer is *right*:
  - ✅ **Valid** — reviewer has a point, code needs to change
  - ❌ **Invalid** — disagree for a concrete technical reason (not because the fix is inconvenient)
  - 💡 **Nice-to-have** — reasonable suggestion, but out of scope for this PR
  - ❓ **Needs clarification** — comment is ambiguous; ask the reviewer instead of guessing
- **Reasoning:** 1-3 sentences. Reference the comment body or the code, not vibes. Severity ≠ verdict — a "should-fix" can still be Invalid if the reviewer is wrong.
- **Plan:** concrete next step — fix inline, deep-dive first, reply-and-defer, ask reviewer.

Keep the `(tentative)` label. It's the shallow-pass signal; it invites deep-dive on anything non-obvious.

### 4. Deep-dive on request

When the user asks to dig into a specific thread ("verify the race condition claim", "dig into thread 3"):

1. Read the referenced file at current HEAD
2. Check surrounding code for context the reviewer may not have seen
3. Re-evaluate, then upgrade `**Verdict (tentative):**` → `**Verdict:**`

Shallow pass catches obvious cases (typos, renames, style). Deep-dive is where the hard judgment lives — reserve it for threads with real technical substance.

### 5. Apply rigor to Invalid verdicts

For any Invalid, apply **superpowers:receiving-code-review**: verify the reviewer's claim is actually wrong (don't just disagree because fixing is annoying), acknowledge the concern even when disagreeing, and plan a reply that explains the reasoning. That skill was written for agent reviews; the core rigor applies equally to humans.

### 6. Report back

Summarize counts and offer a next step:

> 7 threads triaged: 4 valid, 2 invalid, 1 nit. Doc at `.scratch/pr-reviews/603/threads.md`. Walk through them, or dig deeper on specific ones?

Then stop. Addressing threads, making code changes, and replying are normal work from there — not this skill's job.

## Stay in Scope

This skill is about **review threads**, not PR health. Do NOT drift into:

- Merge conflicts, CI status, approval gates, mergeable state
- Whether the PR needs a rebase
- Whether another reviewer should be added

If the user asks "catch me up on my PR", they mean the review feedback. Other PR state belongs to other tools (`gh pr view`, `gh pr checks`, `git:pull-request`).

**Reviewer scoping:** If the user asks specifically about one reviewer ("what did alice say?"), scope the doc to that reviewer's threads. Other reviewers' threads can be omitted or deferred — don't force all-threads mode.

## When Not to Use

- PRs awaiting the user's review → `git:inbox`
- Writing PR body, description, or replies → `git:pull-request`
- Reviewing someone else's PR → `pr-review-toolkit:review-pr` or `code-review:code-review`
- Marking threads resolved, posting replies, or pushing commits — outside this skill's scope

## Quick Reference

| Action | Command |
|--------|---------|
| Fetch for current branch's PR | `./fetch.sh` |
| Fetch for specific PR | `./fetch.sh 123` or `./fetch.sh owner/repo#123` |
| Deep-dive on thread N | Read the file, update verdict + reasoning via Edit |
| Run internal tests | `./tests/run-tests.sh` |

## Common Mistakes

- **Severity in place of verdict.** "Should-fix" is urgency, not validity. A Should-fix comment can still be Invalid if the reviewer is wrong about the code. Keep the two axes separate.
- **Filling `## Summary` without real context.** If you don't actually know what the PR does, either read enough to find out or leave the section off. Don't confabulate.
- **Scope drift to PR health.** Merge conflicts and CI aren't review feedback. Stay on threads.
- **Confirming verdicts without deep-diving.** The `(tentative)` marker isn't decoration — keep it until you've read the code for that thread.
- **Addressing threads in the same turn as triaging.** The skill ends at the filled doc. Code changes are a separate step; forcing both into one pass rushes both.

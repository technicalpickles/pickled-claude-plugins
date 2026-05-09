# Baseline observations (RED phase)

Three subagents ran the eval prompts against `Gusto/gdev-wish#603` without access to the `pull-feedback` skill or `fetch.sh`. They had default tools: `gh`, Read/Write/Edit, Bash.

## What the baselines produced

| Eval | Tool calls | Output | Scope |
|------|------------|--------|-------|
| explicit-pr-ref | 9 (gh + writes) | `review-feedback.md` — 7 items from 3 reviewers, priority buckets | All threads, all reviewers |
| ambient-pr-context | 8 | `rubberduck203-feedback.md` — 2 items scoped to one reviewer | Correct — single reviewer |
| cold-reorient | 21 | `catch-up.md` — broad PR state (merge conflict, CI, approval gate) + threads | Scope drift into PR health |

All three fetched and read the PR cleanly. `gh api` + `gh pr view` was the default path; no one reinvented the wheel, but each invented their own output structure.

## Gaps the skill must close

1. **No verdict column.** None of the baselines assigned a `valid / invalid / nice-to-have / needs-clarification` verdict per thread. They used *severity* ("Should-fix", "Minor", "Info") — a different axis. Severity is about urgency; verdict is about whether the reviewer is *right*. The skill needs to force the right question: "is this a real problem, or should we push back?"

2. **No per-thread plan.** Baselines listed "what the reviewer said" + vague "what to address". None of them articulated concrete next steps: fix inline, deep-dive first, reply-and-defer, ask reviewer. The plan field turns a list-of-issues into an actionable queue.

3. **No tentative-vs-confirmed distinction.** All baselines committed to confident verdicts (as severity) without signaling "I haven't read the code yet." The shallow-pass / deep-dive split is missing — nothing signals which judgments are cheap takes vs. grounded in code.

4. **Scope drift on cold-reorient.** The cold-reorient baseline went 2x the tool-call budget (21 vs 8-9) exploring CI status, mergeable state, review decision gates — things that are *about* the PR but aren't review feedback. The skill needs to hold the line: "catch me up" means catch me up on review feedback, not PR health.

5. **No standard output location.** Each baseline picked its own filename (`review-feedback.md`, `rubberduck203-feedback.md`, `catch-up.md`). The skill needs `.scratch/pr-reviews/<N>/threads.md` as the canonical location — makes it discoverable, consistent across sessions, and cheap to find when resuming.

6. **Issue-level vs inline comments conflated.** Baselines mixed general PR comments (Fresh Eyes's description-mismatch note) with inline review threads. The skill's artifact separates these into "Threads" and "General comments" sections.

7. **Ambient-context baseline succeeded on scope discipline.** The 2nd baseline correctly scoped to rubberduck203 alone, which is a good signal. The skill shouldn't force all-threads mode when the user asked about one reviewer.

## What the baselines got right (don't break)

- Clean `gh api` usage, no GraphQL fumbling
- Comment bodies quoted accurately with context (file:line, author)
- Markdown rendering was human-readable

## Implications for SKILL.md

The skill needs to teach:
- **Verdict rubric** explicit and required per thread
- **Plan** required per thread
- **Tentative** marker on shallow pass; **deep-dive** as a distinct follow-up step
- **Scope discipline** — stay on review threads, don't bleed into PR health; respect reviewer scoping in the ask
- **Standard output location** via `fetch.sh`
- **Threads vs general comments** separated

The baseline data confirms the artifact design from the spec already addresses #1-#3, #5, #6. The skill needs to *direct Claude to fill it out that way* and *not scope-drift*. The hardest behavior to enforce is #4 (cold-reorient scope discipline).

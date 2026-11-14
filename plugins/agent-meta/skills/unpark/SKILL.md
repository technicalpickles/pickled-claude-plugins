---
name: unpark
description: Use when resuming work from a parked handoff, or reading a wrapped close-out record as reference
---

# Unpark

Validate the handoff, report in a few lines, then keep going. Ask only when something new needs a human: drift that changes the plan, context the user added, or a question the handoff left open.

## 1. Find the handoff

Look in every location that applies, together: the vault (when the injected context has a `Park vault:` line and `<vault>/CLAUDE.md` has a `## Parking` section with a `Location:`, that folder relative to the vault) and `.parkinglot/` in the project root.

- **A path:** use it.
- **A name or topic:** match filenames and first headings. One match, use it. Several close matches, list them and ask which.
- **Nothing given:** the newest `Parked:` or `Checkpoint:` file whose Branch or Worktree is in the current repo, else the newest overall. Name it in the report.
- **The user asked to see what exists:** list both locations grouped as active (`Parked:`, `Checkpoint:`) and wrapped, each labeled `[vault]` or `[.parkinglot]`, then run the sweep below and stop.

The first heading decides the mode, not the filename. If they disagree, trust the heading.

### Sweep (listing only)

Flag an active handoff as stale when either holds:

- its Branch is merged into the default branch (`git -C <repo> branch --merged <default>`; the default is `origin/HEAD`, else `main`, else `master`). The repo is the handoff's Worktree, else the current one.
- it names task UUIDs and every one is done (`task <uuid> status`).

A handoff with no such evidence, a branch that does not exist, or a repo you cannot reach is not flagged. Age alone never flags. `Wrapped:` files are never flagged.

Mark each flagged line `stale: <reason>` in the listing. If any are flagged, ask once with `AskUserQuestion` (multi-select, one option per flagged file by name, plus "Keep all"; as plain text with a stop if the tool is missing). Delete exactly the files the answer selects, each by its absolute path, no globs. No answer means no delete. Say what was deleted, with paths. The vault is not a git repo, so only sync history can bring a file back. Nothing flagged: no question.

## 2. Go where the work is

Work from the handoff's Worktree, else the repo its Branch belongs to. Put the `cd` or `git -C` in every command, including commands you hand the user. A missing worktree is drift.

## 3. Validate the claims

Check what the `Parked:` or `Checkpoint:` handoff asserts against reality:

- the branch and worktree exist, and what landed on the branch since the `Parked:` time
- the key files exist
- the PRs, tasks and commits named in Current State and Next Steps are in the state it says (`gh`, `task`, `git`)

**In the same step as the first check, look up the devlog, even when the checks already show drift.**

1. Take the handoff's `Session:` id and keep the first 8 characters.
2. `grep -rlF --include='*.md' "claude-code session <id8>" <Park vault>`. Notes move into topic folders, so search by that string, not by path. No `Park vault:` line or no hit means move on.
3. Read the note, about 6 KB at most (the latest entries if longer). Keep what the handoff lacks: traps, gotchas, decisions the user made, corrections. Entries timestamped after the `Parked:` time are newer than the handoff, so check them for drift. The date is in the note's filename prefix.

## 4. Report, then act

The report is at most five lines, each one sentence:

1. `✅ Handoff holds.` plus what you checked (head commit, clean tree, pending tasks), or `⚠️ Drift.` plus the one fact that changes the plan.
2. `📓` plus one devlog trap, decision or correction the handoff lacks. Omit the line when there is none.
3. `▶️ Picking up with <first next step>`, then do it. On drift, one question with a recommended default instead: `AskUserQuestion` when available, two options, recommended first.

```
✅ Handoff holds. main @837b3bc, clean, tasks a1b2c3d4 and e5f6a7b8 still pending.
📓 The sync failure was a renamed container, not a timeout. The timeout was already fixed.
▶️ Picking up with the dashboard check.
```

```
⚠️ Drift. Steps 1 to 4 landed in #41 and later PRs, and the worktree is gone.
📓 The uncommitted fix shipped inside #44, so nothing was lost.
Start at step 5, or retire this handoff?
```

```
⚠️ Drift. Every step landed in #41 through #47, and 5 follow-ups remain, the main one c9d0e1f2 (the lint check skips in worktrees).
Pick up c9d0e1f2, or retire this handoff?
```

Nothing else goes in the report. No bullet lists, no list of what landed or what is still open (give a count and the one that matters), and no remark about a missing devlog. The user can ask for detail.

Drift is a next step that already landed, a missing branch or worktree, a decision that no longer holds, or a newer devlog entry that contradicts the handoff. A moved `main` or an unrelated commit goes in the `✅` line. An old handoff's age goes there too.

## 5. Extra context is where to ask

Ask one question with a default when:

- **The user added context** that conflicts with or extends the handoff's next step. Say how you would merge it. Consistent, additive context needs no question.
- **An open question in the handoff blocks the first next step.** Others wait until the work reaches them.
- **The next step is irreversible or outward** (deploy, publish, delete, message someone). The usual rules apply. Unpark adds no gate of its own.

## 6. Wrapped files

A `Wrapped:` file is a record, not a handoff. Skip validation. Show the Outcome's first paragraph and the Open Threads as one-liners, and ask what to do with them. If the user already said, do that. New work building on the record goes through `superpowers:brainstorming` with the file as context. If they say it was wrapped too early, run steps 2 to 4.

## Leave the handoff alone

Don't edit, rename or delete the handoff while resuming. The listing sweep is the only place unpark deletes, and only files the user selected.

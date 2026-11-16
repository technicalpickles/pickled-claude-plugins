# Tie-off

Close-out runs every step below before it writes the record. Continuation runs only **Loose ends**, read-only, and puts what it finds in Next Steps or Open Questions. Idle checkpoint skips the tie-off.

## Extensions

Read these before step 1:

- A `## Close-out` section in the user's global instructions, then in the repository's `CLAUDE.md` or `AGENTS.md`. Each line names a step below and what it adds there, as in `Tracker: pt beans, never raw beans` or `Cleanup: cenv sandboxes, coder workspaces`. Apply repository lines after user lines. A line that names no step belongs to Loose ends.
- Lines a hook appended to this prompt, such as `Git state:`. They are inputs to the step they bear on, not a replacement for checking it.

## Steps

1. **Trigger.** Confirm, live, what says the work is done: the PR merged (`gh pr view`), CI green, the rollout finished. A handoff or the conversation saying so is not the check. If the work is not done, this is a continuation: re-pick the mode now, before writing.
2. **Durable.** Commit and push what this session changed, following the repository's commit rules. In a working tree other sessions share, scope the commit to the paths this session touched. Changes this session did not make stay put, named in Loose ends.
3. **Loose ends.** Go back through the session for threads set aside, follow-ups promised, deferrals, things noticed but not done, and questions left open. Decide each one: do it now when it is small and reversible, file it (Tracker), or drop it with a reason. What you cannot decide goes to Ask once.
4. **Tracker.** Use the tracker the extensions or the repository's instructions name, else the one this session used. Close items whose work landed. Update in-progress items with absolute state: a date, a SHA, a PR number. File what Loose ends chose to file. A deferral counts only once its item exists. With no tracker, filed items become the record's Open Threads.
5. **Docs.** Correct, in place, the docs this session's work made wrong: status lines, READMEs, plans, claims that turned out false.
6. **Cleanup.** For each thing this session created that the finished work no longer needs (worktrees, branches, containers, dev environments, remote workspaces, temp dirs, background processes), find out what it is, whether it is merged or rebuildable, and whether anything else still uses it. Remove it when it is clean, merged, and unused. Hold it for Ask once when it has uncommitted work, unmerged commits, another session using it, or you did not create it.
7. **Lessons.** Record gotchas, workarounds, and corrections the user gave, wherever this setup keeps them: a devlog, memory, a rule, or the skill that was wrong. A correction goes where the next session will load it.
8. **Ask once.** One `AskUserQuestion`, multi-select, listing every held item: removals, undecided loose ends, and any message to another person the work calls for, as a draft. Do only what the answer selects. Skip the question when nothing is held.

The tie-off never messages anyone on its own. A message it would send goes to Ask once as a draft.

## Into the record

Items the tie-off filed are linked from Open Threads, not restated. Items it closed or removed go in Outcome only when the commits do not show them. When the tie-off emptied Open Threads and Key Decisions holds nothing new, the record does not earn a file (see SKILL.md).

Open the closing message with one line tallying the tie-off: closed, filed, removed, held. Omit any count that is zero.

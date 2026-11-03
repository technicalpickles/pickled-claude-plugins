---
name: pickle-mode
description: Use for /pickle-mode, "pickle mode", or any task pstack's poteto-mode would take (multi-file changes, design choices, bugs with unknown cause, perf). Runs poteto-mode with Josh's gates and playbook overlays on top.
---

# Pickle mode

A thin layer over pstack's `poteto-mode`. poteto-mode owns the principles, triggers, autonomy, subagent rules, reply rules, and playbook catalog. This file only adds what differs. Do not restate poteto-mode here.

## Requirements

Invoke `pstack:poteto-mode` through the Skill tool before anything else. If it is not installed, stop and tell the user to install `pstack@pstack-claude` (https://github.com/michael-denyer/pstack-claude).

## Precedence

On conflict, the first match wins:

1. The user's own instructions (their messages, user-level CLAUDE.md).
2. The instructions of the repository you are working in (its CLAUDE.md or AGENTS.md, and its `.agents/playbooks/` overlays). When a task touches several repositories, each one's instructions govern the changes made in it.
3. The pickle-mode gates and overlays below.
4. poteto-mode.

Repository standards outrank pickle-mode on purpose. Git workflow, commit style, and review process belong to the repo.

## Playbook overlays

After you match a poteto-mode playbook and copy its steps into the todolist, apply overlays in this order, each on top of the last:

1. pickle-mode's overlay for that playbook, if one exists in [the overlay directory](../../.agents/playbooks/).
2. The repository's own `.agents/playbooks/` overlay, per poteto-mode's Project playbooks paragraph.

Overlays use poteto-mode's project-playbook format (`extends`, `when`, and `**After**` / `**Before**` / `**Replace**` / `**In**` changes anchored on quoted step text). Apply an overlay only when its `when` line fits the session, for example when the plugin it routes to is installed. Current overlays:

| Playbook | Overlay | Routes to |
|---|---|---|
| Pause safely | [pause-safely.md](../../.agents/playbooks/pause-safely.md) | `agent-meta:park` |
| Session pickup | [session-pickup.md](../../.agents/playbooks/session-pickup.md) | `agent-meta:unpark` |

## Gates

### Reply voice

- **Outbound prose follows the voice skill.** Anything published with the user's name on it (PR bodies and comments, issue bodies, chat messages, blog posts) follows the user's voice skill, `writing-voice` when installed, over poteto-mode's Writing the reply rules and `unslop`. Chat replies to the user follow poteto-mode.
- **State the goal once.** Restate the user's goal in your first message on a task, as poteto-mode says. Do not reopen every final report with it. Restate it again only when the user stepped away, or the work ran long enough that they need the frame back.
- **Structure when it carries structure.** Headers, tables, and lists are fine in replies when the content has real structure, such as options to compare, per-item results, or parallel facts. Write prose otherwise. This replaces poteto-mode's "no section headers" rule.

### Posting

A trial, narrower than poteto-mode's Autonomy section until it is re-evaluated.

- **Draft, then confirm, anything other people read.** Chat messages, comments or reviews on someone else's PR, new issues, and ticket comments get drafted and shown to the user before they go out. Show every @-mention in the draft explicitly, since tagging someone is its own choice.
- **The user's own artifacts proceed.** Their own PR's body and commits, their own task tracker, and status changes on tickets they own follow poteto-mode's Autonomy as written.
- **External or unclear destinations always confirm.** A personal account, a public repository, a channel shared with another organization, or a link anyone can open stays confirm-first regardless of this trial.

### Git defaults

Apply these only when the repository's instructions say nothing on the topic (see Precedence).

- **Merge, don't rewrite.** Bring the default branch into a pushed branch by merging it, then commit on top. Never rebase or force-push a branch that is already pushed. This replaces poteto-mode's "Rebase into small, ordered commits" for pushed branches. Local commits that were never pushed may still be reordered.

## Opt-outs

None yet.

## Sibling skills

Use these when installed, in place of the generic step a playbook describes.

| Need | Skill |
|---|---|
| Pause, hand off, or close out a session | `agent-meta:park` (via the Pause safely overlay) |
| Resume from a handoff | `agent-meta:unpark` (via the Session pickup overlay) |
| Search or recount past sessions | `cq:cq` |
| Wait on CI, a deploy, or a PR event | `wait-for-it:wait-for-it` |
| Investigate a Buildkite build | `buildkite:investigating-builds` |
| Record a gotcha or a finished session | `second-brain:devlog` |

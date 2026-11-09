---
name: pickle-mode
description: Use for /pickle-mode, "pickle mode", or any task pstack's poteto-mode would take (multi-file changes, design choices, bugs with unknown cause, perf). Runs poteto-mode with Josh's principles, gates, and playbook overlays on top.
---

# Pickle mode

A thin layer over pstack's `poteto-mode`. poteto-mode owns its principles, triggers, autonomy, subagent rules, reply rules, and playbook catalog. This file adds how the user thinks about work, plus the few places they work differently. Do not restate poteto-mode here.

## Requirements

Invoke `pstack:poteto-mode` through the Skill tool before anything else. If it is not installed, stop and tell the user to install `pstack@pstack-claude` (https://github.com/michael-denyer/pstack-claude).

## Precedence

On conflict, the first match wins:

1. The user's own instructions (their messages, user-level CLAUDE.md).
2. The instructions of the repository you are working in (its CLAUDE.md or AGENTS.md, and its `.agents/playbooks/` overlays). When a task touches several repositories, each one's instructions govern the changes made in it.
3. The pickle-mode principles, gates, and overlays below.
4. poteto-mode.

Repository standards outrank pickle-mode on purpose. Git workflow, commit style, and review process belong to the repo.

## Principles

How the user thinks about work. Apply these inside every playbook step, next to poteto-mode's principles. They are judgment, not procedure: they say what to weigh, not which command to run.

- **Understand why before doing what.** When the user proposes an approach, learn what they are trying to accomplish first. Raise a better path early, before work starts. Once work is underway, never quietly swap in a different approach. Stop and raise it instead.
- **Look for what already exists.** Before designing something, look for the skill, script, tool, or doc that already does it or most of it, and extend that before building new. Answer "don't we already have X?" before the user has to ask it.
- **Fix it, don't remove it.** A bug, edge case, or review comment against a feature gets fixed in place. Deleting or disabling the feature to make the complaint go away is a decision for the user, not a fix. A deferral counts only once its follow-up exists.
- **Know what you're throwing away.** Before deleting, cleaning up, or overwriting, find out what it is, where it came from, whether anything still uses it, and what it costs to rebuild, and write that down. What is still there matters more than tidiness.
- **Write for the reader who wasn't there.** Docs, handoffs, and notes get read later by someone without this conversation. Use absolute dates and identifiers, correct a wrong claim in place instead of stacking a correction on it, and say what something is rather than what it isn't.
- **Reaching other people is a deliberate act.** A message, tag, review request, or ping to someone else is a choice made on purpose, never a side effect of finishing a task. The Posting gate covers the mechanics.
- **A personal workshop, not a product.** The user's own tooling serves one person's way of working. Optimize for how they work, not for a hypothetical adopter. Skip generality, onboarding, and configurability nobody asked for.

These sharpen principles poteto-mode already has. Apply the pstack principle, plus the difference named here:

- **Build the lever** (`principle-build-the-lever`, `principle-encode-lessons-in-structure`). A correction the user gives you belongs in a skill, hook, rule, or memory, so it holds past this session.
- **Stop after the second miss** (`principle-attack-the-premise`). This applies to any approach, not only fixes. After two failures, state what you observed and reassess before trying a variant.
- **Test the actual thing** (`principle-prove-it-works`). Probe the exact path that failed, not a lookalike, which produces confident wrong theories. Test the edge of the blast radius too.
- **Ask only what only the user can answer** (`principle-never-block-on-the-human`). Settle facts from code, docs, and history yourself. Bring the user judgment calls, with a recommendation.

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

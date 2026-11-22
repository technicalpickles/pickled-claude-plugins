# Unpark FYI without waking the origin session

**Date:** 2026-11-22
**Status:** Implemented, verified live
**Builds on:** #209 (unpark tells the origin session), #210 (leave next steps out of the FYI)

## Goal

When `agent-meta:unpark` resumes a `Parked:` or `Checkpoint:` handoff, the session the handoff came from should learn it was handed off without running a model turn.

## Problem

Since #209, the `agent-meta` mod's `skill.prompt` hook sends the origin session an FYI through `$.session.send`. The receiver treats it as a peer message, which starts a turn. Every real origin did the right thing (no tool calls, a one-line "noted"), but the turn re-reads the whole context to say so.

Measured from transcripts, 2026-11-16 to 2026-11-21, the turn that answered the FYI:

| session | model | cache read | cache write | output |
|---|---|---|---|---|
| 7ccec688 | sonnet | 72K | 149K | 37 |
| b50c3eeb | sonnet | 83K | 194K | 28 |
| d9ca82c3 | opus | 84K | 147K | 28 |
| 14203b7e | sonnet | 294K | 0.4K | 59 |
| 856c497c | sonnet | 254K | 0.4K | 111 |
| ae7ad678 | sonnet | 670K | 0.4K | 111 |

A parked session usually sits idle past the prompt-cache window, so the common case is a ~150-190K token cache write to say "noted".

## Design

The sender stays as it is. Every live session loads `agent-meta`, so the receiving session's copy of the mod handles the FYI.

### Wire format

The FYI text does not change. `buildMessage(path)` already writes a fixed first sentence and a `Handoff: <path>` line. A new pure function, `parseMessage(text) → { path } | undefined`, reads it back, and a round-trip test pins the pair together.

Keeping the text means an origin still running an older `agent-meta` reads the same prose and behaves as it does today.

`parseMessage` looks for the marker sentence and the `Handoff:` line anywhere in the text, not anchored at the start, in case the delivery arrives wrapped in a cross-session envelope.

### Receiving hook

A `session.receive` hook in `hooks/register.ts`:

1. Passes through (`next(e)`) anything addressed to a subagent (`e.agentId` set), anything not from a peer, and anything `parseMessage` rejects.
2. For an FYI, appends two rows with `$.session.append`, the model's first:
   - a `user` row for the model. On an idle session it waits for the next real turn. Mid-turn it joins the next request of that turn. Its text opens with `Note from the agent-meta plugin, not from the user:`, because CLI 2.1.322 sends the row bare inside the person's turn, with no label naming the plugin.
   - a `system` row, a notice the model never reads: `Handed off: <path> is being picked up in another session.`
3. Returns `{ consumed }`, so the FYI is never queued and never starts a turn.
4. If the model note is refused, returns `next(e)`, and the origin gets today's wake, so the FYI is never lost. A refused append resolves `{ deny }` rather than throwing, so the hook checks the result as well as catching. A refused notice alone does not fall back: the note already did the job.

| Origin state | Before | After |
|---|---|---|
| idle, person never returns | wakes, ~150K cache write | notice row, no tokens |
| idle, person returns and types | model already knew | model reads the queued note with that prompt |
| mid-turn | FYI joins the running turn | note joins the next request, no extra turn |
| older `agent-meta` | wakes | wakes (unchanged) |
| an append fails | n/a | falls back to the wake |

### Decisions

- **Two rows.** The notice is for the person. The model note keeps the origin from resuming work that moved on when the person comes back and says "keep going".
- **No toast or native notification.** Nobody is looking at the origin when the FYI lands, so a ping is noise.
- **The parse is the gate, not `origin.plugin`.** The engine documents the sending plugin's name as an unverified claim. A forged message that parses only gets demoted from a turn to a notice, so it gains nothing.

### Rejected: a `$.store` marker

The sender could write "handoff resumed" to the cross-session `$.store`, and a `prompt.submit` hook in the origin could check it. That also costs no tokens, but the person sees nothing in the origin until they type there, and it adds a second channel when send-and-consume reuses the one that works.

## Verification

- Unit tests (`tests/unpark-notify.test.ts`): build/parse round-trip; an FYI is consumed and appends a `system` and a `user` row; a non-FYI peer message and a subagent delivery pass through; a failed append falls back to `next`.
- Live check, run 2026-11-22 on CLI 2.1.322 with Haiku: origin held in tmux (`claude --plugin-dir`), resumer a headless `claude -p "/agent-meta:unpark <file>"`. The origin transcript gained the `user` note and the `informational` notice, and no `api-request` followed either FYI until a real prompt. On the next prompt the model read the note. Without the plugin label it took the note for the person's own words. With the label it treated the work as handed off.
- Not checked: whether the desktop app draws the notice. The terminal did not draw it on screen, though the row is in the transcript.

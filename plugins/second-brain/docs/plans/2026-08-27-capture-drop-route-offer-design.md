# Capture: Drop the Per-Note Routing Offer

Bean: gt-6zaa
Date: 2026-08-27

## Goal

`second-brain:capture` Step 4 currently ends every single-note capture with a
question — "Want me to route it to X?" — before leaving the note in the inbox.
Remove that question. Routing is `process-inbox`'s job: it already auto-routes
above a confidence threshold and only pauses on low-confidence notes. The
per-note offer is a duplicated decision point on top of a batch path that
already exists.

## Background

- A 2026-08-20 session (bean `1fxi` / PR #111) diagnosed capture as doing
  three round-trips per note: route offer, connect offer, breadcrumb offer.
  That work automated the breadcrumb (no longer a yes/no) but deliberately
  left the route and connect offers unfiled — "a design call, not a bug fix."
- Session history (checked via `cq` across ~1300 indexed transcripts,
  2026-08-27) confirms capture asks to route on essentially every single-note
  capture sampled from 2026-07-28 through 2026-08-20, while `process-inbox`
  already auto-routes silently above threshold and only surfaces low-confidence
  notes for a decision.
- The newer, unmerged `devlog` skill (successor to `distill-conversation`,
  currently only in the `bare.git.devlog-skill` worktree) already embodies the
  target philosophy: never ask at write time, defer all processing decisions
  to the batch pipeline.

## Decision

Capture stops asking about routing entirely. It doesn't route, and it doesn't
mention that the note still needs routing — that status is `process-inbox`'s
to surface, not capture's. The final report only covers what was captured and
linked, the same way `devlog`'s report only covers what was logged.

The one exception: if the user names a destination in the same conversation
("put it in 66"), capture resolves it the way `route` would — via
`sb vault structure`, matching against a real destination (JD `area`/`code` or
PARA folder) — and moves the note there with `sb note move`. It never
constructs a destination path from the user's words alone. This isn't an
"offer"; it's honoring an explicit instruction, and it stays subject to the
same "sb owns paths, no hand-rolling" rule the rest of the skill already
follows.

Out of scope: the Step 5 *connect* offer is untouched. Josh's 2026-08-27
statement was specific to routing; no decision has been made on connect.

## Changes

### `skills/capture/SKILL.md`, Step 4

Replace the current step:

```
## Step 4: Leave it in the inbox - routing is opt-in

The note stays where sb put it. **Offer** to route it; do not route it.

This overrides the vault's general "capture: file rough, move on / a wrong-but-close
home beats the global inbox" guidance, which governs notes *the user* files by hand.
Notes *the agent* writes on request stay in the inbox until the user says otherwise.
Both rules coexist in the vault CLAUDE.md and the scope of the override has
historically been read as ambiguous, which produced a roughly 50/50 split between
inbox and direct-to-area filing. It is not ambiguous: **agent-written note on
request → inbox, stop.**

The exception is an explicit destination from the user ("put it in 66"). Then write it there.
```

with:

```
## Step 4: Leave it in the inbox for `process-inbox` to route

The note stays where sb put it. Routing is `process-inbox`'s job, not capture's —
don't ask, don't route it, and don't mention that it still needs routing.

This overrides the vault's general "capture: file rough, move on / a wrong-but-close
home beats the global inbox" guidance, which governs notes *the user* files by hand.
Notes *the agent* writes on request stay in the inbox until `process-inbox` picks them
up. Both rules coexist in the vault CLAUDE.md; the scope of the override has
historically been read as ambiguous — first producing a roughly 50/50 split between
inbox and direct-to-area filing, later a per-note routing question duplicating
process-inbox's own batch routing. It is not ambiguous: **agent-written note on
request → inbox, no offer, no mention.**

The exception is an explicit destination named in the same conversation ("put it in
66"). Resolve it the way `route` would rather than hand-rolling a path: run
`sb vault structure`, match the user's phrase against a real destination (JD `area`/
`code` or PARA folder), then `sb note move --from "{note-path}" --to "{destination}/"`.
Never construct the destination path from the user's words alone.
```

### `skills/capture/SKILL.md`, Constraints section

Replace:

> - **Inbox by default.** Routing is offered, not performed.

with:

> - **Inbox by default.** Routing is `process-inbox`'s job — capture never asks or
>   routes, except an explicit user-named destination, resolved via `sb vault
>   structure` like `route` does, never hand-rolled.

## Not changing

- `description:` frontmatter — unchanged, so no eval re-run needed (evals only
  test trigger-phrase discrimination, not this wording; confirmed by grepping
  `evals/trigger-evals.json`, which has no assertions tied to Step 4).
- Step 5 (connect offer, daily breadcrumb) — untouched.
- `references/note-format.md` — already consistent with the new design ("a
  capture that hasn't been routed isn't `filed` yet," pipeline states owned by
  pipeline skills). No edit needed.
- The vault's own `CLAUDE.md` (`~/Vaults/pickled-knowledge/CLAUDE.md`) — its
  override language ("routing is a separate, opt-in step") remains accurate;
  routing is still opt-in, just opt-in via running `process-inbox`, not via a
  per-note question. Not part of this repo, not part of this PR.

## Verification

Textual change to a SKILL.md — no automated test surface. Verify by reading
the diff for internal consistency (Step 4 and the Constraints bullet agree)
and confirming no other file in `skills/capture/` still references the
per-note routing offer (`grep -rn "route" skills/capture/`).

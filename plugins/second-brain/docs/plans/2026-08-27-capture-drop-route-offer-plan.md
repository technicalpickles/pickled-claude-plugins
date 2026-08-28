# Capture: Drop the Per-Note Routing Offer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the per-note "want me to route it?" question from `second-brain:capture`, since `process-inbox` already owns routing.

**Architecture:** Single-file prose edit to `plugins/second-brain/skills/capture/SKILL.md` in the `pickled-claude-plugins` repo — no code, no tests, no `description:` change. Design is fully specified in `plugins/second-brain/docs/plans/2026-08-27-capture-drop-route-offer-design.md`; this plan just sequences the edit, verification, version bump, and PR.

**Tech Stack:** Markdown (Claude Code skill file). Repo tooling: `scripts/bump-version.sh`, `scripts/check-commit-scope.sh` (conventional-commit CI gate), `gh` for the PR.

---

### Task 1: Edit `capture/SKILL.md` — Step 4 and the Constraints bullet

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md:115-126` (Step 4)
- Modify: `plugins/second-brain/skills/capture/SKILL.md:183` (Constraints bullet)

- [ ] **Step 1: Replace Step 4**

Find this exact block (lines 115-126):

```markdown
## Step 4: Leave it in the inbox - routing is opt-in

The note stays where sb put it. **Offer** to route it; do not route it.

This overrides the vault's general "capture: file rough, move on / a wrong-but-close
home beats the global inbox" guidance, which governs notes *the user* files by hand. Notes *the agent* writes on
request stay in the inbox until the user says otherwise. Both rules coexist in the vault CLAUDE.md
and the scope of the override has historically been read as ambiguous, which produced a roughly
50/50 split between inbox and direct-to-area filing. It is not ambiguous: **agent-written note on
request → inbox, stop.**

The exception is an explicit destination from the user ("put it in 66"). Then write it there.
```

Replace it with:

```markdown
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

- [ ] **Step 2: Replace the Constraints bullet**

Find this exact line:

```markdown
- **Inbox by default.** Routing is offered, not performed.
```

Replace it with:

```markdown
- **Inbox by default.** Routing is `process-inbox`'s job — capture never asks or
  routes, except an explicit user-named destination, resolved via `sb vault
  structure` like `route` does, never hand-rolled.
```

- [ ] **Step 3: Verify no leftover per-note routing-offer language**

Run:

```bash
grep -n "route\|Route" plugins/second-brain/skills/capture/SKILL.md
```

Expected matches, and only these:
- Line 3 (`description:`) — mentions `route` as the *other* skill capture defers to (unchanged, correct)
- The new Step 4 block (mentions `route`, `sb vault structure`, `sb note move` — the resolution path, correct)
- The new Constraints bullet (correct)
- Line ~67 ("Notes get routed between folders constantly" in the search-fallback section) — unrelated, leave as is

If any other line mentions offering to route, the edit is incomplete — fix before continuing.

- [ ] **Step 4: Read the full file once for internal consistency**

Read `plugins/second-brain/skills/capture/SKILL.md` top to bottom. Confirm:
- Step 4's heading, body, and the Constraints bullet all agree (no offer, no mention, exception uses `sb vault structure` + `sb note move`)
- Step 5 (connect offer, daily breadcrumb) is untouched
- `references/note-format.md` is not touched (design doc confirmed it's already consistent)

- [ ] **Step 5: Commit**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "$(cat <<'EOF'
fix(second-brain): drop capture's per-note routing offer

process-inbox already auto-routes above a confidence threshold and
only surfaces low-confidence notes for a decision. capture's
per-note "want me to route it?" question duplicated that decision
instead of deferring to it. Capture now leaves the note in the
inbox silently; the only exception is an explicit user-named
destination, resolved via `sb vault structure` the way route
resolves destinations, never hand-rolled.
EOF
)"
```

---

### Task 2: Bump the plugin version

**Files:**
- Modify: `.claude-plugin/marketplace.json` (version bump)
- Modify: `README.md` (plugin table, if `generate-plugin-table.sh` changes it — it won't here, since no plugin description changed, but the script still runs as part of `--auto`)

- [ ] **Step 1: Run the auto-bump script**

```bash
./scripts/bump-version.sh --auto
```

Expected output: reports a version bump for `second-brain` (patch bump, since this is a `fix(second-brain)` commit — behavior fix, not a new feature).

- [ ] **Step 2: Verify the diff**

```bash
git diff
```

Expected: `.claude-plugin/marketplace.json` shows `second-brain`'s version incremented by patch (e.g. `1.10.1` → `1.10.2` — check the actual current version in the file first, since it may have moved since this plan was written). No unrelated version bumps.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json README.md
git commit -m "chore(second-brain): bump version to <version-from-step-1>"
```

(Fill in `<version-from-step-1>` with the actual number the script reported — don't guess it ahead of running the script.)

---

### Task 3: Open the PR

**Files:** none (GitHub operation)

- [ ] **Step 1: Push the branch**

```bash
git push -u origin capture-drop-route-offer
```

- [ ] **Step 2: Open the PR**

```bash
gh pr create --title "fix(second-brain): drop capture's per-note routing offer" --body "$(cat <<'EOF'
## Summary
- `second-brain:capture` no longer asks "want me to route it?" after writing a note — that's `process-inbox`'s job, which already auto-routes above a confidence threshold.
- The one exception (an explicit destination named in the same conversation, e.g. "put it in 66") now resolves through `sb vault structure` the way `route` does, instead of writing a hand-rolled path.

## Why
Per-note capture already asks about the daily breadcrumb-adjacent connect offer and, until now, routing too — three round-trips per note. The breadcrumb one was fixed in #111. This closes the routing half: it was a duplicated decision point sitting on top of a batch routing path (`process-inbox`) that already exists and already handles low-confidence cases by asking.

## Test plan
- [ ] Read the diff: Step 4 and the Constraints bullet agree, Step 5 (connect offer, breadcrumb) untouched
- [ ] `description:` frontmatter unchanged — no eval re-run needed
- [ ] CI green (commit-scope check, version-bump check)
EOF
)"
```

- [ ] **Step 3: Confirm CI is green**

```bash
gh pr checks --watch
```

Expected: both checks (commit-scope validation, version-bump check) pass. If either fails, read the failure output and fix before re-pushing — don't skip checks.

---

## Not in this plan

- Merging the PR — that's a human call, done by Josh after review.
- Updating bean `gt-6zaa` — mark it `completed` with the merge SHA once the PR actually merges (matches the `1fxi` precedent: don't mark done until the PR is in).
- Any change to the Step 5 connect offer, `devlog`, or `route`/`process-inbox` skills — explicitly out of scope per the design doc.

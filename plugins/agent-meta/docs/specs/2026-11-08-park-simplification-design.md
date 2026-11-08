# Park: one mechanism for where parks go

**Date:** 2026-11-08
**Status:** Proposed
**Plugins:** agent-meta, second-brain

## Goal

Make park and unpark simple and consistent: one rule for where a park lives, no settings to learn, one filename scheme. Backward compatibility counts, but the only known user of the current knobs is the author.

## Problem

PR #176 made parks go to the second-brain vault. It added several overlapping ways to say where a park goes and what happens to it afterward. They were added one at a time and never lined up with how devlog picks a vault.

Where a park goes is decided by up to five things:

1. The `Park vault:` line from the second-brain `skill.prompt` mod, which reads the default vault from `~/.claude/second-brain.md`.
2. The `park_vault` second-brain setting.
3. The `park_in_vault` second-brain setting.
4. The vault's own `CLAUDE.md` `## Parking` section (`Location:` and a filename convention).
5. A `## Handoffs` or `## Parking` `Location:` in the project or user `CLAUDE.md`, with `.parkinglot/` as the last fallback.

What happens to a park afterward adds the `destination` and `destination_helper` agent-meta settings, plus the legacy `AGENT_PARK_DESTINATION` and `AGENT_PARK_DESTINATION_HELPER` env vars.

devlog answers the same "which vault" question differently. It runs `scripts/resolve-vault.sh`, which honors `SB_NOTE_VAULT`, then the registered vault containing the working directory, then sb's default. It has no settings for any of this.

## Evidence on who uses what

Measured on the author's machine on 2026-11-08:

- No `AGENT_PARK_*` or `SB_NOTE_VAULT` variable in the environment, the dotfiles repo, or the shell rc files.
- No `## Parking` or `## Handoffs` section in the user `CLAUDE.md` or the dotfiles `claude/` sources. Only the vault's `CLAUDE.md` has a `Location:`.
- No other plugin hardcodes `.parkinglot`. The pickle-mode, stay-on-target and taskwarrior hits for "park" are the word, not the path.
- About ten repos under `~/github.com` have a `.parkinglot/` directory of older parks.

Other marketplace installs are invisible from here. The recommendation below assumes they are few.

## Proposal

### 1. Delete destination

Remove the `destination` and `destination_helper` settings, the legacy env vars, the agent-meta `skill.prompt` hook, its 11 tests, the `dest` case in the e2e script, and the docs. agent-meta's `register.ts` goes back to registering `/session-id` only.

Why: destination was the route for filing a park into a second brain. The vault now does that natively. Its documented `sb note create` example also puts parks in the inbox, where `process-inbox` tries to route them, and the vault's `CLAUDE.md` says parks are operational state, not knowledge notes. Nothing in the author's environment sets it.

This reverses part of #176, which added the settings at the author's request.

### 2. Delete `park_in_vault` and `park_vault`

The rule becomes: if second-brain is installed and configured, parks go to the vault. Opting out means not having second-brain set up.

There is no per-project opt-out, on purpose. A repo whose parks should stay out of the vault (for example a work repo and a personal vault) is not supported. If that need shows up, solve it in the shared resolver (see Deferred), not by bringing back `park_in_vault`.

Files that reference the settings and change with them:

- `plugins/second-brain/hooks/park-vault/register.ts` and `register.test.ts`
- `plugins/second-brain/.claude-plugin/plugin.json` (the settings schema)
- `plugins/second-brain/README.md`
- `plugins/agent-meta/tests/e2e/park-vault.sh`
- `plugins/agent-meta/docs/verifying-park.md`

### 2a. The mod honors `SB_NOTE_VAULT`

The mod resolves the vault as `SB_NOTE_VAULT` if set, otherwise the default vault from `second-brain.md`. That matches the first step of devlog's `scripts/resolve-vault.sh`, so park and devlog agree on the override.

While the mod is open, it should also read `second-brain.md` from `$CLAUDE_CONFIG_DIR` when set, per the repo `CLAUDE.md`, instead of hardcoding `$HOME/.claude`.

This also gives the e2e script its scratch-vault lever: export `SB_NOTE_VAULT=$VAULT` in place of the `park_vault` setting. A scratch `HOME` does not work, because the script finds transcripts under `$HOME/.claude/projects` and `claude -p` needs the real config dir for auth.

### 3. One filename rule, owned by the skill

Every park is `YYYYMMDDHHMM topic.md` (and `-wrapped` or `-checkpoint` before the extension), in the vault or in `.parkinglot/`. The vault's `## Parking` section then only needs `Location:`. Delete the "the skill emits a bare slug, add the prefix yourself" caveat from the vault `CLAUDE.md`.

Existing `.parkinglot` files keep working. Unpark identifies them by suffix and first heading, not by a timestamp.

### 4. Collapse the location chain

Resolve in this order:

1. `Park vault:` line present and the vault's `CLAUDE.md` has a `## Parking` section with `Location:`: use that location.
2. Otherwise `.parkinglot/` in the project root. This covers a vault with no `## Parking` section, so a half-configured vault never sends parks to a guessed folder.

Drop the project and user `CLAUDE.md` `Location:` lookups. The vault keeps its own `## Parking`.

### 5. Fix unpark visibility

[unpark/SKILL.md](../../skills/unpark/SKILL.md) checks locations in order, and step 1 only falls through when the vault's `CLAUDE.md` or its `## Parking` section is missing. So with a vault configured, parks in a repo's `.parkinglot/` are never listed.

Fix: unpark lists parks from the vault and from the local `.parkinglot/` together, grouped as it does today.

## Deferred: one shared resolver

devlog and park should ask one question, "which vault applies to this session", and get one answer. Today the answer lives in a bash script that devlog runs from its own plugin root. The park mod cannot reuse it without a TypeScript copy.

The right home is a command in the `sb` CLI, for example `sb vault resolve`. devlog, the park mod and anything later would call it. That change belongs in the `sb` repository.

Until it exists, park uses `SB_NOTE_VAULT` or the default vault (§2a), so it shares devlog's first step but not the working-directory step. On a one-vault machine that gives the same answer as devlog. When a second vault is registered, the two can disagree for sessions whose working directory is inside the non-default vault.

## Considered and not recommended

**Skill-instructed resolution.** Drop the mod, and have the park skill tell the model to run `sb` commands, as devlog does. This removes the mod but loses the deterministic delivery check (the transcript grep in `tests/e2e/park-vault.sh`), and adds an `npx` round trip to every park. Revisit only if the mod becomes a maintenance burden.

## Result

- Park has one injected value, the vault path. It has no settings and no env vars of its own; it reads `SB_NOTE_VAULT`, which second-brain already defines.
- The second-brain mod stays, about 25 lines.
- A net deletion, mostly the destination hook, its tests and the e2e `dest` case. Measure the real number from the diff.

## Migration and versioning

- Removing settings and env vars is a breaking change. Per [docs/versioning.md](../../../../docs/versioning.md), mark the commits with `!` or a `BREAKING CHANGE:` footer, which means a major bump for both agent-meta and second-brain.
- Anyone relying on `destination` loses it. The README should say so and point at the vault as the replacement.
- Delete the stale caveat in the vault `CLAUDE.md` after the skill change ships.

## Resolved questions

- **Opt-out:** global only, by not configuring second-brain. No per-project opt-out (§2).
- **e2e scratch vault:** `SB_NOTE_VAULT` (§2a).
- **Versioning:** major bump for both plugins.

## Verification

Reuse the layers in `plugins/agent-meta/docs/verifying-park.md`. The mod unit tests and the e2e cases for `slash`, `plain`, `unpark` and the vault landing stay, switched from the `park_vault` setting to `SB_NOTE_VAULT`. The `off` and `dest` cases go.

Add:

- Mod unit tests: `SB_NOTE_VAULT` wins over `second-brain.md`; `CLAUDE_CONFIG_DIR` is honored.
- An e2e case where `.parkinglot/` holds an older park and a vault is configured; assert unpark lists both.
- An e2e or skill-level check that a vault with no `## Parking` section sends the park to `.parkinglot/`.

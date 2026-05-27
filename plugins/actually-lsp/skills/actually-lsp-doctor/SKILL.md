---
name: actually-lsp-doctor
description: Diagnose and fix LSP setup for the current project's detected ecosystems (Rust, TypeScript, Ruby). Use when the SessionStart hook nudged about a missing LSP plugin, when the env isn't ready (no `bundle install`, no `cargo build`, missing server binary), when LSP calls are failing, or when the user invokes `/actually-lsp-doctor` directly. Walks the per-ecosystem state machine, reports what's missing, then runs the fix.
---

# /actually-lsp-doctor

Parse the user's args from the invocation:

- `fix` as the first arg means skip the diagnostic report and jump straight to action.
- `rust` | `typescript` | `ruby` as an arg narrows focus to that ecosystem.
- No args: full diagnostic report followed by interactive fix.

## Step 1: Read project state

Read `.claude/actually-lsp.json` in the current project root. If missing, run detection: source `lib/detect.sh` and `lib/ecosystems.sh` from the plugin root (the env var `CLAUDE_PLUGIN_ROOT` points there), call `detect_ecosystems "$PWD"`, and for each detected ecosystem compute the current state per the rules in `CONTEXT.md`.

## Step 2: Diagnose (unless `fix` arg present)

Output a per-ecosystem report. For each ecosystem:

- State (from `CONTEXT.md`'s six states)
- For non-`ready` ecosystems: what's needed to reach `ready`
- For `dismissed` ecosystems: note them but don't propose action

Keep tone terse. No celebration messaging.

## Step 3: Act

For each ecosystem in `no-lsp-plugin`, `server-not-runnable`, or `error`:

**`no-lsp-plugin`**: try `claude plugin install <recommended_plugin>@claude-plugins-official` via Bash. The user gets a permission prompt. If denied, output the slash command form (`/plugin install <recommended_plugin>@claude-plugins-official`) and ask the user to run it themselves.

**`server-not-runnable`**: run env fixes per ecosystem via Bash. All env fixes auto-run; the user has implicit project consent.

- Rust: `cargo build`
- TypeScript: `npm install`
- Ruby: `bundle install`, plus `gem install ruby-lsp` if `command -v ruby-lsp` is empty

**`error`**: surface the cached `last_error` from the state file. Ask the user how to proceed.

## Step 4: Re-detect and report

Re-run detection (same as Step 1's "if missing" path). Update the project state file. Output a final per-ecosystem status line.

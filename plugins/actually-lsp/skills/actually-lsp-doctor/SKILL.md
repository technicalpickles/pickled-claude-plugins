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

**`server-not-runnable`**: run env fixes per ecosystem via Bash. All env fixes auto-run; the user has implicit project consent. Check `readiness_source` in the state file to aim the fix: `binary` means the server binary is missing or non-functional (fix the binary, not the deps); `heuristic`/`probe` means the binary ran but the project env needs work (build deps).

- **TypeScript**: `npm install`.
- **Ruby**: `bundle install`, plus `gem install ruby-lsp` if `command -v ruby-lsp` is empty.
- **Rust**: the binary is the usual culprit, and `cargo build` does NOT fix it. The `rust-analyzer-lsp` plugin launches a bare `rust-analyzer` from PATH, which is often a rustup proxy that is non-functional when the `rust-analyzer` component isn't installed for the active toolchain (`rust-analyzer is unavailable for the active toolchain`). Recover in order:
  1. **Binary**: if `rust-analyzer --version` fails or prints `unavailable for the active toolchain` (test it, don't trust `command -v` alone, since the proxy resolves but doesn't run), run `rustup component add rust-analyzer`. This makes the bare `rust-analyzer` the LSP tool launches actually work. If `rustup` is absent, tell the user to install rust-analyzer so a working binary is first on PATH (rustup component, mise, or brew) and stop.
  2. **Standard library**: rust-analyzer needs `rust-src` to load std; without it nav can return nothing. If `rustc --print sysroot` has no `lib/rustlib/src`, run `rustup component add rust-src`.
  3. **Deps / proc-macros**: `cargo build` so dependency and macro-generated symbols resolve (intra-project nav works without this, but full semantics need it).
  Then let Step 5 re-probe to confirm the server actually answers.

**`error`**: surface the cached `last_error` from the state file. Ask the user how to proceed.

## Step 4: Re-detect

Re-run detection (same as Step 1's "if missing" path) and compute the new state per ecosystem. Hold the result in memory; don't write the state file yet. Step 5 may downgrade `ready` ecosystems before persistence.

## Step 5: Probe ready ecosystems via LSP

The goal is to ground a `ready` verdict in an actual LSP response, not just env state. Env can say "server should run" while the server fails to answer queries (not indexed yet, wrong workspace root, crashed).

For each ecosystem whose computed state is `ready`:

1. **Ensure the `LSP` tool is loaded.** If it isn't available in this session, call `ToolSearch` with query `select:LSP`. If `ToolSearch` returns no match, skip the probe for *every* ecosystem and note "LSP tool unavailable in session" in the report. Do not downgrade any state. This is an environment issue, not an ecosystem failure.

2. **Find a sample source file** under `$PROJECT_DIR`:
   - rust: `find "$PROJECT_DIR" -maxdepth 4 -type f -name '*.rs' -print -quit`
   - typescript: `find "$PROJECT_DIR" -maxdepth 4 -type f \( -name '*.ts' -o -name '*.tsx' \) -print -quit`
   - ruby: `find "$PROJECT_DIR" -maxdepth 4 -type f -name '*.rb' -print -quit`

   If no file is found, skip the probe for this ecosystem and note "no sample file" in the report. Do not downgrade.

3. **Call `LSP documentSymbol`** against the sample file at `line: 1, character: 1`.

4. **On error or non-array response:** downgrade the ecosystem to `error` and set `last_error` to the stringified LSP response (or a short summary if the response is large). Env said the server should be runnable, so a probe failure is a real LSP failure worth surfacing on the next SessionStart.

5. **On success:** count the symbols in the response array. State stays `ready`. The count is for the report only; nothing extra goes into the state file.

## Step 6: Write state and final report

Write the (possibly probe-updated) per-ecosystem state to `.claude/actually-lsp.json` using `write_state` from `lib/state.sh`. Output one status line per ecosystem:

- `ready` with successful probe: `<ecosystem>: ready (LSP: N symbols)`
- `ready` with skipped probe: `<ecosystem>: ready (LSP: skipped, <reason>)`
- `error` from probe failure: `<ecosystem>: error (LSP probe failed: <summary>)`
- Other states: `<ecosystem>: <state>` plus the recovery hint from Step 2

Keep tone terse. No celebration messaging.

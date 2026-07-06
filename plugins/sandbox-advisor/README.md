# sandbox-advisor

A `PostToolUseFailure` hook that, when a Bash command fails, tells you whether it
failed because of a *known* Claude Code sandbox limitation, and what to do about
it. The message is advisory, not a directive.

## What it does

Knowledge lives in a **failure-mode registry**. Each mode pairs a command
matcher with the error fingerprints that mode is known to produce. When a Bash
command **fails**, the hook checks whether the command matches a known mode and
whether that mode's fingerprints appear in the failure output. Five modes ship,
all of which need to run unsandboxed:

- **git writes inside pt worktrees** -- blocked-path set (`.claude/`, `.vscode/`,
  `.gitmodules`) and `.git/worktrees/.../index.lock`. This deny is *polymorphic*:
  it surfaces as `index.lock`, a blocked-path `Operation not permitted`, or a
  downstream `Could not reset index file`, so this mode carries a broad
  fingerprint set.
- **`srb` (sorbet)** -- LMDB uses SysV semaphores the sandbox denies.
- **`ps` / `top`** -- setuid-root binaries; the sandbox denies setuid exec.
- **git/gh over SSH** (`git push`/`fetch`/`pull`/`clone`/`ls-remote`, or
  `gh pr checkout`/`gh repo sync` against a repo whose remote is an SSH URL)
  -- the sandbox network layer only allows HTTPS to specific allowlisted
  hosts, so raw SSH on port 22 is denied outright, regardless of the
  ssh-agent socket (which is already open via `allowAllUnixSockets`).
  `gh`'s broader command surface is pure REST/GraphQL over HTTPS and
  unaffected; only `pr checkout`/`co`/`sw` and `repo sync` shell out to git
  against the *current repo's existing remote* (so they inherit whatever
  protocol that remote already uses). Commands that clone fresh (`repo
  clone`, `gist clone`, `repo fork --clone`, `extension install`) use gh's
  own `git_protocol` config instead, independent of any local remote, and
  aren't affected unless that config is set to `ssh`. Confirmed empirically:
  `ssh -T git@github.com` fails with `connect to host github.com port 22:
  Operation not permitted`; `git`'s own SSH transport (via `core.sshCommand`)
  fails differently, with `nc: authentication method negotiation failed` /
  `Connection closed by UNKNOWN port`. `gh` wraps the latter with `failed to
  run git: exit status 128`. The durable fix is switching the remote/gh
  protocol to HTTPS, not a sandbox setting -- there's no `allowedHosts`-style
  knob for raw TCP ports.
- **macOS Keychain writes** (`gh auth login`/`refresh`/`logout`/`setup-git`,
  or `security add-*-password`/`delete-*-password`) -- Keychain *writes* go
  through a `Security.framework` call the sandbox denies outright
  (`SecKeychainItemCreateFromContent ... Operation not permitted`). Reads are
  unaffected: `security find-generic-password` and `gh auth status` (which
  reads an already-stored token) both succeed sandboxed. There's no durable
  sandbox-side fix here either; the practical workaround is running the
  auth/write step once unsandboxed -- subsequent reads of that credential
  work fine sandboxed.

When a mode matches, it injects an advisory note ("this command is known to fail
under the sandbox; if that's why it failed, re-run with
`dangerouslyDisableSandbox: true`"). Otherwise it stays silent. Adding a new
failure mode is appending a registry entry (matcher + fingerprints + advice).

## Why reactive (not a proactive guard)

A command-name guard mis-fires: `git add` fails sandboxed only ~4% of the time
(only in worktrees). Acting on the actual failure means a command that succeeds
sandboxed is never touched, so the hook can never cause a false sandbox bypass.

## Who it's for

Auto-mode already retries unsandboxed for you. This plugin covers the contexts
auto-mode does not reliably reach: subagents, cron/headless runs, and teammates
not on auto-mode, where a hard EPERM is a stall instead of a recovery.

## Guarantees

- **Fail-open.** Any internal error exits 0 with no output; the raw failure
  surfaces unchanged. A broken advisor never wedges work.
- **No rewrite, no block, no state.** It only ever adds advice to an
  already-failed command.

## Background

See the deny-surface evidence and friction data this is built on:
the sandbox-probe results and the transcript-mining sandbox-friction findings
in the pickletown workspace.

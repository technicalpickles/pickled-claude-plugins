---
name: sandbox-first
description: Use when a Bash command fails in the sandbox, or when considering whether to use dangerouslyDisableSandbox. Guides sandbox-first execution and sandbox config diagnosis.
---

# Sandbox-First Execution

## Core Rule

Always run Bash commands sandboxed first. Never set `dangerouslyDisableSandbox: true` unless
a sandboxed attempt has already failed in this session, or the command is listed in
`skip_failure_requirement` (see Configured Exceptions below).

## When a Sandboxed Command Fails

Before retrying with `dangerouslyDisableSandbox`:

1. **Read the error.** What specifically failed?
2. **Is it a sandbox restriction?** Look for:
   - "Operation not permitted" (filesystem write outside allowed paths)
   - "Connection refused" or network timeouts (host not in allowedHosts)
   - "Permission denied" on paths outside the project
   - **macOS Mach port / XPC denial** — crash containing `bootstrap_check_in`
     and "Permission denied (1100)". The surface error looks like an
     application crash (e.g. Chromium `Check failed: kr == KERN_SUCCESS`),
     but the root cause is seatbelt denying `mach-register`/`mach-lookup`
     for a service. Seen with Playwright launching headless Chromium, and
     applies to other multi-process macOS tools (Electron, Puppeteer, etc.).
     Sandbox config cannot grant Mach port access, so this genuinely
     requires `dangerouslyDisableSandbox`.
3. **Suggest a config fix.** Tell the user what to add to `~/.claude/settings.json`:
   - Network: add host to `sandbox.network.allowedHosts`
   - Filesystem: add path to `sandbox.filesystem.allowWrite`
4. **If retrying unsandboxed**, explain what restriction was hit and why the sandbox
   config change would be the better long-term fix.

## Configured Exceptions

Some commands are known to always fail in the sandbox (e.g. `docker`, `colima ssh`).
These can be configured in `~/.claude/sandbox-first.json` or `.claude/sandbox-first.json`
under the `skip_failure_requirement` key. The enforcement hook will allow
`dangerouslyDisableSandbox: true` for these commands without requiring a prior
sandboxed failure.

## What NOT to Do

- Do not preemptively use `dangerouslyDisableSandbox` because you think a command
  "might" fail in the sandbox. Try it first.
- Do not silently retry unsandboxed after a sandbox failure. Always surface what happened.
- Do not use `dangerouslyDisableSandbox` for convenience. It exists for cases where the
  sandbox genuinely cannot support the operation.

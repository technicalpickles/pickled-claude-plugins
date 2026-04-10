---
name: sandbox-first
description: Use when a Bash command fails in the sandbox, or when considering whether to use dangerouslyDisableSandbox. Guides sandbox-first execution and sandbox config diagnosis.
---

# Sandbox-First Execution

## Core Rule

Always run Bash commands sandboxed first. Never set `dangerouslyDisableSandbox: true` unless
a sandboxed attempt has already failed in this session.

## When a Sandboxed Command Fails

Before retrying with `dangerouslyDisableSandbox`:

1. **Read the error.** What specifically failed?
2. **Is it a sandbox restriction?** Look for:
   - "Operation not permitted" (filesystem write outside allowed paths)
   - "Connection refused" or network timeouts (host not in allowedHosts)
   - "Permission denied" on paths outside the project
3. **Suggest a config fix.** Tell the user what to add to `~/.claude/settings.json`:
   - Network: add host to `sandbox.network.allowedHosts`
   - Filesystem: add path to `sandbox.filesystem.allowWrite`
4. **If retrying unsandboxed**, explain what restriction was hit and why the sandbox
   config change would be the better long-term fix.

## What NOT to Do

- Do not preemptively use `dangerouslyDisableSandbox` because you think a command
  "might" fail in the sandbox. Try it first.
- Do not silently retry unsandboxed after a sandbox failure. Always surface what happened.
- Do not use `dangerouslyDisableSandbox` for convenience. It exists for cases where the
  sandbox genuinely cannot support the operation.

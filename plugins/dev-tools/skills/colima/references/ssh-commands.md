# SSH Commands in Colima VMs

## Overview

Colima VMs require specific syntax for remote command execution. The key insight: `colima ssh` passes arguments directly to the VM, so shell operators (`&&`, `|`, `;`) need explicit bash wrapping.

## Core Pattern

```bash
# Single command - works without wrapper
colima ssh -p <profile> -- <command>

# Multiple commands or shell operators - REQUIRES bash -c
colima ssh -p <profile> -- bash -c "<command1> && <command2>"
```

## Quick Reference

| Task | Command |
|------|---------|
| Single command | `colima ssh -p incus -- uname -a` |
| Multiple commands | `colima ssh -p incus -- bash -c "cmd1 && cmd2"` |
| Pipes | `colima ssh -p incus -- bash -c "cat /etc/os-release \| head -5"` |
| With variables | `colima ssh -p incus -- bash -c "export FOO=bar && echo \$FOO"` |

## Common Mistakes

### Wrong: Quoting entire command string

```bash
# Fails - treats entire string as command name
colima ssh -p incus "uname -a && whoami"
# Error: No such file or directory
```

### Wrong: Shell operators without wrapper

```bash
# Fails - && interpreted by local shell, not VM
colima ssh -p incus -- uname -a && whoami
# Runs whoami locally, not in VM
```

### Correct: Explicit bash wrapper

```bash
colima ssh -p incus -- bash -c "uname -a && whoami"
```

## Escaping Inside bash -c

Inside `bash -c "..."`, escape:
- `$` as `\$` (unless you want local expansion)
- `"` as `\"`
- Pipes `|` may need escaping depending on local shell

```bash
# Variable in VM
colima ssh -p incus -- bash -c "echo \$HOME"

# Pipe in VM
colima ssh -p incus -- bash -c "cat /etc/passwd \| grep root"
```

## Testing Pattern

When working with unfamiliar Colima setups, verify syntax first:

```bash
# Step 1: Test basic connectivity
colima ssh -p <profile> -- echo "test"

# Step 2: Test command chaining
colima ssh -p <profile> -- bash -c "echo one && echo two"

# Step 3: Proceed with actual commands
```

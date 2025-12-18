# Working with Colima Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a skill that helps Claude assist users with Colima (Docker runtime for macOS) - lifecycle management, profile handling, Docker context integration, and troubleshooting.

**Architecture:** Progressive disclosure structure - small SKILL.md (~100-150 lines) as navigation map, detailed content in `references/` directory. Follows the "200-line rule" from skill best practices.

**Tech Stack:** Markdown skill file, Colima CLI, Docker CLI

**Skill Structure:**
```
plugins/dev-tools/skills/working-with-colima/
├── SKILL.md                    # Entry point: overview, quick ref, navigation
└── references/
    ├── docker-contexts.md      # Docker context integration details
    ├── profile-management.md   # Creating, switching, deleting profiles
    ├── troubleshooting.md      # All troubleshooting scenarios
    └── common-options.md       # Flags and configuration
```

---

## Task 1: Create Skill Directory Structure

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/`
- Create: `plugins/dev-tools/skills/working-with-colima/references/`

**Step 1: Create the skill directories**

```bash
mkdir -p plugins/dev-tools/skills/working-with-colima/references
```

**Step 2: Verify directories exist**

Run: `ls -la plugins/dev-tools/skills/working-with-colima/`
Expected: Shows `references/` subdirectory

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima
git commit -m "chore(dev-tools): create working-with-colima skill directory structure"
```

---

## Task 2: Write SKILL.md Entry Point

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Write SKILL.md with frontmatter, overview, and quick reference**

The entry point should be ~100-150 lines. It's a navigation map, not a manual.

```markdown
---
name: working-with-colima
description: Use when Docker commands fail with "Cannot connect to Docker daemon", when starting/stopping container environments, or when managing multiple Docker contexts on macOS - provides Colima lifecycle management, profile handling, and troubleshooting
---

# Working with Colima

## Overview

Colima provides container runtimes (Docker, Containerd) on macOS with minimal setup. It runs a Linux VM and exposes Docker via contexts.

**Use this skill when:**
- Docker commands fail ("Cannot connect to Docker daemon")
- Starting/stopping container runtime on macOS
- Managing multiple Docker profiles/contexts
- Troubleshooting container environment issues
- Need SSH agent forwarding for Docker builds

**Not for:** Docker Compose, Kubernetes clusters, or Linux environments.

## Quick Reference

| Operation | Command |
|-----------|---------|
| Start | `colima start` or `colima start <profile>` |
| Start with SSH agent | `colima start <profile> -s` |
| Stop | `colima stop` or `colima stop --force` |
| Status | `colima status -p <profile>` |
| List profiles | `colima list` |
| SSH into VM | `colima ssh` or `colima ssh -- <cmd>` |
| Get socket path | `colima status -p <profile> --json \| jq -r .docker_socket` |

## Docker Context Basics

Colima creates Docker contexts per profile:
- Profile `default` → context `colima`
- Profile `work` → context `colima-work`

```bash
# Switch context (global - affects all terminals)
docker context use colima-work

# Override per-session
export DOCKER_CONTEXT=colima-work

# Override per-command
docker --context colima-work ps
```

For details, see `references/docker-contexts.md`.

## Common Issues

**Docker daemon not connecting?**
1. `colima status` - is it running?
2. `docker context list` - right context selected?
3. See `references/troubleshooting.md` for more

**Need more VM resources?**
```bash
colima stop && colima start --cpu 4 --memory 8
```

**"Broken" status after restart?**
```bash
colima stop --force && colima start
```

## References

- `references/docker-contexts.md` - Context switching, DOCKER_HOST, socket paths
- `references/profile-management.md` - Creating, configuring, deleting profiles
- `references/troubleshooting.md` - Common issues and solutions
- `references/common-options.md` - Flags, VM types, resource configuration

## External Resources

For updated Colima documentation:
```bash
uvx gitingest https://github.com/abiosoft/colima -i "*.md" -o colima-docs.txt
```

See also: [Colima FAQ](https://github.com/abiosoft/colima/blob/main/docs/FAQ.md)
```

**Step 2: Verify file length and structure**

Run: `wc -l plugins/dev-tools/skills/working-with-colima/SKILL.md`
Expected: ~80-100 lines (well under 200-line limit)

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
git commit -m "feat(dev-tools): add working-with-colima skill entry point"
```

---

## Task 3: Write Docker Contexts Reference

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/references/docker-contexts.md`

**Step 1: Write docker-contexts.md**

```markdown
# Docker Context Integration

## How Colima Creates Contexts

Each Colima profile creates a corresponding Docker context:

| Colima Profile | Docker Context |
|----------------|----------------|
| `default` | `colima` |
| `work` | `colima-work` |
| `<name>` | `colima-<name>` |

Colima sets itself as the default context on startup.

## Switching Contexts

### Global Switch (Persistent)

Stored in `~/.docker/config.json` under `currentContext`. Affects all terminals.

```bash
# List available contexts
docker context list

# Switch globally
docker context use colima-work
```

### Per-Session Override

```bash
export DOCKER_CONTEXT=colima-work
```

### Per-Command Override

```bash
docker --context colima-work ps
docker --context colima-work build -t myimage .
```

## Getting the Socket Path

Some applications don't respect Docker contexts and need `DOCKER_HOST` set explicitly.

```bash
# View full status including socket
colima status -p <profile>

# Extract just the socket path
colima status -p <profile> --json | jq -r .docker_socket

# Set DOCKER_HOST for non-context-aware apps
export DOCKER_HOST="unix://$(colima status -p work --json | jq -r .docker_socket)"
```

## Socket Locations

- Default profile: `~/.colima/default/docker.sock`
- Named profile: `~/.colima/<profile>/docker.sock`

## Running Multiple Profiles Simultaneously

You can run multiple Colima profiles at once, each with its own Docker context:

```bash
colima start default
colima start work --cpu 4 --memory 8

# Now both contexts exist
docker context list
# NAME          DESCRIPTION  DOCKER ENDPOINT
# colima        colima       unix:///.../.colima/default/docker.sock
# colima-work   colima       unix:///.../.colima/work/docker.sock
```

Switch between them as needed, or use per-command `--context` flags.
```

**Step 2: Verify file was created**

Run: `head -20 plugins/dev-tools/skills/working-with-colima/references/docker-contexts.md`
Expected: Shows title and first section

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/references/docker-contexts.md
git commit -m "feat(dev-tools): add docker contexts reference for colima skill"
```

---

## Task 4: Write Profile Management Reference

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/references/profile-management.md`

**Step 1: Write profile-management.md**

```markdown
# Profile Management

## Creating Profiles

### Default Profile

```bash
colima start
```

Creates a profile named `default` with default resources (2 CPU, 2GB RAM, 100GB disk).

### Named Profiles

```bash
# Basic named profile
colima start work

# With custom resources
colima start work --cpu 4 --memory 8 --disk 60

# With SSH agent forwarding (for git in Docker builds)
colima start work -s
# or
colima start work --ssh-agent
```

### Using Config Files

```bash
# Edit config before starting
colima start work --edit

# Edit default template (affects new profiles)
colima template
```

## Profile Configuration Locations

| File | Purpose |
|------|---------|
| `~/.colima/<profile>/colima.yaml` | Config for specific profile |
| `~/.colima/_templates/default.yaml` | Default template for new profiles |

## Listing Profiles

```bash
colima list
```

Output shows:
```
PROFILE    STATUS     ARCH       CPUS    MEMORY    DISK     RUNTIME    ADDRESS
default    Running    aarch64    2       2GiB      60GiB    docker
work       Running    aarch64    4       8GiB      60GiB    docker
```

## Checking Profile Status

```bash
# Current/default profile
colima status

# Specific profile
colima status -p work

# JSON output (for scripting)
colima status -p work --json
```

## Stopping Profiles

```bash
# Graceful stop
colima stop
colima stop -p work

# Force stop (use for "Broken" status)
colima stop --force
colima stop -p work --force
```

## Deleting Profiles

```bash
# Delete profile (keeps container data)
colima delete work

# Delete profile AND container data (v0.9.0+)
colima delete work --data
```

## Modifying Running Profiles

Resource changes require stopping first:

```bash
colima stop -p work
colima start work --cpu 4 --memory 8
```

Or edit the config file:

```bash
colima stop -p work
colima start work --edit  # Modify values, save, exits editor to start
```
```

**Step 2: Verify file was created**

Run: `wc -l plugins/dev-tools/skills/working-with-colima/references/profile-management.md`
Expected: ~90-110 lines

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/references/profile-management.md
git commit -m "feat(dev-tools): add profile management reference for colima skill"
```

---

## Task 5: Write Troubleshooting Reference

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/references/troubleshooting.md`

**Step 1: Write troubleshooting.md**

```markdown
# Troubleshooting

## "Cannot connect to Docker daemon"

**Symptoms:**
- `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`
- `Is the docker daemon running?`

**Diagnosis:**

```bash
# 1. Is Colima running?
colima status
colima status -p <profile>

# 2. Which Docker context is active?
docker context list
```

**Solutions:**

1. **Colima not running:** Start it
   ```bash
   colima start
   # or for a specific profile
   colima start <profile>
   ```

2. **Wrong context selected:**
   ```bash
   docker context use colima
   # or for named profile
   docker context use colima-<profile>
   ```

3. **App ignores Docker contexts:** Set DOCKER_HOST explicitly
   ```bash
   export DOCKER_HOST="unix://$(colima status -p <profile> --json | jq -r .docker_socket)"
   ```

## "Broken" Status After macOS Restart

**Symptom:** `colima list` shows "Broken" status

```bash
colima list
# PROFILE    STATUS     ARCH       CPUS    MEMORY    DISK
# default    Broken     aarch64    2       2GiB      60GiB
```

**Solution:**

```bash
colima stop --force
colima start
```

## VM Running Slow / Needs More Resources

**Diagnosis:**

```bash
# Check current allocation
colima list

# Check actual usage in VM
colima ssh -- htop
# or
colima ssh -- top
```

**Solution:**

```bash
colima stop
colima start --cpu 4 --memory 8
```

Or edit config for persistent change:
```bash
colima stop
colima start --edit  # Change cpu/memory values
```

## Container Getting OOM Killed

**Symptom:** Container exits unexpectedly, `docker logs` shows nothing useful

**Cause:** VM itself may be out of memory

**Solution:**

```bash
colima stop
colima start --memory 8  # or higher
```

## VM Disk Space Running Low

**Diagnosis:**

```bash
colima ssh -- df -h
```

**Solutions:**

1. **Clean Docker resources:**
   ```bash
   docker system prune -a --volumes
   ```

2. **Reclaim space in VM:**
   ```bash
   colima ssh -- sudo fstrim -a
   ```

3. **Increase disk size (requires stop):**
   ```bash
   colima stop
   colima start --edit  # Increase disk: value
   ```

Note: Disk size can only be increased, not decreased.

## Colima Can't Access Internet (DNS Issues)

**Symptom:** Builds fail to download packages, can't pull images

**Diagnosis:**

```bash
colima ssh -- ping -c4 google.com
```

**Solution:**

```bash
colima stop
colima start --dns 8.8.8.8 --dns 1.1.1.1
```

## Issues After Colima Upgrade

**Recommended approach:** Test with a fresh profile first

```bash
# Create a test profile
colima start debug

# If that works, the issue is your existing profile
colima delete <profile>
colima start <profile>
```

## Docker Build Fails - Can't Access Private Git Repos

**Symptom:** `git clone` in Dockerfile fails with authentication errors

**Cause:** SSH agent not forwarded to Colima VM

**Solution:**

```bash
colima stop
colima start -s
# or
colima start --ssh-agent
```

Then use `--ssh` flag in Docker build:
```bash
docker build --ssh default .
```
```

**Step 2: Verify file was created**

Run: `wc -l plugins/dev-tools/skills/working-with-colima/references/troubleshooting.md`
Expected: ~140-160 lines

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/references/troubleshooting.md
git commit -m "feat(dev-tools): add troubleshooting reference for colima skill"
```

---

## Task 6: Write Common Options Reference

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/references/common-options.md`

**Step 1: Write common-options.md**

```markdown
# Common Options

## Resource Flags

Used with `colima start`:

| Flag | Description | Example |
|------|-------------|---------|
| `--cpu` | Number of CPUs | `--cpu 4` |
| `--memory` | Memory in GB | `--memory 8` |
| `--disk` | Disk size in GB | `--disk 60` |

**Example:**
```bash
colima start work --cpu 4 --memory 8 --disk 60
```

**Note:** Changes require stopping first. Disk can only be increased.

## VM Type Flags (Apple Silicon)

| Flag | Description |
|------|-------------|
| `--vm-type=vz` | Apple Virtualization.framework (faster, recommended) |
| `--vz-rosetta` | Enable Rosetta for x86 emulation |

**Example (Apple Silicon with Rosetta):**
```bash
colima start --vm-type=vz --vz-rosetta
```

Requires macOS 13+ (Ventura) on Apple Silicon.

## SSH Agent Forwarding

| Flag | Description |
|------|-------------|
| `--ssh-agent` or `-s` | Forward SSH agent to VM |

**When needed:** Docker builds that clone private git repos.

```bash
colima start work -s
```

## Configuration Flags

| Flag | Description |
|------|-------------|
| `--edit` | Open config in editor before starting |
| `--dns` | Custom DNS server (can repeat) |
| `--runtime` | Container runtime: `docker`, `containerd`, `incus` |
| `--kubernetes` | Enable Kubernetes |

**Examples:**
```bash
# Edit config
colima start --edit

# Custom DNS
colima start --dns 8.8.8.8 --dns 1.1.1.1

# With Kubernetes
colima start --kubernetes
```

## Profile Flag

Most commands accept `-p <profile>` to target a specific profile:

```bash
colima status -p work
colima stop -p work
colima ssh -p work
colima delete -p work
```

## Default VM Specs

If not specified, Colima creates VMs with:
- 2 CPUs
- 2 GB memory
- 100 GB disk

## Config File Format

Located at `~/.colima/<profile>/colima.yaml`:

```yaml
cpu: 4
memory: 8
disk: 60
arch: host
runtime: docker
vmType: vz
rosetta: true
mountType: virtiofs
```

Edit with `colima start --edit` or `colima template` for defaults.
```

**Step 2: Verify file was created**

Run: `wc -l plugins/dev-tools/skills/working-with-colima/references/common-options.md`
Expected: ~90-100 lines

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/references/common-options.md
git commit -m "feat(dev-tools): add common options reference for colima skill"
```

---

## Task 7: Verify Complete Skill Structure

**Step 1: Check all files exist**

```bash
find plugins/dev-tools/skills/working-with-colima -type f -name "*.md"
```

Expected:
```
plugins/dev-tools/skills/working-with-colima/SKILL.md
plugins/dev-tools/skills/working-with-colima/references/docker-contexts.md
plugins/dev-tools/skills/working-with-colima/references/profile-management.md
plugins/dev-tools/skills/working-with-colima/references/troubleshooting.md
plugins/dev-tools/skills/working-with-colima/references/common-options.md
```

**Step 2: Verify SKILL.md is under 200 lines**

```bash
wc -l plugins/dev-tools/skills/working-with-colima/SKILL.md
```

Expected: Under 150 lines

**Step 3: Verify total skill size is reasonable**

```bash
wc -l plugins/dev-tools/skills/working-with-colima/**/*.md
```

Expected: ~500-600 total lines across all files

---

## Task 8: Test Skill with Subagent (RED phase)

**Purpose:** Verify the skill helps agents handle Colima scenarios correctly.

**Step 1: Run baseline test WITHOUT skill**

Dispatch subagent with prompt:
> "Docker commands are failing with 'Cannot connect to the Docker daemon'. The user is on macOS. How do you troubleshoot this?"

Document what the agent does/doesn't know about Colima.

**Step 2: Run test WITH skill loaded**

Dispatch subagent with the SKILL.md content prepended, same prompt.

**Step 3: Compare results**

- Does agent now mention Colima?
- Does agent know about `colima status`, `docker context`?
- Does agent reference the troubleshooting guide?

**Step 4: Document findings**

Note any gaps in the skill that need addressing.

---

## Task 9: Refine Skill Based on Testing

**Files:**
- Modify: Any files that need updates based on testing

**Step 1: Address any gaps found in testing**

Update skill content based on what agents got wrong or missed.

**Step 2: Re-test if significant changes**

Run another subagent test to verify improvements.

**Step 3: Commit refinements**

```bash
git add plugins/dev-tools/skills/working-with-colima/
git commit -m "refactor(dev-tools): refine colima skill based on testing"
```

---

## Task 10: Final Review and Push

**Step 1: Review complete skill**

```bash
cat plugins/dev-tools/skills/working-with-colima/SKILL.md
```

Verify:
- Frontmatter is valid (name, description under 1024 chars)
- Description starts with "Use when..."
- References are correctly linked
- Code examples are accurate

**Step 2: Validate plugin structure**

```bash
claude plugin validate plugins/dev-tools
```

**Step 3: Push to remote**

```bash
git push origin feature/working-with-colima
```

**Step 4: Create PR (optional)**

```bash
gh pr create --title "feat(dev-tools): add working-with-colima skill" \
  --body "Adds skill for working with Colima container runtime on macOS.

## Summary
- Progressive disclosure structure (SKILL.md + references/)
- Quick reference for common commands
- Docker context integration guidance
- Troubleshooting for common issues
- Profile management documentation

## Test plan
- [ ] Verify skill activates on Docker daemon connection errors
- [ ] Verify references load correctly
- [ ] Test with real Colima scenarios"
```

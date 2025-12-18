# Working with Colima Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a skill that helps Claude assist users with Colima (Docker runtime for macOS) - lifecycle management, profile handling, Docker context integration, and troubleshooting.

**Architecture:** Single SKILL.md file in `plugins/dev-tools/skills/working-with-colima/` following the existing skill patterns in this plugin. Include reference docs fetched via gitingest if needed.

**Tech Stack:** Markdown skill file, Colima CLI, Docker CLI

---

## Task 1: Create Skill Directory Structure

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Create the skill directory**

```bash
mkdir -p plugins/dev-tools/skills/working-with-colima
```

**Step 2: Verify directory exists**

Run: `ls -la plugins/dev-tools/skills/working-with-colima`
Expected: Empty directory listed

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima
git commit -m "chore(dev-tools): create working-with-colima skill directory"
```

---

## Task 2: Write SKILL.md with Frontmatter and Overview

**Files:**
- Create: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Write initial SKILL.md with frontmatter and overview**

```markdown
---
name: working-with-colima
description: Use when Docker commands fail with "Cannot connect to Docker daemon", when starting/stopping container environments, or when managing multiple Docker contexts on macOS - provides Colima lifecycle management, profile handling, and troubleshooting
---

# Working with Colima

## Overview

Colima provides container runtimes (Docker, Containerd) on macOS with minimal setup. It runs a Linux VM and exposes Docker via contexts. Use this skill when:

- Docker commands fail ("Cannot connect to Docker daemon")
- Starting/stopping container runtime on macOS
- Managing multiple Docker profiles/contexts
- Troubleshooting container environment issues
- Need SSH agent forwarding for Docker builds

## When NOT to Use

- Docker Compose or container orchestration (that's Docker knowledge)
- Kubernetes cluster management (separate concern)
- Linux environments (Colima is macOS-specific)
```

**Step 2: Verify file was created**

Run: `head -20 plugins/dev-tools/skills/working-with-colima/SKILL.md`
Expected: Shows frontmatter and overview section

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
git commit -m "feat(dev-tools): add working-with-colima skill frontmatter and overview"
```

---

## Task 3: Add Quick Reference Section

**Files:**
- Modify: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Append quick reference table**

Add after the "When NOT to Use" section:

```markdown

## Quick Reference

| Operation | Command | Notes |
|-----------|---------|-------|
| Start default | `colima start` | Creates `default` profile |
| Start named profile | `colima start <profile>` | e.g., `colima start work` |
| Start with SSH agent | `colima start <profile> -s` | Required for Docker builds needing git |
| Start with edit | `colima start --edit` | Opens config in editor |
| Stop | `colima stop` | Graceful stop |
| Force stop | `colima stop --force` | Use for "Broken" status |
| Status | `colima status` | Shows running state, socket path |
| Status (profile) | `colima status -p <profile>` | Status for specific profile |
| List profiles | `colima list` | Shows all profiles and status |
| Delete profile | `colima delete <profile>` | Removes profile |
| SSH into VM | `colima ssh` | Access underlying VM |
| Run command in VM | `colima ssh -- <cmd>` | e.g., `colima ssh -- df -h` |
| Edit default template | `colima template` | Affects new profiles |
```

**Step 2: Verify section was added**

Run: `grep -A 20 "## Quick Reference" plugins/dev-tools/skills/working-with-colima/SKILL.md`
Expected: Shows quick reference table

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
git commit -m "feat(dev-tools): add quick reference table to colima skill"
```

---

## Task 4: Add Docker Context Integration Section

**Files:**
- Modify: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Append Docker context section**

Add after Quick Reference:

```markdown

## Docker Context Integration

Colima creates Docker contexts for each profile:
- Profile `default` → context `colima`
- Profile `work` → context `colima-work`

**Context switching is global** (stored in `~/.docker/config.json`):

```bash
# Switch globally (affects all terminals)
docker context use colima-work

# List available contexts
docker context list
```

**Override per-session or per-command:**

```bash
# Per-session
export DOCKER_CONTEXT=colima-work

# Per-command
docker --context colima-work ps
```

**Get socket path for apps that ignore contexts:**

```bash
# View socket path
colima status -p <profile>

# Get socket path programmatically
colima status -p <profile> --json | jq -r .docker_socket

# Set DOCKER_HOST for non-context-aware apps
export DOCKER_HOST="unix://$(colima status -p work --json | jq -r .docker_socket)"
```
```

**Step 2: Verify section was added**

Run: `grep -A 5 "## Docker Context" plugins/dev-tools/skills/working-with-colima/SKILL.md`
Expected: Shows Docker context section header and content

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
git commit -m "feat(dev-tools): add Docker context integration to colima skill"
```

---

## Task 5: Add Profile Management Section

**Files:**
- Modify: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Append profile management section**

Add after Docker Context Integration:

```markdown

## Profile Management

**Create profiles:**

```bash
# Default profile
colima start

# Named profile with resources
colima start work --cpu 4 --memory 8 --disk 60
```

**Profile configuration locations:**
- Config: `~/.colima/<profile>/colima.yaml`
- Default template: `~/.colima/_templates/default.yaml`
- Edit template: `colima template`

**Delete profiles:**

```bash
colima delete <profile>

# Delete including container data (v0.9.0+)
colima delete <profile> --data
```
```

**Step 2: Verify section was added**

Run: `grep -A 5 "## Profile Management" plugins/dev-tools/skills/working-with-colima/SKILL.md`
Expected: Shows profile management section

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
git commit -m "feat(dev-tools): add profile management to colima skill"
```

---

## Task 6: Add Troubleshooting Section

**Files:**
- Modify: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Append troubleshooting section**

Add after Profile Management:

```markdown

## Troubleshooting

### "Cannot connect to Docker daemon"

1. Check if Colima is running: `colima status` (or `colima status -p <profile>`)
2. If not running: `colima start` (or `colima start <profile>`)
3. If running but wrong context: `docker context use colima-<profile>`
4. For apps ignoring contexts:
   ```bash
   export DOCKER_HOST="unix://$(colima status -p <profile> --json | jq -r .docker_socket)"
   ```

### "Broken" status after macOS restart

```bash
colima list          # Shows "Broken" status
colima stop --force  # Changes to "Stopped"
colima start         # Should work now
```

### VM running slow / needs more resources

```bash
# Check current allocation
colima list

# Check usage in VM
colima ssh -- htop

# Increase resources (requires stop)
colima stop
colima start --cpu 4 --memory 8
```

### Container getting OOM killed

The VM itself may be out of memory. Increase VM memory:

```bash
colima stop && colima start --memory 8
```

### VM disk space running low

```bash
# Check disk usage in VM
colima ssh -- df -h

# Clean up Docker resources
docker system prune -a --volumes

# Reclaim space (fstrim releases unused blocks)
colima ssh -- sudo fstrim -a

# Increase disk size if needed (requires stop)
colima stop
colima start --edit  # Increase disk: value
```

Note: Disk size can only be increased, not decreased.

### Colima can't access internet (DNS issues)

```bash
colima start --dns 8.8.8.8 --dns 1.1.1.1

# Verify connectivity
colima ssh -- ping -c4 google.com
```

### Issues after Colima upgrade

```bash
# Test with fresh profile first
colima start debug

# If that works, reset your profile
colima delete <profile>
colima start <profile>
```
```

**Step 2: Verify section was added**

Run: `grep -c "###" plugins/dev-tools/skills/working-with-colima/SKILL.md`
Expected: Shows count of subsections (should be 7)

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
git commit -m "feat(dev-tools): add troubleshooting section to colima skill"
```

---

## Task 7: Add Common Options Section

**Files:**
- Modify: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Append common options section**

Add after Troubleshooting:

```markdown

## Common Options

**Resource flags (for `colima start`):**

| Flag | Description | Example |
|------|-------------|---------|
| `--cpu` | Number of CPUs | `--cpu 4` |
| `--memory` | Memory in GB | `--memory 8` |
| `--disk` | Disk size in GB | `--disk 60` |

**VM type flags (Apple Silicon):**

| Flag | Description |
|------|-------------|
| `--vm-type=vz` | Use Apple Virtualization.framework (faster) |
| `--vz-rosetta` | Enable Rosetta for x86 emulation (macOS 13+) |

**Other useful flags:**

| Flag | Description |
|------|-------------|
| `--ssh-agent` / `-s` | Forward SSH agent (for git in Docker builds) |
| `--edit` | Open config in editor before starting |
| `--dns` | Custom DNS server(s), can repeat |
| `--kubernetes` | Enable Kubernetes |

**Profile flag:** Most commands accept `-p <profile>`:

```bash
colima status -p work
colima stop -p work
colima ssh -p work
```

## References

For updated Colima documentation, fetch from upstream:

```bash
uvx gitingest https://github.com/abiosoft/colima -i "*.md" -o colima-docs.txt
```

See also: [Colima FAQ](https://github.com/abiosoft/colima/blob/main/docs/FAQ.md)
```

**Step 2: Verify complete skill file**

Run: `wc -l plugins/dev-tools/skills/working-with-colima/SKILL.md`
Expected: Approximately 180-220 lines

**Step 3: Commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
git commit -m "feat(dev-tools): add common options and references to colima skill"
```

---

## Task 8: Test Skill with Subagent (RED phase)

**Purpose:** Verify the skill helps agents handle Colima scenarios correctly.

**Step 1: Run baseline test WITHOUT skill**

Dispatch subagent with prompt:
> "Docker commands are failing with 'Cannot connect to the Docker daemon'. The user is on macOS. How do you troubleshoot this?"

Document what the agent does/doesn't know about Colima.

**Step 2: Run test WITH skill loaded**

Dispatch subagent with the skill content prepended, same prompt.

**Step 3: Compare results**

- Does agent now mention Colima?
- Does agent know about `colima status`, `docker context`?
- Does agent know about `--ssh-agent` for builds?

**Step 4: Document findings**

Note any gaps in the skill that need addressing.

---

## Task 9: Refine Skill Based on Testing

**Files:**
- Modify: `plugins/dev-tools/skills/working-with-colima/SKILL.md`

**Step 1: Address any gaps found in testing**

Update skill content based on what agents got wrong or missed.

**Step 2: Re-test if significant changes**

Run another subagent test to verify improvements.

**Step 3: Final commit**

```bash
git add plugins/dev-tools/skills/working-with-colima/SKILL.md
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
- All sections present and formatted correctly
- Code examples are correct

**Step 2: Validate plugin structure**

```bash
claude plugin validate plugins/dev-tools
```

**Step 3: Push to remote**

```bash
git push origin main
```

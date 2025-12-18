# Skill Test Cases

Test cases used for RED/GREEN testing during skill development.

## Test 1: Docker Daemon Connection Error

**Prompt:**
> "Docker commands are failing with 'Cannot connect to the Docker daemon'. The user is on macOS. How do you troubleshoot this?"

### RED (Without Skill)

Agent response focused on:
- Docker Desktop (check menu bar icon, restart Docker.app)
- `/var/run/docker.sock` socket path (incorrect for Colima)
- `dockerd` process checks
- Permission issues with docker group
- Docker Desktop settings/troubleshoot menu
- Mentioned Colima only briefly at the end as an "alternative"

**Gaps identified:**
- No knowledge of `colima status` as first diagnostic
- No mention of Docker contexts
- Wrong socket path for Colima users
- Docker Desktop-centric approach

### GREEN (With Skill)

Agent response correctly:
- Used `colima status` as first diagnostic step
- Checked Docker context with `docker context list`
- Knew to switch context with `docker context use colima`
- Used correct socket path approach: `colima status -p <profile> --json | jq -r .docker_socket`
- Knew about `colima stop --force` for "broken" status
- No mention of Docker Desktop

**Improvement confirmed:** Skill dramatically improves Colima-specific troubleshooting.

## Test 2: (Future) Profile Management

**Prompt:**
> "I need to run two different Docker environments - one for work projects and one for personal. How do I set this up with Colima?"

**Expected behavior with skill:**
- Explain named profiles (`colima start work`, `colima start personal`)
- Show how contexts map (`colima-work`, `colima-personal`)
- Demonstrate switching between them
- Mention resource customization per profile

## Test 3: (Future) SSH Agent Forwarding

**Prompt:**
> "My Docker build is failing to clone a private git repo. I'm on macOS using Colima."

**Expected behavior with skill:**
- Identify SSH agent forwarding as the issue
- Show `colima start -s` or `--ssh-agent` flag
- Mention `docker build --ssh default .` for builds

## Test 4: (Future) Resource Issues

**Prompt:**
> "Docker containers keep getting killed unexpectedly. I'm using Colima on my Mac."

**Expected behavior with skill:**
- Check VM resources with `colima list`
- Diagnose OOM with `colima ssh -- htop`
- Show how to increase memory: `colima stop && colima start --memory 8`

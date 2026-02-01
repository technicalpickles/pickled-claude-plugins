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

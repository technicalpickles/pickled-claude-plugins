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

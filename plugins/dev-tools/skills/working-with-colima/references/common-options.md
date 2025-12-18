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

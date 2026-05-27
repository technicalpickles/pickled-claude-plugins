# Incus Runtime

Colima supports running [Incus](https://linuxcontainers.org/incus/) as a runtime, in addition to Docker and containerd. Incus is a system container and VM manager (the LXD fork). Unlike Docker/containerd, it can run full Linux **virtual machines** with their own kernel, useful when you need stronger isolation than a shared-kernel container provides.

## When to use this

- You want VM-grade isolation for some workload on macOS (e.g. agent sandboxes, untrusted code)
- You want to spin up cheap throwaway Linux machines (system containers or VMs)
- You explicitly need an incus-compatible target on macOS for local dev

If you just need Docker, stay on the default runtime.

## Hardware requirements for VMs

Running incus **VMs** (not containers) requires nested virtualization.

| Apple Silicon | Nested virt in vz | Incus VMs work? |
|---------------|-------------------|-----------------|
| M1 / M2       | No                | No (containers only) |
| M3 or newer (M3, M4, etc.) | Yes (macOS 15+) | Yes |
| Intel         | n/a               | Likely yes via qemu, not tested here |

Containers work on any chip. Only the `--vm` flag needs nested virt.

## Setup

```bash
brew install incus      # client (server runs inside the colima VM)

colima start incus \
  --runtime incus \
  --vm-type vz \
  --nested-virtualization \
  --network-address \
  --cpu 4 \
  --memory 12 \
  --disk 40
```

Flag notes:
- `--runtime incus`: selects the runtime instead of docker/containerd
- `--vm-type vz`: required for nested virt (qemu backend can't do it)
- `--nested-virtualization` (or `-z`): must be set explicitly; not implied by vz
- `--network-address`: gives the colima VM a reachable IP. Needs sudo for sudoers setup on first run. In a non-interactive shell the prompt is swallowed and a warning is logged, but the address still gets assigned. Re-run from an actual terminal if routing breaks.

## How the host CLI talks to the server

Colima forwards the incus server's Unix socket out of the VM:

```
/var/lib/incus/unix.socket (guest)  →  ~/.colima/incus/incus.sock (host)
```

The brew-installed `incus` client picks this up automatically and registers a remote called `colima-incus`:

```bash
incus remote list
# colima-incus (current) | unix:///Users/<you>/.colima/incus/incus.sock | incus | tls
```

So plain `incus list`, `incus launch ...` etc. from the macOS terminal Just Work. Client/server version skew is normal and expected: the linuxcontainers project releases them independently. Don't try to "fix" it.

## Containers vs VMs

Same CLI, one flag difference:

```bash
incus launch images:ubuntu/24.04 mycontainer          # system container (shared kernel)
incus launch images:ubuntu/24.04 myvm --vm            # virtual machine (own kernel)
```

VMs cost more (boot time, memory, disk) but give kernel isolation. Containers start in seconds. Reach for containers first unless you specifically need VM-grade boundaries.

## Network reachability

Three layers to keep straight:

| Reach | How |
|-------|-----|
| Host (macOS) → colima VM | `192.168.64.x` via lima's vmnet bridge (when `--network-address` is on) |
| Colima VM → inner incus instances | `192.168.100.0/24` (incusbr0, NAT'd outbound) |
| Host → inner incus instances | Not direct |

To reach an inner instance from macOS:

1. **`incus exec`** (analog of `docker exec`): `incus exec myvm -- bash`
2. **`incus shell`**: interactive shell
3. **Proxy device** for specific ports:
   ```bash
   incus config device add myvm web proxy \
     listen=tcp:0.0.0.0:8080 \
     connect=tcp:127.0.0.1:80
   ```

## Sandbox gotcha (Claude Code)

`incus launch`, `incus copy`, `incus publish` write image blobs to `~/.cache/incus/`, which is not on the default Bash sandbox `allowWrite` list. First run fails with:

```
Error: mkdir /Users/<you>/.cache/incus/<sha>: operation not permitted
```

Workaround: run the `incus` command with `dangerouslyDisableSandbox: true`. Per-path allowlisting isn't worth the whack-a-mole: the client touches sockets, image registries, and ssh-exec into the colima VM as well.

## Verifying nested virt actually works

```bash
incus launch images:ubuntu/24.04 testvm --vm
sleep 30                                # let the in-guest agent come up
incus exec testvm -- uname -a
# Linux testvm 6.8.0-xxx-generic ... aarch64
incus delete testvm --force
```

If `incus launch ... --vm` fails with KVM-related errors, `--nested-virtualization` wasn't set or the chip is M1/M2.

## Teardown

```bash
colima stop incus
colima delete incus --data    # also wipes inner VMs and image cache in the colima VM
```

The `--data` flag is colima 0.9+; on older versions the inner data persists across delete and you have to clean up `~/.colima/_lima/_disks/colima-incus/` by hand.

## Resource sizing reality check

Lima disks are sparse (qcow2), so `--disk 40` is a cap not a floor. But once you launch inner VMs, real bytes get committed. On a constrained host (e.g. <100GB free) be conservative: the colima VM disk grows as inner VMs grow, and it doesn't shrink back automatically when you delete them. `incus image flush` and `incus rm <vm>` help, but the host-visible qcow2 file stays large.

## References

- [Colima runtimes docs](https://colima.run/docs/runtimes/)
- [linuxcontainers forum: Easy way to try Incus on macOS with Colima](https://discuss.linuxcontainers.org/t/easy-way-to-try-incus-on-macos-with-colima/21153)
- [Incus documentation](https://linuxcontainers.org/incus/docs/main/)

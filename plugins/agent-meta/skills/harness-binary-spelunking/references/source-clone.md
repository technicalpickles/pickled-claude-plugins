# Source-clone path: version to git tag to reading source

codex, opencode, and pi are all open source. When the installed version has a corresponding git tag, cloning the source and reading it directly beats spelunking a binary: no minified names, no fragment reassembly, no guessing at a Rust struct's field order.

## Find the tag scheme, don't assume it

Every one of these tools uses a **different tag scheme** for the same-looking version string. Don't guess; derive it with `git ls-remote --tags` before cloning:

```bash
V=$(codex --version | awk '{print $NF}')                             # e.g. 0.139.0
git ls-remote --tags https://github.com/openai/codex.git | grep "$V"  # confirms the exact tag string
```

Confirmed mappings from this recon:

| Tool | Installed version | Repo | Tag |
|------|-------------------|------|-----|
| codex | `0.139.0` (`codex --version`) | github.com/openai/codex | `rust-v0.139.0` |
| opencode | `1.17.5` (`opencode --version`) | github.com/sst/opencode | `v1.17.5` |
| pi | `0.67.6` (`pi --version`) | github.com/badlogic/pi-mono (monorepo, `packages/coding-agent`) | `v0.67.6` |

Note codex prefixes with `rust-v`, not bare `v`; opencode and pi use bare `v`. This is exactly the kind of detail `git ls-remote --tags | grep` catches and blind-guessing doesn't.

## Clone recipe

```bash
V=$(codex --version | awk '{print $NF}')
git ls-remote --tags https://github.com/openai/codex.git | grep "$V"
git clone --depth 1 --branch rust-v$V https://github.com/openai/codex.git /tmp/codex-src
```

Swap the repo URL and tag prefix per the table above. `--depth 1` is enough; you're reading one version's source, not the history.

For a monorepo (pi), clone the whole thing and locate the relevant package rather than assuming a matching subdirectory tag exists:

```bash
V=$(pi --version)
git clone --depth 1 --branch v$V https://github.com/badlogic/pi-mono.git /tmp/pi-src
ls /tmp/pi-src/packages/coding-agent
```

## pi is the boundary case: source this readable means "just read it"

pi's shipped `dist/cli.js` is a thin, readable entry point; the actual coding-agent logic is TypeScript source living in the monorepo, not a minified bundle worth spelunking. There is almost nothing to reverse-engineer: no fragment reassembly, no anchor-hunting, no build-classification step. You clone, `cd packages/coding-agent`, and read the TypeScript like any other open-source project.

This is the far end of the Step 0 decision in the main SKILL.md: when the source is this available and this readable, spelunking the binary is strictly more work for the same or worse answer. Reach for the clone first, every time, for tools built this way. Only fall back to binary spelunking if you specifically need to verify what's *actually installed* on a machine (e.g. confirming a patched build matches source, or the version isn't tagged yet).

## When to still spelunk the binary despite source being available

- The installed version has no matching tag yet (a nightly, a pre-release, a locally patched build).
- You suspect the shipped binary diverges from what the tagged source claims to build.
- You need to confirm the exact build that's running on a specific machine right now, not what the source repo says it should be.

In all of these, drop to [bun-js.md](bun-js.md) or [rust.md](rust.md) depending on the build classification from the main SKILL.md's "Identify the build" step.

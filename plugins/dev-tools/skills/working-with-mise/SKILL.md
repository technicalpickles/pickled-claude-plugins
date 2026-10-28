---
name: working-with-mise
description: Use when adding, configuring, or troubleshooting mise-managed tools - ensures proper CLI usage, detects existing config files, and diagnoses PATH/activation issues when commands aren't found
---

# Working with mise

## Overview

mise is a polyglot tool version manager. Use this skill when:
- Adding tools to a project via mise
- Troubleshooting "command not found" when mise should have tools available
- Deciding whether mise is the right choice for a dependency

## The Iron Rules

1. **Use `mise use` to add tools** - never manually edit config files
2. **Detect existing config files first** - don't create new ones when one exists
3. **Fix the shell, don't workaround** - if tools aren't on PATH, diagnose the activation issue rather than using `mise exec` as a permanent workaround

## When to Use mise vs Alternatives

### Use mise when version matters per-project

Tools where different projects need different versions:
- Language runtimes: node, python, ruby, go, rust
- Infrastructure tools: terraform, kubectl, helm
- Tools with breaking changes between versions

```bash
# Good mise candidates - version sensitivity
mise use node@20      # Projects may need different Node versions
mise use terraform@1.5  # IaC often pins specific versions
mise use ruby@3.2     # Gemfiles often require specific Ruby
```

### Use Homebrew/system when version rarely matters

Stable CLIs with consistent interfaces across versions:
- jq, yq - query languages are stable
- gh, hub - GitHub CLI
- ripgrep, fd - search tools
- tree, htop - system utilities

```bash
# Better as Homebrew - version doesn't matter
brew install jq gh ripgrep
```

### Decision checklist

Ask yourself:
1. Does this project's README/docs specify a version? → mise
2. Could different team members need different versions? → mise
3. Does the tool have breaking changes between versions? → mise
4. Is it a stable CLI you use the same way everywhere? → Homebrew

## Adding Tools with mise

### 1. Check for existing config files first

Before adding tools, detect what config format the project uses:

```bash
# Check for existing mise config
ls -la mise.toml .mise.toml mise.local.toml .mise.local.toml .tool-versions 2>/dev/null
```

Config file precedence (mise uses the first it finds):
- `mise.toml` or `.mise.toml` - standard mise config
- `mise.local.toml` or `.mise.local.toml` - local overrides (usually gitignored)
- `.tool-versions` - legacy asdf format

**If a config file exists, use that format.** Don't create a new one.

### 2. Use `mise use` to add tools

**Always use the CLI** - it validates the tool exists and works:

```bash
# Add to project config (mise.toml or existing format)
mise use node@20

# Add to global config (~/.config/mise/config.toml)
mise use -g python@3.12

# Dry run to see what would happen
mise use --dry-run terraform@1.5
```

**Never manually edit config files** - `mise use` ensures:
- The tool/version exists in the registry
- The tool installs correctly
- The config syntax is valid

### 3. Verify the tool is available

```bash
# Check mise sees the tool
mise ls

# Check the tool is on PATH
which node
node --version

# Compare with mise's view
mise which node
```

## Conventions: Pins, Runtimes, and Local Overrides

Defaults to follow unless the repo you're in says otherwise. Rationale and history: [dotfiles ADR 0067](https://github.com/technicalpickles/dotfiles/blob/main/doc/adr/0067-pin-global-mise-tools-and-leave-runtimes-to-projects.md).

### Pin exact versions

Prefer `mise use --pin tool@x.y.z`, which saves the resolved concrete version. `"latest"` and fuzzy versions can't be bumped by Renovate (nothing to compare against), and two machines can end up on different builds. If a pin is deliberate, say so in a comment beside it.

### Renovate and mise

- Renovate's mise manager reads `mise.toml`, `.mise.toml` and `.config/mise/` by default. Config kept elsewhere (a dotfiles `config/mise/`, say) needs `managerFilePatterns` on the `mise` manager.
- It understands `github:` and `npm:` backends and core tools like `bun` and `go`. It skips `"latest"`, `lts` and `stable`.
- mise strips the `v` from `github:` tags but Renovate writes the raw tag back. The `github>technicalpickles/renovate-config:mise` preset handles this. A hand-written rule needs `"extractVersion": "^v?(?<version>.+)$"` scoped with `"matchDepNames": ["github:**"]`; unscoped, it drops updates for core tools like `go` (see `dev-tools:adopting-renovate`).

### Runtimes belong to the project

`go`, `python`, `rust` and `ruby` go in the project's own `mise.toml`, not the global config. Global config is for tools you run everywhere (CLIs, `node` for `npm:` tools).

### Local overrides for clones without mise config

When you've cloned something with no mise config of its own, create `mise.local.toml` with the versions it needs (read them from `go.mod`, CI or `.ruby-version`), and keep it out of git:

```bash
# Per clone. In a bare-repo + worktrees layout the exclude lives in the common dir
echo mise.local.toml >> "$(git rev-parse --git-common-dir)/info/exclude"
```

Or ignore `mise.local.toml` and `.mise.local.toml` in the global gitignore once, and skip the per-clone step.

### Don't read go.mod as a version source

`idiomatic_version_file_enable_tools = ["go"]` makes mise read the `go` directive in `go.mod`, but that is only a minimum version and mise removes the support in 2026.11.0. A `toolchain goX.Y.Z` line, `.go-version` or `mise.toml` still work.

### npm: backend still needs node to run

The `npm:` backend installs without node, but the installed bin shims run whichever `node` is first on `PATH`. Keep a node on `PATH` wherever an `npm:` tool is used.

## Troubleshooting "Command Not Found"

When a tool should be available but isn't found:

### Diagnostic workflow

```bash
# 1. Check mise installation health
mise doctor

# 2. Check what tools mise knows about
mise ls                    # All installed tools
mise ls --current          # Tools for current directory

# 3. Compare which vs mise which
which node                 # What shell finds
mise which node            # What mise thinks it should be

# 4. Check if tool would work via mise exec
mise exec -- node --version  # If this works, it's an activation issue
```

### Common causes and fixes

#### Shell activation not set up

**Symptom**: `mise exec -- node` works, but `node` doesn't

**Diagnose**:
```bash
mise doctor  # Look for activation warnings
```

**Fix** - add to shell rc file:

```bash
# For zsh (~/.zshrc)
eval "$(mise activate zsh)"

# For bash (~/.bashrc)
eval "$(mise activate bash)"

# For fish (~/.config/fish/config.fish)
mise activate fish | source
```

Then restart your shell or `source` the rc file.

#### Config file not trusted

**Symptom**: mise shows trust warning, tools not activated

**Fix**:
```bash
mise trust
```

#### Tool not installed for current directory

**Symptom**: `mise ls` shows tool globally but not in `mise ls --current`

**Diagnose**:
```bash
# Check what config file applies
mise config

# Check if there's a local config overriding global
cat mise.toml .mise.toml .tool-versions 2>/dev/null
```

**Fix**: Add the tool to the project config:
```bash
mise use node@20  # Adds to project config
```

#### Shims vs PATH activation confusion

**Symptom**: Tools work in terminal but not in IDE/scripts

See [references/dev-tools/shims-html.md](references/dev-tools/shims-html.md) for detailed explanation.

**Quick fix** for non-interactive contexts:
```bash
# In ~/.zprofile or ~/.bash_profile (non-interactive)
eval "$(mise activate zsh --shims)"

# In ~/.zshrc or ~/.bashrc (interactive)
eval "$(mise activate zsh)"
```

### When to use `mise exec` (legitimately)

`mise exec` is appropriate for:
- One-off commands with specific versions: `mise exec node@18 -- npm test`
- CI/CD scripts where activation isn't available
- Testing a different version temporarily

`mise exec` is NOT a fix for:
- Tools not being on PATH in your terminal (fix activation instead)
- "It works with mise exec" as a permanent solution

## Available References

- [references/cli/use-html.md](references/cli/use-html.md) - Full `mise use` documentation
- [references/cli/doctor-html.md](references/cli/doctor-html.md) - Diagnostic commands
- [references/cli/activate-html.md](references/cli/activate-html.md) - Shell activation
- [references/cli/which-html.md](references/cli/which-html.md) - Path resolution
- [references/dev-tools/shims-html.md](references/dev-tools/shims-html.md) - Shims vs PATH activation
- [references/guides/getting-started.md](references/guides/getting-started.md) - Setup guide

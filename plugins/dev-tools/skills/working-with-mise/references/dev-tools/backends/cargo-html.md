---
title: "Cargo Backend | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# Cargo Backend [​](#cargo-backend)

You may install packages directly from [Cargo Crates](https://crates.io/) even if there isn't an asdf plugin for it.

The code for this is inside the mise repository at [`./src/backend/cargo.rs`](https://github.com/jdx/mise/blob/main/src/backend/cargo.rs).

## Dependencies [​](#dependencies)

This relies on having `cargo` installed. You can either install it on your system via [rustup](https://rustup.rs/):

sh

```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Or you can install it via mise:

sh

```
mise use -g rust
```

## Usage [​](#usage)

The following installs the latest version of [eza](https://crates.io/crates/eza) and sets it as the active version on PATH:

sh

```
$ mise use -g cargo:eza
$ eza --version
eza - A modern, maintained replacement for ls
v0.17.1 [+git]
https://github.com/eza-community/eza
```

The version will be set in `~/.config/mise/config.toml` with the following format:

toml

```
[tools]
"cargo:eza" = "latest"
```

### Using Git [​](#using-git)

You can install any package from a Git repository using the `mise` command. This allows you to install a particular tag, branch, or commit revision:

sh

```
# Install a specific tag
mise use cargo:https://github.com/username/demo@tag:<release_tag>

# Install the latest from a branch
mise use cargo:https://github.com/username/demo@branch:<branch_name>

# Install a specific commit revision
mise use cargo:https://github.com/username/demo@rev:<commit_hash>
```

This will execute a `cargo install` command with the corresponding Git options.

## Settings [​](#settings)

Set these with `mise settings set [VARIABLE] [VALUE]` or by setting the environment variable listed.

### `cargo.binstall`[](#cargo.binstall)

- Type: `Bool`
- Env: `MISE_CARGO_BINSTALL`
- Default: `true`

If true, mise will use `cargo binstall` instead of `cargo install` if [`cargo-binstall`](https://crates.io/crates/cargo-binstall) is installed and on PATH. This makes installing CLIs with cargo _much_ faster by downloading precompiled binaries.

You can install it with mise:```sh
mise use -g cargo-binstall
```

### `cargo.registry_name`[](#cargo.registry_name)

- Type: `string`(optional)
- Env: `MISE_CARGO_REGISTRY_NAME`
- Default: `None`

Packages are installed from the official cargo registry.

You can set this to a different registry name if you have a custom feed or want to use a different source.

Please follow the [cargo alternative registries documentation](https://doc.rust-lang.org/cargo/reference/registries.html#using-an-alternate-registry) to configure your registry.

## Tool Options [​](#tool-options)

The following [tool-options](https://mise.jdx.dev/dev-tools/#tool-options) are available for the `cargo` backend—these go in `[tools]` in `mise.toml`.

### `features` [​](#features)

Install additional components (passed as `cargo install --features`):

toml

```
[tools]
"cargo:cargo-edit" = { version = "latest", features = "add" }
```

### `default-features` [​](#default-features)

Disable default features (passed as `cargo install --no-default-features`):

toml

```
[tools]
"cargo:cargo-edit" = { version = "latest", default-features = false }
```

### `bin` [​](#bin)

Select the CLI bin name to install when multiple are available (passed as `cargo install --bin`):

toml

```
[tools]
"cargo:https://github.com/username/demo" = { version = "tag:v1.0.0", bin = "demo" }
```

### `crate` [​](#crate)

Select the crate name to install when multiple are available (passed as `cargo install --git=<repo> <crate>`):

toml

```
[tools]
"cargo:https://github.com/username/demo" = { version = "tag:v1.0.0", crate = "demo" }
```

### `locked` [​](#locked)

Use Cargo.lock (passes `cargo install --locked`) when building CLI. This is the default behavior, pass `false` to disable:

toml

```
[tools]
"cargo:https://github.com/username/demo" = { version = "latest", locked = false }
```
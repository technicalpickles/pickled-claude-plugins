---
title: "npm Backend | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# npm Backend [​](#npm-backend)

You may install packages directly from [npmjs.org](https://npmjs.org/) even if there isn't an asdf plugin for it.

The code for this is inside of the mise repository at [`./src/backend/npm.rs`](https://github.com/jdx/mise/blob/main/src/backend/npm.rs).

## Dependencies [​](#dependencies)

This relies on having `npm` installed for resolving package versions. If you use `bun` or `pnpm` as the package manager, they must also be installed.

Here is how to install `npm` with mise:

sh

```
mise use -g node
```

To install `bun` or `pnpm`:

sh

```
mise use -g bun
# or
mise use -g pnpm
```

## Usage [​](#usage)

The following installs the latest version of [prettier](https://www.npmjs.com/package/prettier) and sets it as the active version on PATH:

sh

```
$ mise use -g npm:prettier
$ prettier --version
3.1.0
```

The version will be set in `~/.config/mise/config.toml` with the following format:

toml

```
[tools]
"npm:prettier" = "latest"
```

## Settings [​](#settings)

Set these with `mise settings set [VARIABLE] [VALUE]` or by setting the environment variable listed.

### `npm.bun`[](#npm.bun)deprecated

- Type: `Bool`
- Env: `MISE_NPM_BUN`
- Default: `false`
- Deprecated: Use npm.package_manager instead.

If true, mise will use `bun` instead of `npm` if [`bun`](https://bun.sh/) is installed and on PATH. This makes installing CLIs faster by using `bun` as the package manager.

You can install it with mise:```sh
mise use -g bun
```

### `npm.package_manager`[](#npm.package_manager)

- Type: `string`
- Env: `MISE_NPM_PACKAGE_MANAGER`
- Default: `npm`

Package manager to use for installing npm packages. Can be one of:- `npm` (default) - `bun`- `pnpm`
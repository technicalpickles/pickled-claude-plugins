---
title: "mise unset | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise unset` [​](#mise-unset)

- **Usage**: `mise unset [-f --file <FILE>] [-g --global] [ENV_KEY]…`
- **Source code**: [`src/cli/unset.rs`](https://github.com/jdx/mise/blob/main/src/cli/unset.rs)

Remove environment variable(s) from the config file.

By default, this command modifies `mise.toml` in the current directory.

## Arguments [​](#arguments)

### `[ENV_KEY]…` [​](#env-key)

Environment variable(s) to remove e.g.: NODE_ENV

## Flags [​](#flags)

### `-f --file <FILE>` [​](#f-file-file)

Specify a file to use instead of `mise.toml`

### `-g --global` [​](#g-global)

Use the global config file

Examples:

```
# Remove NODE_ENV from the current directory's config
$ mise unset NODE_ENV

# Remove NODE_ENV from the global config
$ mise unset NODE_ENV -g
```
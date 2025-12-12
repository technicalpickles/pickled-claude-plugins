---
title: "mise settings | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise settings` [​](#mise-settings)

- **Usage**: `mise settings [FLAGS] [SETTING] [VALUE] <SUBCOMMAND>`
- **Source code**: [`src/cli/settings/mod.rs`](https://github.com/jdx/mise/blob/main/src/cli/settings/mod.rs)

Show current settings

This is the contents of ~/.config/mise/config.toml

Note that aliases are also stored in this file but managed separately with `mise aliases`

## Arguments [​](#arguments)

### `[SETTING]` [​](#setting)

Name of setting

### `[VALUE]` [​](#value)

Setting value to set

## Global Flags [​](#global-flags)

### `-l --local` [​](#l-local)

Use the local config file instead of the global one

## Flags [​](#flags)

### `-a --all` [​](#a-all)

List all settings

### `-J --json` [​](#j-json)

Output in JSON format

### `-T --toml` [​](#t-toml)

Output in TOML format

### `--json-extended` [​](#json-extended)

Output in JSON format with sources

## Subcommands [​](#subcommands)

- [`mise settings add \[-l --local\] <SETTING> <VALUE>`](https://mise.jdx.dev/cli/settings/add.html)
- [`mise settings get \[-l --local\] <SETTING>`](https://mise.jdx.dev/cli/settings/get.html)
- [`mise settings ls \[FLAGS\] \[SETTING\]`](https://mise.jdx.dev/cli/settings/ls.html)
- [`mise settings set \[-l --local\] <SETTING> <VALUE>`](https://mise.jdx.dev/cli/settings/set.html)
- [`mise settings unset \[-l --local\] <KEY>`](https://mise.jdx.dev/cli/settings/unset.html)

Examples:

```
# list all settings
$ mise settings

# get the value of the setting "always_keep_download"
$ mise settings always_keep_download

# set the value of the setting "always_keep_download" to "true"
$ mise settings always_keep_download=true

# set the value of the setting "node.mirror_url" to "https://npm.taobao.org/mirrors/node"
$ mise settings node.mirror_url https://npm.taobao.org/mirrors/node
```
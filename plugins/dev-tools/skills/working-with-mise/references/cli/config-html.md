---
title: "mise config | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise config` [​](#mise-config)

- **Usage**: `mise config [FLAGS] <SUBCOMMAND>`
- **Aliases**: `cfg`
- **Source code**: [`src/cli/config/mod.rs`](https://github.com/jdx/mise/blob/main/src/cli/config/mod.rs)

Manage config files

## Flags [​](#flags)

### `-J --json` [​](#j-json)

Output in JSON format

### `--no-header` [​](#no-header)

Do not print table header

### `--tracked-configs` [​](#tracked-configs)

List all tracked config files

## Subcommands [​](#subcommands)

- [`mise config generate \[-o --output <OUTPUT>\] \[-t --tool-versions <TOOL_VERSIONS>\]`](https://mise.jdx.dev/cli/config/generate.html)
- [`mise config get \[-f --file <FILE>\] \[KEY\]`](https://mise.jdx.dev/cli/config/get.html)
- [`mise config ls \[FLAGS\]`](https://mise.jdx.dev/cli/config/ls.html)
- [`mise config set \[-f --file <FILE>\] \[-t --type <TYPE>\] <KEY> <VALUE>`](https://mise.jdx.dev/cli/config/set.html)

Examples:

```
$ mise config ls
Path                        Tools
~/.config/mise/config.toml  pitchfork
~/src/mise/mise.toml        actionlint, bun, cargo-binstall, cargo:cargo-edit, cargo:cargo-insta
```
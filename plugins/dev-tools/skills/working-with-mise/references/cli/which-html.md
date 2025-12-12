---
title: "mise which | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise which` [​](#mise-which)

- **Usage**: `mise which [FLAGS] [BIN_NAME]`
- **Source code**: [`src/cli/which.rs`](https://github.com/jdx/mise/blob/main/src/cli/which.rs)

Shows the path that a tool's bin points to.

Use this to figure out what version of a tool is currently active.

## Arguments [​](#arguments)

### `[BIN_NAME]` [​](#bin-name)

The bin to look up

## Flags [​](#flags)

### `-t --tool <TOOL@VERSION>` [​](#t-tool-tool-version)

Use a specific tool@version e.g.: `mise which npm --tool=node@20`

### `--plugin` [​](#plugin)

Show the plugin name instead of the path

### `--version` [​](#version)

Show the version instead of the path

Examples:

```
$ mise which node
/home/username/.local/share/mise/installs/node/20.0.0/bin/node

$ mise which node --plugin
node

$ mise which node --version
20.0.0
```
---
title: "mise tool | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise tool` [​](#mise-tool)

- **Usage**: `mise tool [FLAGS] <TOOL>`
- **Source code**: [`src/cli/tool.rs`](https://github.com/jdx/mise/blob/main/src/cli/tool.rs)

Gets information about a tool

## Arguments [​](#arguments)

### `<TOOL>` [​](#tool)

Tool name to get information about

## Flags [​](#flags)

### `-J --json` [​](#j-json)

Output in JSON format

### `--active` [​](#active)

Only show active versions

### `--backend` [​](#backend)

Only show backend field

### `--config-source` [​](#config-source)

Only show config source

### `--description` [​](#description)

Only show description field

### `--installed` [​](#installed)

Only show installed versions

### `--requested` [​](#requested)

Only show requested versions

### `--tool-options` [​](#tool-options)

Only show tool options

Examples:

```
$ mise tool node
Backend:            core
Installed Versions: 20.0.0 22.0.0
Active Version:     20.0.0
Requested Version:  20
Config Source:      ~/.config/mise/mise.toml
Tool Options:       [none]
```
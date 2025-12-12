---
title: "mise link | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise link` [​](#mise-link)

- **Usage**: `mise link [-f --force] <TOOL@VERSION> <PATH>`
- **Aliases**: `ln`
- **Source code**: [`src/cli/link.rs`](https://github.com/jdx/mise/blob/main/src/cli/link.rs)

Symlinks a tool version into mise

Use this for adding installs either custom compiled outside mise or built with a different tool.

## Arguments [​](#arguments)

### `<TOOL@VERSION>` [​](#tool-version)

Tool name and version to create a symlink for

### `<PATH>` [​](#path)

The local path to the tool version e.g.: ~/.nvm/versions/node/v20.0.0

## Flags [​](#flags)

### `-f --force` [​](#f-force)

Overwrite an existing tool version if it exists

Examples:

```
# build node-20.0.0 with node-build and link it into mise
$ node-build 20.0.0 ~/.nodes/20.0.0
$ mise link node@20.0.0 ~/.nodes/20.0.0

# have mise use the node version provided by Homebrew
$ brew install node
$ mise link node@brew $(brew --prefix node)
$ mise use node@brew
```
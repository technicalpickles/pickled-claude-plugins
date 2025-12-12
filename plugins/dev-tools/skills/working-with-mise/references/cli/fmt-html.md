---
title: "mise fmt | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise fmt` [​](#mise-fmt)

- **Usage**: `mise fmt [FLAGS]`
- **Source code**: [`src/cli/fmt.rs`](https://github.com/jdx/mise/blob/main/src/cli/fmt.rs)

Formats mise.toml

Sorts keys and cleans up whitespace in mise.toml

## Flags [​](#flags)

### `-a --all` [​](#a-all)

Format all files from the current directory

### `-c --check` [​](#c-check)

Check if the configs are formatted, no formatting is done

### `-s --stdin` [​](#s-stdin)

Read config from stdin and write its formatted version into stdout

Examples:

```
mise fmt
```
---
title: "mise implode | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise implode` [​](#mise-implode)

- **Usage**: `mise implode [-n --dry-run] [--config]`
- **Source code**: [`src/cli/implode.rs`](https://github.com/jdx/mise/blob/main/src/cli/implode.rs)

Removes mise CLI and all related data

Skips config directory by default.

## Flags [​](#flags)

### `-n --dry-run` [​](#n-dry-run)

List directories that would be removed without actually removing them

### `--config` [​](#config)

Also remove config directory
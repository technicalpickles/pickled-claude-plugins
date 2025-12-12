---
title: "mise version | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise version` [​](#mise-version)

- **Usage**: `mise version [-J --json]`
- **Aliases**: `v`
- **Source code**: [`src/cli/version.rs`](https://github.com/jdx/mise/blob/main/src/cli/version.rs)

Display the version of mise

Displays the version, os, architecture, and the date of the build.

If the version is out of date, it will display a warning.

## Flags [​](#flags)

### `-J --json` [​](#j-json)

Print the version information in JSON format

Examples:

```
mise version
mise --version
mise -v
mise -V
```
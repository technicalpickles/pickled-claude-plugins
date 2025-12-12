---
title: "mise env | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise env` [​](#mise-env)

- **Usage**: `mise env [FLAGS] [TOOL@VERSION]…`
- **Aliases**: `e`
- **Source code**: [`src/cli/env.rs`](https://github.com/jdx/mise/blob/main/src/cli/env.rs)

Exports env vars to activate mise a single time

Use this if you don't want to permanently install mise. It's not necessary to use this if you have `mise activate` in your shell rc file.

## Arguments [​](#arguments)

### `[TOOL@VERSION]…` [​](#tool-version)

Tool(s) to use

## Flags [​](#flags)

### `-D --dotenv` [​](#d-dotenv)

Output in dotenv format

### `-J --json` [​](#j-json)

Output in JSON format

### `-s --shell <SHELL>` [​](#s-shell-shell)

Shell type to generate environment variables for

**Choices:**

- `bash`
- `elvish`
- `fish`
- `nu`
- `xonsh`
- `zsh`
- `pwsh`

### `--json-extended` [​](#json-extended)

Output in JSON format with additional information (source, tool)

### `--redacted` [​](#redacted)

Only show redacted environment variables

### `--values` [​](#values)

Only show values of environment variables

Examples:

```
eval "$(mise env -s bash)"
eval "$(mise env -s zsh)"
mise env -s fish | source
execx($(mise env -s xonsh))
```
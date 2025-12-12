---
title: "mise en | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise en` [​](#mise-en)

- **Usage**: `mise en [-s --shell <SHELL>] [DIR]`
- **Source code**: [`src/cli/en.rs`](https://github.com/jdx/mise/blob/main/src/cli/en.rs)

Starts a new shell with the mise environment built from the current configuration

This is an alternative to `mise activate` that allows you to explicitly start a mise session. It will have the tools and environment variables in the configs loaded. Note that changing directories will not update the mise environment.

## Arguments [​](#arguments)

### `[DIR]` [​](#dir)

Directory to start the shell in

**Default:** `.`

## Flags [​](#flags)

### `-s --shell <SHELL>` [​](#s-shell-shell)

Shell to start

Defaults to $SHELL

Examples:

```
$ mise en .
$ node -v
v20.0.0

Skip loading bashrc:
$ mise en -s "bash --norc"

Skip loading zshrc:
$ mise en -s "zsh -f"
```
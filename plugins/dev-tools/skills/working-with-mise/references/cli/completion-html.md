---
title: "mise completion | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise completion` [​](#mise-completion)

- **Usage**: `mise completion [--include-bash-completion-lib] [SHELL]`
- **Source code**: [`src/cli/completion.rs`](https://github.com/jdx/mise/blob/main/src/cli/completion.rs)

Generate shell completions

## Arguments [​](#arguments)

### `[SHELL]` [​](#shell)

Shell type to generate completions for

**Choices:**

- `bash`
- `fish`
- `zsh`

## Flags [​](#flags)

### `--include-bash-completion-lib` [​](#include-bash-completion-lib)

Include the bash completion library in the bash completion script

This is required for completions to work in bash, but it is not included by default you may source it separately or enable this flag to enable it in the script.

Examples:

```
mise completion bash --include-bash-completion-lib > ~/.local/share/bash-completion/completions/mise
mise completion zsh  > /usr/local/share/zsh/site-functions/_mise
mise completion fish > ~/.config/fish/completions/mise.fish
```
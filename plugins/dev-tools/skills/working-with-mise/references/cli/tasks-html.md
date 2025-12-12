---
title: "mise tasks | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise tasks` [​](#mise-tasks)

- **Usage**: `mise tasks [FLAGS] [TASK] <SUBCOMMAND>`
- **Aliases**: `t`
- **Source code**: [`src/cli/tasks/mod.rs`](https://github.com/jdx/mise/blob/main/src/cli/tasks/mod.rs)

Manage tasks

## Arguments [​](#arguments)

### `[TASK]` [​](#task)

Task name to get info of

## Global Flags [​](#global-flags)

### `-g --global` [​](#g-global)

Only show global tasks

### `-J --json` [​](#j-json)

Output in JSON format

### `-l --local` [​](#l-local)

Only show non-global tasks

### `-x --extended` [​](#x-extended)

Show all columns

### `--all` [​](#all)

Load all tasks from the entire monorepo, including sibling directories. By default, only tasks from the current directory hierarchy are loaded.

### `--hidden` [​](#hidden)

Show hidden tasks

### `--no-header` [​](#no-header)

Do not print table header

### `--sort <COLUMN>` [​](#sort-column)

Sort by column. Default is name.

**Choices:**

- `name`
- `alias`
- `description`
- `source`

### `--sort-order <SORT_ORDER>` [​](#sort-order-sort-order)

Sort order. Default is asc.

**Choices:**

- `asc`
- `desc`

## Subcommands [​](#subcommands)

- [`mise tasks add \[FLAGS\] <TASK> \[-- RUN\]…`](https://mise.jdx.dev/cli/tasks/add.html)
- [`mise tasks deps \[--dot\] \[--hidden\] \[TASKS\]…`](https://mise.jdx.dev/cli/tasks/deps.html)
- [`mise tasks edit \[-p --path\] <TASK>`](https://mise.jdx.dev/cli/tasks/edit.html)
- [`mise tasks info \[-J --json\] <TASK>`](https://mise.jdx.dev/cli/tasks/info.html)
- [`mise tasks ls \[FLAGS\]`](https://mise.jdx.dev/cli/tasks/ls.html)
- [`mise tasks run \[FLAGS\] \[TASK\] \[ARGS\]…`](https://mise.jdx.dev/cli/tasks/run.html)
- [`mise tasks validate \[--errors-only\] \[--json\] \[TASKS\]…`](https://mise.jdx.dev/cli/tasks/validate.html)

Examples:

```
mise tasks ls
```
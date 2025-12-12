---
title: "mise ls | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise ls` [​](#mise-ls)

- **Usage**: `mise ls [FLAGS] [INSTALLED_TOOL]…`
- **Aliases**: `list`
- **Source code**: [`src/cli/ls.rs`](https://github.com/jdx/mise/blob/main/src/cli/ls.rs)

List installed and active tool versions

This command lists tools that mise "knows about". These may be tools that are currently installed, or those that are in a config file (active) but may or may not be installed.

It's a useful command to get the current state of your tools.

## Arguments [​](#arguments)

### `[INSTALLED_TOOL]…` [​](#installed-tool)

Only show tool versions from [TOOL]

## Flags [​](#flags)

### `-c --current` [​](#c-current)

Only show tool versions currently specified in a mise.toml

### `-g --global` [​](#g-global)

Only show tool versions currently specified in the global mise.toml

### `-i --installed` [​](#i-installed)

Only show tool versions that are installed (Hides tools defined in mise.toml but not installed)

### `-J --json` [​](#j-json)

Output in JSON format

### `-l --local` [​](#l-local)

Only show tool versions currently specified in the local mise.toml

### `-m --missing` [​](#m-missing)

Display missing tool versions

### `--no-header` [​](#no-header)

Don't display headers

### `--outdated` [​](#outdated)

Display whether a version is outdated

### `--prefix <PREFIX>` [​](#prefix-prefix)

Display versions matching this prefix

### `--prunable` [​](#prunable)

List only tools that can be pruned with `mise prune`

Examples:

```
$ mise ls
node    20.0.0 ~/src/myapp/.tool-versions latest
python  3.11.0 ~/.tool-versions           3.10
python  3.10.0

$ mise ls --current
node    20.0.0 ~/src/myapp/.tool-versions 20
python  3.11.0 ~/.tool-versions           3.11.0

$ mise ls --json
{
  "node": [
    {
      "version": "20.0.0",
      "install_path": "/Users/jdx/.mise/installs/node/20.0.0",
      "source": {
        "type": "mise.toml",
        "path": "/Users/jdx/mise.toml"
      }
    }
  ],
  "python": [...]
}
```
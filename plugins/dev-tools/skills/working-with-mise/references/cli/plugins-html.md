---
title: "mise plugins | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise plugins` [​](#mise-plugins)

- **Usage**: `mise plugins [FLAGS] <SUBCOMMAND>`
- **Aliases**: `p`
- **Source code**: [`src/cli/plugins/mod.rs`](https://github.com/jdx/mise/blob/main/src/cli/plugins/mod.rs)

Manage plugins

## Flags [​](#flags)

### `-c --core` [​](#c-core)

The built-in plugins only Normally these are not shown

### `-u --urls` [​](#u-urls)

Show the git url for each plugin e.g.: [https://github.com/asdf-vm/asdf-nodejs.git](https://github.com/asdf-vm/asdf-nodejs.git)

### `--user` [​](#user)

List installed plugins

This is the default behavior but can be used with --core to show core and user plugins

## Subcommands [​](#subcommands)

- [`mise plugins install \[FLAGS\] \[NEW_PLUGIN\] \[GIT_URL\]`](https://mise.jdx.dev/cli/plugins/install.html)
- [`mise plugins link \[-f --force\] <NAME> \[DIR\]`](https://mise.jdx.dev/cli/plugins/link.html)
- [`mise plugins ls \[-u --urls\]`](https://mise.jdx.dev/cli/plugins/ls.html)
- [`mise plugins ls-remote \[-u --urls\] \[--only-names\]`](https://mise.jdx.dev/cli/plugins/ls-remote.html)
- [`mise plugins uninstall \[-a --all\] \[-p --purge\] \[PLUGIN\]…`](https://mise.jdx.dev/cli/plugins/uninstall.html)
- [`mise plugins update \[-j --jobs <JOBS>\] \[PLUGIN\]…`](https://mise.jdx.dev/cli/plugins/update.html)
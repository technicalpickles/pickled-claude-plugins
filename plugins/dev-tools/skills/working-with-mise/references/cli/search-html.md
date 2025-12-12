---
title: "mise search | mise-en-place"
meta:
  description: "mise-en-place documentation"
---

# `mise search` [​](#mise-search)

- **Usage**: `mise search [FLAGS] [NAME]`
- **Source code**: [`src/cli/search.rs`](https://github.com/jdx/mise/blob/main/src/cli/search.rs)

Search for tools in the registry

This command searches a tool in the registry.

By default, it will show all tools that fuzzy match the search term. For non-fuzzy matches, use the `--match-type` flag.

## Arguments [​](#arguments)

### `[NAME]` [​](#name)

The tool to search for

## Flags [​](#flags)

### `-i --interactive` [​](#i-interactive)

Show interactive search

### `-m --match-type <MATCH_TYPE>` [​](#m-match-type-match-type)

Match type: equal, contains, or fuzzy

**Choices:**

- `equal`
- `contains`
- `fuzzy`

**Default:** `fuzzy`

### `--no-header` [​](#no-header)

Don't display headers

Examples:

```
$ mise search jq
Tool  Description
jq    Command-line JSON processor. https://github.com/jqlang/jq
jqp   A TUI playground to experiment with jq. https://github.com/noahgorstein/jqp
jiq   jid on jq - interactive JSON query tool using jq expressions. https://github.com/fiatjaf/jiq
gojq  Pure Go implementation of jq. https://github.com/itchyny/gojq

$ mise search --interactive
Tool
Search a tool
❯ jq    Command-line JSON processor. https://github.com/jqlang/jq
  jqp   A TUI playground to experiment with jq. https://github.com/noahgorstein/jqp
  jiq   jid on jq - interactive JSON query tool using jq expressions. https://github.com/fiatjaf/jiq
  gojq  Pure Go implementation of jq. https://github.com/itchyny/gojq
/jq 
esc clear filter • enter confirm
```
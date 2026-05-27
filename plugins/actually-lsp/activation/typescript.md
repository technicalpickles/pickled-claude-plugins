## LSP context

An LSP server is loaded for this codebase: **typescript-language-server** via the `typescript-lsp` plugin. It can answer:

- `textDocument/definition`: where is this symbol defined?
- `textDocument/references`: where is this symbol used, which classes implement this interface?
- `textDocument/documentSymbol`: what symbols are defined in this file?
- `workspace/symbol`: find a symbol by name anywhere in the workspace.
- `textDocument/hover`: what is the type or signature of this symbol?

The `LSP` tool in this Claude Code session is a **deferred tool**: its schema is not loaded by default. To use it:

1. Call `ToolSearch` with `query: "select:LSP"` to load the LSP tool's schema.
2. Then call `LSP` with the appropriate `operation` (one of those above).

For navigation, definition lookup, and references, prefer LSP over `grep` + `Read`. LSP gives semantic answers that `grep` can't (a `references` query won't miss an inheritance chain the way a `grep` for `implements TokenFormatter` would).

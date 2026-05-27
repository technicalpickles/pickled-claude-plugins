## LSP context

An LSP server is loaded for this codebase: **ruby-lsp** via the `ruby-lsp` plugin. It can answer:

- `textDocument/definition`: where is this symbol defined?
- `textDocument/references`: where is this symbol used, which classes inherit or include this module?
- `textDocument/documentSymbol`: what symbols are defined in this file?
- `workspace/symbol`: find a symbol by name anywhere in the workspace.
- `textDocument/hover`: what is the type or signature of this symbol?

The `LSP` tool in this Claude Code session is a **deferred tool**: its schema is not loaded by default. To use it:

1. Call `ToolSearch` with `query: "select:LSP"` to load the LSP tool's schema.
2. Then call `LSP` with the appropriate `operation` (one of those above).

For navigation and definition lookup, prefer LSP over `grep` + `Read`. LSP walks the gem graph for installed dependencies, so it can resolve into gems your code uses.

**Ruby diagnostics note:** ruby-lsp is pull-only, and Claude Code's LSP client doesn't pull diagnostics. Use LSP for navigation; for rubocop offenses, run `rubocop` directly via Bash.

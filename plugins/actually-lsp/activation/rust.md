## LSP context

An LSP server is loaded for this codebase: **rust-analyzer** via the `rust-analyzer-lsp` plugin. It can answer:

- `textDocument/definition`: where is this symbol defined?
- `textDocument/references`: where is this symbol used, which types implement this trait?
- `textDocument/documentSymbol`: what symbols are defined in this file?
- `workspace/symbol`: find a symbol by name anywhere in the workspace.
- `textDocument/hover`: what is the type or signature of this symbol?

The `LSP` tool in this Claude Code session is a **deferred tool**: its schema is not loaded by default. To use it:

1. Call `ToolSearch` with `query: "select:LSP"` to load the LSP tool's schema.
2. Then call `LSP` with the appropriate `operation` (one of those above).

For navigation, definition lookup, and references, prefer LSP over `grep` + `Read`. LSP gives semantic answers `grep` can't (a `references` query won't miss an `impl` block the way a regex would).

**Rust warm-up note:** if `cargo build` hasn't run recently, run it before LSP queries. rust-analyzer's `workspace/symbol` races indexing on cold cache; file-scoped queries (`documentSymbol`, `goToDefinition`) work fine cold but workspace-scoped queries return empty until indexing settles.

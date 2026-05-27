# Ecosystem-aware, not LSP-plugin-aware

The plugin reasons about **ecosystems** (Rust via Cargo, TypeScript via npm, Ruby via Bundler) and detects them via ecosystem markers (`Cargo.toml`, `package.json`, `Gemfile`). The mapping from ecosystem to recommended LSP plugin is owned by `actually-lsp` and treated as data, not as the unit of state. This leaves room for users to choose alternate language servers (e.g. `solargraph` instead of `ruby-lsp`, `vtsls` instead of `typescript-language-server`) without rewriting detection.

## Considered options

- **LSP-plugin-aware**: detect "user has `rust-analyzer-lsp` enabled" and key everything on that. Tightly coupled to specific upstream plugins; breaks if the user installs a different LSP plugin for the same ecosystem; can't recognize "Rust project with no LSP plugin" as a coherent state.

## Consequences

- The project state file keys on ecosystem (`rust`, `typescript`, `ruby`), not on plugin name.
- v1 hardcodes a single recommended plugin per ecosystem. The shape supports adding alternates later without schema change.
- Detection can answer "this is a Rust project; does the user have *any* compatible LSP plugin enabled?" cleanly. Plugin-aware design can only answer "is `rust-analyzer-lsp` enabled?", which misses the question.
- If a user installs an LSP plugin for an ecosystem we don't know about (e.g. a hypothetical `python-lsp`), the plugin reads `claude plugin list --json` and ignores it. Extension is adding an ecosystem + marker + recommended plugin to the plugin's own tables, not changing the detection model.

# Layer on top of official LSP plugins

`actually-lsp` does not ship its own `lspServers` config and does not replace the LSP plugins from `claude-plugins-official` (`rust-analyzer-lsp`, `typescript-lsp`, `ruby-lsp`). It points at them by name and assumes the user installs them alongside this plugin. Upstream is the source of truth for server config; this plugin owns detection, nudging, activation context, and failure context.

## Considered options

- **Replace**: ship `lspServers` config for Rust / TypeScript / Ruby in our own marketplace entry. One install, but the plugin owns server-config drift and conflicts with the upstream plugins if both are enabled.
- **Per-language drop-in replacements**: three plugins (`actually-rust-lsp`, etc.) each shipping server config + skill + nudge. 3x install steps, 3x marketplace surface, shared scaffolding has to duplicate.

## Consequences

- Two installs required (the official LSP plugin + `actually-lsp`). Documented as the standard setup path.
- Upstream `lspServers` changes flow through unchanged. No drift to manage.
- The plugin has no place to inject Rust-specific `initializationOptions` (e.g. `cachePriming.numThreads: 'physical'`). Users who need that still need the local-marketplace pattern from the LSP how-to. Acknowledged limitation; revisit if per-language sibling plugins become viable.

---
name: skip
description: Dismiss actually-lsp nudges for an ecosystem in this project. Use when the user wants to silence, dismiss, or skip the LSP setup nudges for a specific ecosystem (Rust, TypeScript, Ruby), or invokes `/actually-lsp:skip` directly. Writes `dismissed=true` to `.claude/actually-lsp.json`. Persistent across sessions for this project only.
---

# /actually-lsp:skip

Parse args:

- `rust` | `typescript` | `ruby` as an arg dismisses that ecosystem directly.
- No args: read `.claude/actually-lsp.json` in the current project root, present the detected ecosystems, and ask the user which to dismiss.

## Action

Update the project state file at `.claude/actually-lsp.json`: set `.ecosystems.<ecosystem>.dismissed` to `true`. If the file doesn't exist, create it with version 1 schema:

```json
{
  "version": 1,
  "ecosystems": {
    "<ecosystem>": {
      "state": "dismissed",
      "dismissed": true,
      "last_check_at": null,
      "last_marker_mtime": null,
      "last_plugin_list_hash": null,
      "last_error": null
    }
  }
}
```

If the file exists, preserve all other fields and only flip `dismissed`.

## Confirmation output

Output a one-line confirmation per dismissed ecosystem:

```
Dismissed <ecosystem> for this project. To re-enable, manually edit .claude/actually-lsp.json and set dismissed back to false. (An `unskip` command is a future extension.)
```
